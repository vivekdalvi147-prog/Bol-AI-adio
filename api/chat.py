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
        # CORS set karna
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            # Request body read karna
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            audio_b64 = data.get('audio')
            
            if not audio_b64:
                self.wfile.write(json.dumps({"error": "Audio data nahi mila"}).encode())
                return

            # Vercel Environment Variable
            api_key = os.environ.get("Google_api_vivek")
            if not api_key:
                self.wfile.write(json.dumps({"error": "API Key (Google_api_vivek) nahi mili"}).encode())
                return

            # Naya GenAI client initialize karna
            client = genai.Client(api_key=api_key)
            audio_bytes = base64.b64decode(audio_b64)

            # --- TRUE NATIVE AUDIO REQUEST ---
            # Hum model ko bata rahe hain ki sirf AUDIO (Voice) me reply kare
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Listen to the user's audio and respond completely in a helpful voice.",
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/webm")
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"]  # Yahan Native Audio set kiya hai
                )
            )

            audio_output_base64 = None
            
            # Model ke response se NATIVE VOICE extract karna
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data:
                        # Gemini Raw 24kHz PCM audio deta hai
                        raw_pcm_bytes = part.inline_data.data
                        
                        # Use browser ke liye Playable WAV format me pack karna
                        wav_io = io.BytesIO()
                        with wave.open(wav_io, 'wb') as wf:
                            wf.setnchannels(1)       # Mono
                            wf.setsampwidth(2)       # 16-bit
                            wf.setframerate(24000)   # Gemini ki standard sample rate 24kHz
                            wf.writeframes(raw_pcm_bytes)
                            
                        wav_bytes = wav_io.getvalue()
                        # Base64 me wapas UI ko bhejna
                        audio_output_base64 = base64.b64encode(wav_bytes).decode('utf-8')
                        break

            if audio_output_base64:
                self.wfile.write(json.dumps({"audio": audio_output_base64}).encode())
            else:
                self.wfile.write(json.dumps({"error": "Model ne Audio return nahi kiya. Dubara try karein."}).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"error": f"Backend Error: {str(e)}"}).encode())
            
    # Preflight Request ke liye
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
