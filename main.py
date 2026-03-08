import os
import asyncio
from pathlib import Path
import discord
from discord.ext import commands
from dotenv import load_dotenv
import edge_tts
import google.generativeai as genai
from moviepy import VideoFileClip, AudioFileClip, concatenate_videoclips
import yt_dlp

# Ładowanie kluczy z pliku .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Konfiguracja
VOICE = "pl-PL-MarekNeural"
GEMINI_MODEL = "gemini-1.5-flash"
TEMP_VIDEO = "tlo.mp4"
OUTPUT_AUDIO = "audio.mp3"
OUTPUT_VIDEO = "gotowy_film.mp4"

# Konfiguracja API
genai.configure(api_key=GEMINI_API_KEY)

# Konfiguracja Intencji (Naprawione!)
intents = discord.Intents.default()
intents.message_content = True 

bot = commands.Bot(command_prefix="!", intents=intents)

# Funkcja pobierająca wideo
def download_background(topic: str):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
        'outtmpl': TEMP_VIDEO,
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([f"ytsearch1:free stock footage {topic}"])

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

@bot.command(name="film")
async def film(ctx, *, topic: str):
    await ctx.send("Pobieram wideo i tworzę Twój viral... Czekaj ⏳")
    try:
        # 1. Pobierz wideo
        await asyncio.to_thread(download_background, topic)
        
        # 2. Generuj skrypt przez Gemini
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(f"Napisz krótki, dynamiczny scenariusz TikTok o: {topic}. Sam tekst bez nagłówków.")
        script = response.text
        
        # 3. Audio
        await edge_tts.Communicate(script, VOICE).save(OUTPUT_AUDIO)
        
        # 4. Montaż
        def build():
            video = VideoFileClip(TEMP_VIDEO)
            audio = AudioFileClip(OUTPUT_AUDIO)
            if video.duration < audio.duration:
                video = concatenate_videoclips([video] * (int(audio.duration // video.duration) + 1))
            final = video.subclipped(0, audio.duration).with_audio(audio)
            final.write_videofile(OUTPUT_VIDEO, codec="libx264", audio_codec="aac", fps=24)
            video.close(); audio.close(); final.close()
            
        await asyncio.to_thread(build)
        
        # 5. Wyślij
        await ctx.send(file=discord.File(OUTPUT_VIDEO))
    except Exception as e:
        await ctx.send(f"Błąd: {e}")

bot.run(DISCORD_TOKEN)