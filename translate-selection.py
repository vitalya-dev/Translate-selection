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
	"LOG_FILE": "/tmp/translation_stream.log"
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

def show_yakuake():
	"""
	Отправляет команду через D-Bus для вызова окна Yakuake.
	"""
	print("Вызов Yakuake...")
	# Вызываем Yakuake с помощью qdbus. Игнорируем ошибки (check=False), 
	# чтобы скрипт не упал, если Yakuake вдруг закрыт.
	run_command(
		["qdbus6", "org.kde.yakuake", "/yakuake/window", "org.kde.yakuake.toggleWindowState"],
		check=False
	)

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
		# Возвращаем сырой текст со всеми \n, чтобы preprocess_text мог с ним поработать
		return content
	
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
	text = re.sub(r'(\.)\s*\d{1,3}\s*', r'\1 ', text)
	
	# 4. Убираем лишние пробелы в начале и в конце текста.
	return text.strip()

def split_into_sentences(text):
	"""
	Разбивает сплошной текст на отдельные предложения.
	"""
	if not text:
		return []
		
	# Разбиваем текст по пробелам, которым предшествует точка, восклицательный или вопросительный знак.
	# Используем позитивный просмотр назад (?<=[.!?]), чтобы знаки препинания оставались в конце предложений.
	sentences = re.split(r'(?<=[.!?])\s+', text.strip())
	
	# Возвращаем список, отфильтровав пустые строки (на всякий случай)
	return [s for s in sentences if s]


def main():
	"""Main function to execute the translation pipeline."""
	
	try:
		# 1. Получаем сырой текст из буфера обмена
		raw_text = get_clipboard_text()
		if not raw_text:
			print("No content found in clipboard to translate.")
			subprocess.run(["notify-send", "Translation", "No text selected or copied."])
			return

		# 2. Очищаем текст от переносов и сносок
		processed_text = preprocess_text(raw_text)

		# 3. Разбиваем текст на отдельные предложения
		sentences = split_into_sentences(processed_text)
		if not sentences:
			return

		# 4. Вызываем Yakuake, чтобы показать терминал
		show_yakuake()

		# 5. Открываем лог-файл в режиме добавления ("a") и переводим по частям
		print(f"Starting stream translation to {CONFIG['LOG_FILE']}...")
		
		with open(CONFIG["LOG_FILE"], "a", encoding="utf-8") as log_file:
			# Добавляем разделитель для удобства чтения в tail -f
			log_file.write("\n\n--- Новый перевод ---\n")
			log_file.flush()
			
			for sentence in sentences:
				translated_sentence = translate_with_libre(sentence)
				
				# Записываем переведенное предложение с пробелом
				log_file.write(translated_sentence + " ")
				# Принудительно сбрасываем буфер, чтобы tail -f сразу показал текст
				log_file.flush()
				
				print(f"Translated chunk: {translated_sentence}")
				
		subprocess.run(["notify-send", "Translation", "Finished streaming to log."])

	except ScriptError as e:
		# Этот блок сработает, если сервер недоступен или возникла другая ошибка
		error_message = str(e)
		print(f"Operation failed: {error_message}")
		subprocess.run(["notify-send", "-u", "critical", "Translation Failed", error_message])
		return

if __name__ == "__main__":
	main()