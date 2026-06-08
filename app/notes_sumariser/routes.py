from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
import os
import re
import tempfile
import shutil
import google.generativeai as genai
from moviepy.editor import VideoFileClip
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from faster_whisper import WhisperModel
import yt_dlp
from dotenv import load_dotenv

load_dotenv()

notes_bp = Blueprint("notes_sumariser", __name__, url_prefix="/notes_sumariser")

# Configure Gemini
api_key = os.getenv("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    print("GOOGLE_API_KEY not found in environment variables")

# Whisper Configuration
WHISPER_MODEL_NAME = os.getenv("WHISPER_MODEL", "tiny")
WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8_float16").lower()

_compute_type_aliases = {
    "fp16": "float16",
    "int8": "int8",
    "int8_float16": "int8_float16",
    "float32": "float32",
    "float16": "float16",
}

preferred_compute_types = [
    _compute_type_aliases.get(WHISPER_COMPUTE_TYPE, WHISPER_COMPUTE_TYPE),
]

if WHISPER_DEVICE == "cpu":
    for ct in ["int8_float16", "int8", "float32"]:
        if ct not in preferred_compute_types:
            preferred_compute_types.append(ct)
else:
    for ct in ["float16", "float32", "int8_float16", "int8"]:
        if ct not in preferred_compute_types:
            preferred_compute_types.append(ct)

whisper_model = None
whisper_loaded = False

def get_whisper_model():
    global whisper_model, whisper_loaded
    if whisper_loaded:
        return whisper_model
        
    for compute_type in preferred_compute_types:
        try:
            whisper_model = WhisperModel(WHISPER_MODEL_NAME, device=WHISPER_DEVICE, compute_type=compute_type)
            print(f"Loaded faster-whisper model '{WHISPER_MODEL_NAME}' with device='{WHISPER_DEVICE}' and compute_type='{compute_type}'")
            break
        except Exception as exc:
            print(f"Warning: Failed to load faster-whisper model ({WHISPER_MODEL_NAME}, compute_type={compute_type}): {exc}")
    
    if whisper_model is None:
        print("Could not load any supported faster-whisper compute type; transcription routes will fail until a compatible configuration is provided.")
        
    whisper_loaded = True
    return whisper_model

from urllib.parse import urlparse, parse_qs

def extract_video_id(url):
    parsed = urlparse(url)

    if parsed.hostname == "youtu.be":
        return parsed.path[1:]

    if parsed.hostname in ("www.youtube.com", "youtube.com"):
        return parse_qs(parsed.query).get("v", [None])[0]

    return None

def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)

        return " ".join(entry["text"] for entry in transcript)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as exc:
        print(f"Transcript error: {exc}")
        return None

def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".mp3")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    video.close()
    return audio_path

def transcribe_audio(audio_path):
    model = get_whisper_model()
    if model is None:
        raise RuntimeError("Whisper model is not loaded.")

    print(f"Transcribing audio using faster-whisper {WHISPER_MODEL_NAME}...")
    segments, _ = model.transcribe(audio_path, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments if segment.text).strip()

def summarize_with_gemini(text):
    if not text:
        return "No text provided for summarization."
    
    print("Summarizing text with Gemini...")
    try:
        model = genai.GenerativeModel("gemini-2.5-flash") # Switch to standard 2.5-flash for free tier
        response = model.generate_content(f"Summarise these notes in detail: {text}")
        return response.text if response.text else "No summary generated."
    except Exception as e:
        print(f"Gemini summarization error: {e}")
        return f"Error summarizing: {str(e)}"

def format_summary_html(summary_text):
    """Format summary with HTML styling for better presentation"""
    prompt = f"""Format the following summary into well-structured HTML with:
- Main heading (h2)
- Bold headings for sections (strong/b tags)
- Bullet points for lists (ul/li)
- Code blocks for technical content (if any)
- Proper paragraph formatting (p tags)

Summary to format:
{summary_text}

Return ONLY the HTML content without html/body tags. Use semantic HTML."""

    try:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        return response.text if response.text else summary_text
    except Exception as e:
        print(f"Gemini formatting error: {e}")
        return summary_text

@notes_bp.route("/")
def summariser_ui():
    return render_template("notes_summariser.html")

@notes_bp.route("/summarise_local", methods=["POST"])
def summarise_local():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
    
    video = request.files["video"]
    filename = secure_filename(video.filename)
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, filename)
    video.save(video_path)

    try:
        # Extract audio & transcribe
        audio_path = extract_audio(video_path)
        transcript = transcribe_audio(audio_path)
        
        # Summarize using Gemini
        summary = summarize_with_gemini(transcript)
        
        # Format with HTML
        formatted_summary = format_summary_html(summary)
        
        return jsonify({"summary": formatted_summary, "raw_text": transcript})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

@notes_bp.route("/summarise_youtube", methods=["POST"])
def summarise_youtube():
    data = request.get_json()
    yt_url = data.get("url")
    if not yt_url:
        return jsonify({"error": "No YouTube URL provided"}), 400

    temp_dir = tempfile.mkdtemp()
    try:
        video_id = extract_video_id(yt_url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL!"}), 400

        # Try getting transcript first
        transcript = get_youtube_transcript(video_id)

        # Always download the video and run faster-whisper.
        # This guarantees consistent transcription even when transcripts are disabled.
        print("Downloading YouTube video for faster-whisper transcription...")
        video_path = os.path.join(temp_dir, "%(title)s.%(ext)s")
        ydl_opts = {
            "outtmpl": video_path,
            "format": "best[ext=mp4]/best",
            "quiet": False,
            "no_warnings": False,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.download([yt_url])
            # Get the actual downloaded file path
            video_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
            if not video_files:
                raise Exception("Video download failed - no MP4 file found")
            video_path = os.path.join(temp_dir, video_files[0])

        audio_path = extract_audio(video_path)
        transcript = transcribe_audio(audio_path)

        # Summarize using Gemini
        summary = summarize_with_gemini(transcript)

        
        # Format with HTML
        formatted_summary = format_summary_html(summary)
        
        return jsonify({"summary": formatted_summary, "raw_text": transcript})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
@notes_bp.route("/upload_notes", methods=["POST"])
def upload_notes():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
        
    filename = secure_filename(file.filename)
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, filename)
    file.save(file_path)

    try:
        return jsonify({"message": f"File upload disabled temporarily.", "chunks": 0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
