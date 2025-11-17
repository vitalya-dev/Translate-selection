import subprocess
import os # Keep os for os.path.dirname/abspath
import shutil

# ==============================================================================
# --- CONFIGURATION ---
# ==============================================================================
CONFIG = {
	"NOTIFICATION_TITLE": "Translated",
}
# ==============================================================================


# --- Path Construction and Validation ---
# (This section is now removed, as we don't need venv or the other script)
script_dir = os.path.dirname(os.path.abspath(__file__))


# --- Custom Exception ---
class ScriptError(Exception):
	"""Custom exception for script-specific errors."""
	pass


# --- Helper Functions ---

def is_command_available(command):
	"""
	Checks if a command-line tool is available in the system's PATH.
	Args:
		command (str): The name of the command to check (e.g., "trans").
	Returns:
		bool: True if the command is found, False otherwise.
	"""
	return shutil.which(command) is not None

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

# (run_command_popen function removed)

def get_clipboard_text():
	"""
	Retrieves text from the Wayland clipboard.
	"""
	print("Getting clipboard content (trying primary selection)...")
	paste_process = run_command(["wl-paste", "-p"])
	content = paste_process.stdout.strip()

	if not content:
		print("Primary selection empty, trying regular clipboard...")
		paste_process = run_command(["wl-paste"])
		content = paste_process.stdout.strip()
	
	if content:
		return " ".join(content.splitlines())
	
	return None

# (stream_translation function removed)

# (stream_and_notify function removed)

def translate_with_trans_shell(text_to_translate):
	"""
	Translates the given text using the 'trans-shell' command-line tool.

	Args:
		text_to_translate (str): The text to be translated.

	Returns:
		str: The translated text.

	Raises:
		ScriptError: If the 'trans' command fails or returns an empty result.
	"""
	print("\n--- Attempting translation with 'trans-shell'... ---")
	
	# The command to run. '-b' stands for "brief" mode, which gives only the translation.
	command = ["trans", "-b", text_to_translate]
	
	# Use the existing run_command helper to execute the translation
	process = run_command(command)
	
	translated_text = process.stdout.strip()
	
	if not translated_text:
		raise ScriptError("'trans-shell' returned an empty result.")
		
	print(f"Translation successful.") # Updated print statement
	return translated_text

# --- Main Logic ---
def main():
	"""Main function to execute the translation pipeline."""
	
	try:
		# 1. Check if 'trans' command is available
		if not is_command_available("trans"):
			raise ScriptError("Fallback tool 'trans' not found. Please install 'trans-shell'.")

		# 2. Get content from clipboard
		processed_text = get_clipboard_text()
		if not processed_text:
			print("No content found in clipboard to translate.")
			subprocess.run(["notify-send", "Translation", "No text selected or copied."])
			return

		# 3. Perform the translation
		translated_text = translate_with_trans_shell(processed_text)

		# 4. Send a single notification for the result
		print("Sending notification...")
		title = CONFIG["NOTIFICATION_TITLE"]
		run_command(["notify-send", title, translated_text], check=False)

		# 5. Copy the result to the clipboard
		if translated_text:
			print("Copying final translated text to clipboard...")
			run_command(["wl-copy"], input_data=translated_text, capture_output=False)
			print("Done.")

	except ScriptError as e:
		# This block runs if any step in the 'try' block fails.
		error_message = str(e)
		print(f"Operation failed: {error_message}")
		subprocess.run(["notify-send", "-u", "critical", "Translation Failed", error_message])
		return


if __name__ == "__main__":
	main()


