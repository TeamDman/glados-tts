import sys
import os
sys.path.insert(0, os.getcwd()+'/glados_tts')
import re

import torch
from utils.tools import prepare_text
from scipy.io.wavfile import write
import time

from glados import tts_runner
		
print("\033[1;94mINFO:\033[;97m Initializing TTS Engine...")

glados = tts_runner(False, True)

def glados_tts(text, key=False, alpha=1.0):

	if(key):
		output_file = ('audio/GLaDOS-tts-temp-output-'+key+'.wav')
	else:
		output_file = ('audio/GLaDOS-tts-temp-output.wav')

	glados.run_tts(text, alpha).export(output_file, format = "wav")
	return True

def sanitize_filename(text):
    sanitized = re.sub(r'[^a-zA-Z0-9\-_\.]', '', text)  # Keep only alphanumeric, dashes, underscores, and dots
    return sanitized

# If the script is run directly, assume remote engine
if __name__ == "__main__":
	
	# Remote Engine Veritables
	PORT = 8124
	CACHE = True

	from flask import Flask, request, send_file
	import urllib.parse
	import shutil
	
	print("\033[1;94mINFO:\033[;97m Initializing TTS Server...")
	
	app = Flask(__name__)

	@app.route("/")
	def index():
		return "GLaDOS TTS Engine"

	@app.route('/synthesize', methods=['POST'])
	def synthesize():
		text = request.data.decode('utf-8')  # Decode the request body directly as text
		if not text:
			return 'No input', 400  # Return a 400 Bad Request error if no text is provided

		filename_sanitized = "GLaDOS-tts-" + sanitize_filename(text.replace(" ", "-")) + ".wav"
		file = os.getcwd() + '/audio/' + filename_sanitized
		
		# Check for Local Cache
		if(os.path.isfile(file)):
		
			# Update access time. This will allow for routine cleanups
			os.utime(file, None)
			print("\033[1;94mINFO:\033[;97m The audio sample sent from cache.")
			return send_file(file)
			
		# Generate New Sample
		key = str(time.time())[7:]
		if(glados_tts(text, key)):
			tempfile = os.getcwd()+'/audio/GLaDOS-tts-temp-output-'+key+'.wav'
						
			# If the line isn't too long, store in cache
			if(len(text) < 200 and CACHE):
				shutil.move(tempfile, file)
			else:
				return send_file(tempfile)
				os.remove(tempfile)
				
			return send_file(file)
				
		else:
			return 'TTS Engine Failed'
			
	cli = sys.modules['flask.cli']
	cli.show_server_banner = lambda *x: None
	app.run(host="0.0.0.0", port=PORT)
