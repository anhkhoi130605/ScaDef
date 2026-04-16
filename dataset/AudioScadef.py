import yt_dlp
from pydub import AudioSegment
from groq import Groq
import os
import json
import re
import shutil
import torch
from pathlib import Path
# ===== CONFIG =====
OUTPUT_DIR = r"D:\Resconnect-References\Data\Audio\Script(Kich-Ban)"
FFMPEG_BIN = r"C:\Users\ADMIN\Downloads\ffmpeg-8.1-full_build\ffmpeg-8.1-full_build\bin"


def load_env_file(env_path):
    if not env_path.exists():
        return

    with env_path.open("r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file(Path(__file__).resolve().parent.parent / "Secret" / ".env")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is missing. Set it in Secret/.env.")

client = Groq(api_key=GROQ_API_KEY)



AudioSegment.converter = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(FFMPEG_BIN, "ffprobe.exe")


def ensure_ffmpeg_for_whisper():
    # Whisper calls `ffmpeg` via subprocess, so it must be discoverable on PATH.
    if os.path.isdir(FFMPEG_BIN) and FFMPEG_BIN not in os.environ.get("PATH", ""):
        os.environ["PATH"] = FFMPEG_BIN + os.pathsep + os.environ.get("PATH", "")

    if shutil.which("ffmpeg") is None:
        raise RuntimeError(
            "ffmpeg was not found. Install ffmpeg or update FFMPEG_BIN to the correct bin folder."
        )


def load_whisper_module():
    try:
        import whisper
    except Exception as exc:
        raise RuntimeError(
            "Failed to import OpenAI Whisper. If you installed package `whisper`, remove it and install `openai-whisper`: "
            "`python -m pip uninstall -y whisper` then `python -m pip install -U openai-whisper`."
        ) from exc

    whisper_file = (getattr(whisper, "__file__", "") or "").lower()
    if whisper_file.endswith("site-packages\\whisper.py"):
        raise RuntimeError(
            "Detected wrong module `whisper.py`. Please uninstall package `whisper` and install `openai-whisper`."
        )

    return whisper

# ===== 1. DOWNLOAD AUDIO =====
def download_audio(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'audio.%(ext)s',
        'ffmpeg_location': r"C:\Users\ADMIN\Downloads\ffmpeg-8.1-full_build\ffmpeg-8.1-full_build\bin",
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return "audio.wav"


# ===== 2. TRANSCRIBE (WHISPER) =====
def transcribe(audio_file):
    ensure_ffmpeg_for_whisper()
    whisper = load_whisper_module()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    model = whisper.load_model("base", device=device)  # đổi medium nếu cần
    result = model.transcribe(audio_file)
    return result["segments"]


# ===== 3. CLEAN JSON =====
def safe_json_parse(text):
    if text is None:
        return []

    cleaned = re.sub(r"```json|```", "", text, flags=re.IGNORECASE).strip()
    if not cleaned:
        return []

    decoder = json.JSONDecoder()

    # Fast path: response is already valid JSON.
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        pass

    # Fallback: find the first JSON payload embedded in prose.
    for idx, ch in enumerate(cleaned):
        if ch not in "[{":
            continue
        try:
            parsed, _ = decoder.raw_decode(cleaned[idx:])
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            continue

    return []


def normalize_scam_segments(raw_segments):
    normalized = []

    if not isinstance(raw_segments, list):
        return normalized

    for item in raw_segments:
        if not isinstance(item, dict):
            continue

        try:
            start = float(item.get("start"))
            end = float(item.get("end"))
        except (TypeError, ValueError):
            continue

        if end <= start:
            continue

        normalized.append({
            "start": start,
            "end": end,
            "type": item.get("type", "scam"),
        })

    return normalized


# ===== 4. DETECT SCAM (LLM - GROQ) =====
def detect_scam(segments):
    text_block = "\n".join([
        f"[{s['start']} - {s['end']}] {s['text']}"
        for s in segments
    ])

    prompt = f"""
Transcript có timestamp.

Nhiệm vụ:
1. Phân loại từng đoạn:
   - "narration": mô tả, giải thích, kịch bản
   - "dialogue": nội dung cuộc gọi thật

2. Chỉ trong các đoạn "dialogue", xác định đoạn có dấu hiệu lừa đảo.

Dấu hiệu scam:
- yêu cầu OTP
- yêu cầu chuyển tiền
- giả danh ngân hàng / công an
- tạo áp lực khẩn cấp

Chỉ trả về JSON:
[
  {{
    "start": ...,
    "end": ...,
    "type": "scam"
  }}
]

Nếu không có → []

Transcript:
{text_block}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return normalize_scam_segments(safe_json_parse(response.choices[0].message.content))


# ===== 5. CUT AUDIO =====
def cut_audio(file, segments):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Output folder: {OUTPUT_DIR}")

    if not segments:
        print("No valid scam segments to cut.")
        return []

    audio = AudioSegment.from_wav(file)
    outputs = []

    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            continue

        if "start" not in seg or "end" not in seg:
            continue

        start = int(seg["start"] * 1000)
        end = int(seg["end"] * 1000)

        chunk = audio[start:end]

        name = os.path.join(OUTPUT_DIR, f"scam_{i}_{start}.wav")
        chunk.export(name, format="wav")

        outputs.append(name)

    print(f"Saved {len(outputs)} file(s) to output folder.")

    return outputs


# ===== 6. MAIN PIPELINE =====
def process_youtube(url):
    print("1. Downloading audio...")
    audio = download_audio(url)

    print("2. Transcribing...")
    segments = transcribe(audio)

    print("3. Detecting scam (LLM)...")
    scam_segments = detect_scam(segments)
    print(f"Detected scam segments: {len(scam_segments)}")

    print("4. Cutting audio...")
    files = cut_audio(audio, scam_segments)

    return files


# ===== RUN =====
if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=S2d6pgE1T5k"
    result = process_youtube(url)

    print("DONE:", result)