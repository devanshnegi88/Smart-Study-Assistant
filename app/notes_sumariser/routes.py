from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
from moviepy.editor import VideoFileClip
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline
import whisper
import yt_dlp
import os
import re
import tempfile
import google.generativeai as genai
from dotenv import load_dotenv



load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

notes_bp = Blueprint("notes_sumariser", __name__, url_prefix="/notes_sumariser")

# Load models once
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
whisper_model = whisper.load_model("base")

# Helper functions
def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        text = " ".join([entry["text"] for entry in transcript])
        return text
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as e:
        print(f"⚠ Transcript error: {e}")
        return None

def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".mp3")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    video.close()
    return audio_path

def transcribe_audio(audio_path):
    print("🎧 Transcribing audio using Whisper...")
    result = whisper_model.transcribe(audio_path)
    return result["text"]

def chunk_text(text, max_tokens=900):
    sentences = text.split(". ")
    chunks, current_chunk = [], ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_tokens:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

def summarize_text(text):
    print("🧠 Summarizing text...")
    chunks = chunk_text(text)
    summaries = []
    for i, chunk in enumerate(chunks):
        print(f"📝 Summarizing chunk {i+1}/{len(chunks)}...")
        summary = summarizer(chunk, max_length=200, min_length=50, do_sample=False)[0]["summary_text"]
        summaries.append(summary)
    return " ".join(summaries)

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

    model = genai.GenerativeModel("gemini-2.5-flash-lite")
    response = model.generate_content(prompt)
    return response.text if response.text else summary_text

# Routes
@notes_bp.route("/")
def sumariser_ui():
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
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(f"Summarise these notes in detail: {transcript}")
        summary = response.text if response.text else "No summary generated."
        
        # Format with HTML
        formatted_summary = format_summary_html(summary)
        
        return jsonify({"summary": formatted_summary, "raw_text": summary})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

@notes_bp.route("/summarise_youtube", methods=["POST"])
def summarise_youtube():
    data = request.get_json()
    yt_url = data.get("url")
    if not yt_url:
        return jsonify({"error": "No YouTube URL provided"}), 400

    try:
        temp_dir = tempfile.mkdtemp()
        video_id = extract_video_id(yt_url)
        
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL!"}), 400

        # Try getting transcript first
        transcript = get_youtube_transcript(video_id)

        if not transcript:
            # Download & transcribe video
            print("⚠ No transcript found, downloading video...")
            video_path = os.path.join(temp_dir, "yt_video.mp4")
            ydl_opts = {"outtmpl": video_path, "format": "mp4"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([yt_url])
            
            audio_path = extract_audio(video_path)
            transcript = transcribe_audio(audio_path)

        # Summarize using Gemini
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(f"Summarise these notes in detail: {transcript}")
        summary = response.text if response.text else "No summary generated."
        
        # Format with HTML
        formatted_summary = format_summary_html(summary)
        
        return jsonify({"summary": formatted_summary, "raw_text": summary})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500