from flask import Blueprint, render_template, request, jsonify
from werkzeug.utils import secure_filename
<<<<<<< HEAD
from moviepy.video.io.VideoFileClip import VideoFileClip
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from faster_whisper import WhisperModel
=======
from moviepy.editor import VideoFileClip
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline
import whisper
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
import yt_dlp
import os
import re
import tempfile
import shutil

notes_bp = Blueprint("notes_sumariser", __name__, url_prefix="/notes_sumariser")

<<<<<<< HEAD
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
for compute_type in preferred_compute_types:
    try:
        whisper_model = WhisperModel(WHISPER_MODEL_NAME, device=WHISPER_DEVICE, compute_type=compute_type)
        print(f"✅ Loaded faster-whisper model '{WHISPER_MODEL_NAME}' with device='{WHISPER_DEVICE}' and compute_type='{compute_type}'")
        break
    except Exception as exc:
        print(f"⚠ Failed to load faster-whisper model ({WHISPER_MODEL_NAME}, compute_type={compute_type}): {exc}")

if whisper_model is None:
    print("⚠ Could not load any supported faster-whisper compute type; transcription routes will fail until a compatible configuration is provided.")


=======
# Load models once
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
whisper_model = whisper.load_model("base")

# Helper functions
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
def extract_video_id(url):
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, url)
    return match.group(1) if match else None

<<<<<<< HEAD

def get_youtube_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join(entry["text"] for entry in transcript)
    except (TranscriptsDisabled, NoTranscriptFound):
        return None
    except Exception as exc:
        print(f"⚠ Transcript error: {exc}")
        return None


=======
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

>>>>>>> 84e29029a03bff646e1397431a9616823050952e
def extract_audio(video_path):
    audio_path = tempfile.mktemp(suffix=".mp3")
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path, logger=None)
    video.close()
    return audio_path

<<<<<<< HEAD

def transcribe_audio(audio_path):
    if whisper_model is None:
        raise RuntimeError("Whisper model is not loaded.")

    print("🎧 Transcribing audio using faster-whisper tiny...")
    segments, _ = whisper_model.transcribe(audio_path, beam_size=5)
    return " ".join(segment.text.strip() for segment in segments if segment.text).strip()


def make_safe_summary(text, max_length=2500):
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


=======
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
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
@notes_bp.route("/")
def summariser_ui():
    return render_template("notes_summariser.html")


@notes_bp.route("/summarise_local", methods=["POST"])
def summarise_local():
    if "video" not in request.files:
        return jsonify({"error": "No video file provided"}), 400
<<<<<<< HEAD

=======
    
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
    video = request.files["video"]
    filename = secure_filename(video.filename)
    temp_dir = tempfile.mkdtemp()
    video_path = os.path.join(temp_dir, filename)
    video.save(video_path)

    try:
<<<<<<< HEAD
        audio_path = extract_audio(video_path)
        transcript = transcribe_audio(audio_path)
        summary = make_safe_summary(transcript)
        return jsonify({"summary": summary, "raw_text": transcript})
    except Exception as exc:
        return jsonify({"error": f"Error: {exc}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

=======
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
>>>>>>> 84e29029a03bff646e1397431a9616823050952e

@notes_bp.route("/summarise_youtube", methods=["POST"])
def summarise_youtube():
    data = request.get_json()
    yt_url = data.get("url")
    if not yt_url:
        return jsonify({"error": "No YouTube URL provided"}), 400

<<<<<<< HEAD
    temp_dir = tempfile.mkdtemp()
    try:
        video_id = extract_video_id(yt_url)
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL!"}), 400

        transcript = get_youtube_transcript(video_id)
        if not transcript:
=======
    try:
        temp_dir = tempfile.mkdtemp()
        video_id = extract_video_id(yt_url)
        
        if not video_id:
            return jsonify({"error": "Invalid YouTube URL!"}), 400

        # Try getting transcript first
        transcript = get_youtube_transcript(video_id)

        if not transcript:
            # Download & transcribe video
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
            print("⚠ No transcript found, downloading video...")
            video_path = os.path.join(temp_dir, "yt_video.mp4")
            ydl_opts = {"outtmpl": video_path, "format": "mp4"}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([yt_url])
<<<<<<< HEAD

            audio_path = extract_audio(video_path)
            transcript = transcribe_audio(audio_path)

        summary = make_safe_summary(transcript or "")
        return jsonify({"summary": summary, "raw_text": transcript})
    except Exception as exc:
        return jsonify({"error": f"Error: {exc}"}), 500
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
=======
            
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
>>>>>>> 84e29029a03bff646e1397431a9616823050952e
