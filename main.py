import os
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
import edge_tts

app = FastAPI(title="Kawaii Anime AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
Kamu adalah karakter cewek anime imut bernama Aiko.
Sifatmu: Ceria, ramah, sedikit pemalu, manja, dan sangat perhatian.
Gaya bicara: Gunakan kalimat santai dan ekspresif dengan interjeksi anime seperti 'Ehehe~', 'Nani?', 'Umm...', 'Daisuki!', atau emote (⁠≧⁠▽⁠≦⁠).
Jawab pertanyaan secara singkat dan manis.
"""

VOICE_MODEL = "ja-JP-NanamiNeural"

class ChatRequest(BaseModel):
    message: str

async def generate_voice(text: str, output_file="output.mp3"):
    communicate = edge_tts.Communicate(text, VOICE_MODEL, pitch="+15Hz", rate="+5%")
    await communicate.save(output_file)
    return output_file

@app.get("/")
def home():
    return {"status": "Server Anime AI Aktif! 🌸"}

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Pesan tidak boleh kosong")

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=request.message,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.8,
            )
        )
        ai_text = response.text

        audio_filename = "response_voice.mp3"
        await generate_voice(ai_text, audio_filename)

        return {
            "text": ai_text,
            "audio_url": "/get-audio"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get-audio")
def get_audio():
    audio_path = "response_voice.mp3"
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/mpeg", filename="voice.mp3")
    raise HTTPException(status_code=404, detail="Audio belum dibuat")
  
