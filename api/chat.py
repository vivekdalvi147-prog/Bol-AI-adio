import os
import json
import base64
import google.generativeai as genai
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # CORS allow karne ke liye headers
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

            # Vercel Environment Variable se API key lena
            api_key = os.environ.get("Google_api_vivek")
            if not api_key:
                self.wfile.write(json.dumps({"error": "API Key (Google_api_vivek) Vercel me set nahi hai"}).encode())
                return

            # Gemini API configure karna
            genai.configure(api_key=api_key)
            
            # Model initialize karna (gemini-2.5-flash ya gemini-2.0-flash)
            model = genai.GenerativeModel("gemini-2.5-flash")

            # Base64 string ko bytes me convert karna
            audio_bytes = base64.b64decode(audio_b64)

            # Gemini ke liye audio part create karna
            audio_part = {
                "mime_type": "audio/webm",
                "data": audio_bytes
            }

            # AI ko prompt + audio bhejna
            response = model.generate_content([
                "You are a helpful and friendly AI assistant. Listen to the user's audio and give a short, direct, and helpful response.",
                audio_part
            ])

            # Reply wapas frontend ko bhejna
            self.wfile.write(json.dumps({"reply": response.text}).encode())

        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            
    # OPTIONS method for CORS preflight
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
