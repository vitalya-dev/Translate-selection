import subprocess
import os
import shutil
import urllib.request
import json
import re

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
CONFIG = {
	"NOTIFICATION_TITLE": "Translated",
	"LIBRETRANSLATE_URL": "http://localhost:5000/translate",
	"SOURCE_LANG": "en", 
	"TARGET_LANG": "ru",
	"QML_APP_PATH": "/home/vitalya/Projects/Translate-selection/solarfloat.qml"
}
# ==============================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))

class ScriptError(Exception):
	"""Custom exception for script-specific errors."""
	pass

def run_command(command, input_data=None, capture_output=True, text=True, check=True):
	"""
	Helper function to run a shell command and wait for it to complete.
	"""
	try:
		process = subprocess.run(
			command,
			input=input_data,
			capture_output=capture_output,
			text=text,
			check=check
		)
		return process
	except Exception as e:
		raise ScriptError(f"Command `{' '.join(command)}` failed: {str(e)}")

def get_clipboard_text():
	"""
	Retrieves text from the Wayland clipboard.
	"""
	print("Getting clipboard content (trying primary selection)...")
	paste_process = run_command(["wl-paste", "-p"], check=False)
	content = paste_process.stdout.strip() if paste_process.stdout else ""

	if not content:
		print("Primary selection empty, trying regular clipboard...")
		paste_process = run_command(["wl-paste"], check=False)
		content = paste_process.stdout.strip() if paste_process.stdout else ""
	
	if content:
		return " ".join(content.splitlines())
	
	return None

def translate_with_libre(text_to_translate):
	"""
	Переводит текст с помощью локального API LibreTranslate.
	"""
	print("\n--- Attempting translation with LibreTranslate... ---")
	
	data = {
		"q": text_to_translate,
		"source": CONFIG["SOURCE_LANG"],
		"target": CONFIG["TARGET_LANG"],
		"format": "text"
	}
	
	data_encoded = json.dumps(data).encode('utf-8')
	
	req = urllib.request.Request(
		CONFIG["LIBRETRANSLATE_URL"], 
		data=data_encoded, 
		headers={'Content-Type': 'application/json'}
	)
	
	try:
		with urllib.request.urlopen(req) as response:
			result = json.loads(response.read().decode('utf-8'))
			translated_text = result.get("translatedText", "")
			
			if not translated_text:
				raise ScriptError("LibreTranslate вернул пустой результат.")
				
			print("Translation successful.")
			return translated_text
            
	except Exception as e:
		raise ScriptError(f"Ошибка при запросе к LibreTranslate: {str(e)}")

def preprocess_text(text):
	"""
	Очищает текст от переносов слов, сносок (после точек) и форматирует пробелы.
	"""
	if not text:
		return text
		
	# 1. Убираем переносы слов: дефис, за которым следует перенос строки.
	text = re.sub(r'-\s*\n\s*', '', text)
	
	# 2. Заменяем все оставшиеся переносы строк и множественные пробелы на один пробел.
	text = re.sub(r'\s+', ' ', text)
	
	# 3. Убираем сноски: числа от 1 до 3 цифр, идущие после точки.
	# (\.) захватывает точку, \s+ это пробелы, \d{1,3} это цифры. 
	# Заменяем на \1 (сохраненную точку) и один пробел.
	text = re.sub(r'(\.)\s+\d{1,3}\s+', r'\1 ', text)
	
	# 4. Убираем лишние пробелы в начале и в конце текста.
	return text.strip()


def main():
	"""Main function to execute the translation pipeline."""
	
	try:
		# 1. Получаем текст из буфера обмена
		processed_text = get_clipboard_text()
		if not processed_text:
			print("No content found in clipboard to translate.")
			subprocess.run(["notify-send", "Translation", "No text selected or copied."])
			return

		# 2. Выполняем перевод через локальный LibreTranslate
		translated_text = translate_with_libre(processed_text)

		# 3. Открываем QML-приложение с результатом
		print("Sending to QML app...")
		run_command(["env", "QT_QPA_PLATFORM=xcb", "qml", CONFIG["QML_APP_PATH"], "--", translated_text], check=False)


	except ScriptError as e:
		# Этот блок сработает, если сервер недоступен или возникла другая ошибка
		error_message = str(e)
		print(f"Operation failed: {error_message}")
		subprocess.run(["notify-send", "-u", "critical", "Translation Failed", error_message])
		return

if __name__ == "__main__":
	main()