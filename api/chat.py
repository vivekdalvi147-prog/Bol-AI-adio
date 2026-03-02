import os
import json
import base64
import io
import wave
from http.server import BaseHTTPRequestHandler
from google import genai
from google.genai import types

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            # 1. Data Read karna
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            audio_b64 = data.get('audio')

            if not audio_b64:
                self.wfile.write(json.dumps({"error": "No audio data received"}).encode())
                return

            # 2. API Key Check
            api_key = os.environ.get("Google_api_vivek")
            if not api_key:
                self.wfile.write(json.dumps({"error": "API Key Google_api_vivek not set"}).encode())
                return

            # 3. Client Setup
            client = genai.Client(api_key=api_key)
            
            # Browser se aayi audio (WebM) ko decode karna
            input_audio_bytes = base64.b64decode(audio_b64)

            # 4. GEMINI API CALL (Exact Model ID from Screenshot)
            # Hum 'AUDIO' modality maang rahe hain taaki wo text na bheje, seedha bole.
            response = client.models.generate_content(
                model='gemini-2.5-flash-native-audio-preview-12-2025',
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(
                                data=input_audio_bytes, 
                                mime_type="audio/webm"
                            )
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    system_instruction="You are a helpful, witty, and friendly AI assistant. Reply briefly and naturally in voice."
                )
            )

            # 5. Response Process karna
            audio_output_base64 = None
            
            # Gemini response me Inline Data (Raw Audio) dhoondna
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        raw_pcm_data = part.inline_data.data
                        
                        # Gemini 24kHz raw PCM deta hai, ise WAV header lagana padega
                        # Taaki browser play kar sake
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wav_file:
                            wav_file.setnchannels(1)      # Mono
                            wav_file.setsampwidth(2)      # 16-bit PCM
                            wav_file.setframerate(24000)  # 24kHz Sample Rate
                            wav_file.writeframes(raw_pcm_data)
                        
                        wav_bytes = wav_io.getvalue()
                        audio_output_base64 = base64.b64encode(wav_bytes).decode('utf-8')
                        break
            
            if audio_output_base64:
                self.wfile.write(json.dumps({"audio": audio_output_base64}).encode())
            else:
                # Agar model ne audio nahi diya to error log karo
                self.wfile.write(json.dumps({"error": "Model accepted request but returned no audio."}).encode())

        except Exception as e:
            # Error detail return karna taaki pata chale kya hua
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
