"""
JARVIS Voice System — v3 (Streaming STT)
────────────────────────────────────────────────────────────────
STT:  RealtimeSTT — streams audio into Whisper in real-time.
      Transcript fires the instant you stop speaking — zero wait.
TTS:  Kokoro-82M GPU → Piper CPU fallback
Wake: openwakeword hey_jarvis (optional, currently disabled)
"""

import numpy as np
import sounddevice as sd
import wave
import tempfile
import os
import subprocess
import re
import threading
import time

from faster_whisper import WhisperModel
from openwakeword.model import Model as WakeWordModel

# ── STT — faster-whisper batch ───────────────────────────────────────
print("[JARVIS] Loading Whisper STT model...")
stt_model = WhisperModel("small", device="cuda", compute_type="int8_float16")

# ── Wake word ─────────────────────────────────────────────────────────
print("[JARVIS] Loading wake word model (hey_jarvis)...")
_HEY_JARVIS_MODEL = "/home/kiko/.local/lib/python3.12/site-packages/openwakeword/resources/models/hey_jarvis_v0.1.onnx"
wake_model = WakeWordModel(wakeword_model_paths=[_HEY_JARVIS_MODEL])

SAMPLE_RATE       = 16000
CHUNK_SIZE        = 1280
SILENCE_THRESHOLD = 0.008  # balanced — catches speech, ignores breath
SILENCE_DURATION  = 0.8   # 0.8s — fast cutoff after you stop speaking

PIPER_PATH = f'/home/{os.getenv("USER")}/.local/bin'
STT_PROMPT = "Commands for an AI assistant: open, close, run, search, what is, explain, show me, status, shutdown."

# ── Kokoro GPU TTS ────────────────────────────────────────────────────
KOKORO_VOICE = "bm_george"
KOKORO_SPEED = 1.12

_kokoro_pipeline  = None
_kokoro_available = False
_kokoro_ready     = threading.Event()


def _init_kokoro():
    global _kokoro_pipeline, _kokoro_available
    try:
        print("[JARVIS TTS] Initialising Kokoro on CUDA...")
        from kokoro import KPipeline
        _kokoro_pipeline  = KPipeline(lang_code='b', device='cuda')
        _kokoro_available = True
        print(f"[JARVIS TTS] Kokoro ready — voice: {KOKORO_VOICE} | device: CUDA")
    except Exception as e:
        print(f"[JARVIS TTS] Kokoro init failed: {e} — Piper fallback active")
        _kokoro_available = False
    finally:
        _kokoro_ready.set()


threading.Thread(target=_init_kokoro, daemon=True).start()


def _generate_kokoro(sentence: str):
    if not _kokoro_available or _kokoro_pipeline is None:
        return None
    try:
        import soundfile as sf
        samples = []
        for _, _, audio in _kokoro_pipeline(sentence, voice=KOKORO_VOICE, speed=KOKORO_SPEED):
            if audio is not None:
                samples.append(audio)
        if not samples:
            return None
        audio_np = np.concatenate(samples)
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False, dir='/tmp') as f:
            path = f.name
        sf.write(path, audio_np, 24000)
        return path
    except Exception as e:
        print(f"[JARVIS TTS] Kokoro generation error: {e}")
        return None


def _generate_piper(sentence: str):
    piper_bin  = os.path.join(PIPER_PATH, 'piper')
    model_path = os.path.expanduser('~/jarvis-core/tts/en_GB-alan-medium.onnx')
    if not os.path.exists(piper_bin) or not os.path.exists(model_path):
        return None
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False, dir='/tmp') as f:
            path = f.name
        proc = subprocess.run(
            [piper_bin, '--model', model_path, '--output_file', path],
            input=sentence.encode(),
            capture_output=True, timeout=10
        )
        return path if os.path.exists(path) and os.path.getsize(path) > 0 else None
    except Exception as e:
        print(f"[JARVIS TTS] Piper error: {e}")
        return None


def generate_audio(sentence: str):
    sentence = sentence.strip()
    if not sentence:
        return None
    if not _kokoro_ready.is_set():
        _kokoro_ready.wait(timeout=4.0)
    path = _generate_kokoro(sentence)
    if path:
        return path
    return _generate_piper(sentence)


def play_audio(path: str):
    if not path or not os.path.exists(path):
        return
    subprocess.run(
        ['pw-play', path],
        env={
            **os.environ,
            'XDG_RUNTIME_DIR':    '/run/user/1000',
            'PULSE_RUNTIME_PATH': '/run/user/1000/pulse',
        }
    )
    try:
        os.unlink(path)
    except Exception:
        pass


def speak_sentence(sentence: str):
    path = generate_audio(sentence)
    if path:
        play_audio(path)


def speak(text: str):
    for sentence in split_sentences(text):
        speak_sentence(sentence)


def split_sentences(text: str) -> list:
    parts = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]


def is_silent(chunk):
    return np.sqrt(np.mean(chunk**2)) < SILENCE_THRESHOLD


def record_command():
    print("[JARVIS] Listening for command...")
    frames, silence_frames = [], 0
    max_silence  = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK_SIZE)
    max_duration = int(15.0 * SAMPLE_RATE / CHUNK_SIZE)

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype='float32', blocksize=CHUNK_SIZE,
                        device=None) as stream:
        for _ in range(int(5.0 * SAMPLE_RATE / CHUNK_SIZE)):
            chunk, _ = stream.read(CHUNK_SIZE)
            chunk    = chunk.flatten()
            if not is_silent(chunk):
                frames.append(chunk)
                break
        for _ in range(max_duration):
            chunk, _ = stream.read(CHUNK_SIZE)
            chunk    = chunk.flatten()
            frames.append(chunk)
            if is_silent(chunk):
                silence_frames += 1
                if silence_frames >= max_silence:
                    break
            else:
                silence_frames = 0

    if not frames:
        return np.zeros(CHUNK_SIZE, dtype=np.float32)
    return np.concatenate(frames)


def transcribe(audio: np.ndarray) -> str:
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        path = f.name
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((audio * 32767).astype(np.int16).tobytes())
    segments, _ = stt_model.transcribe(
        path,
        language                   = "en",
        initial_prompt             = STT_PROMPT,
        beam_size                  = 1,
        vad_filter                 = True,
        vad_parameters             = {"min_silence_duration_ms": 400},
        condition_on_previous_text = False,
        temperature                = 0.0,
    )
    text = " ".join(s.text for s in segments).strip()
    os.unlink(path)
    return text


# ── Wake word ─────────────────────────────────────────────────────────

def listen_for_wakeword():
    print("[JARVIS] Wake word detection active — say 'Hey JARVIS' to activate")
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1,
                        dtype='float32', blocksize=CHUNK_SIZE,
                        device=None) as stream:
        while True:
            chunk, _   = stream.read(CHUNK_SIZE)
            chunk      = chunk.flatten()
            prediction = wake_model.predict(chunk)
            score      = list(prediction.values())[0]
            if score > 0.15:
                print(f"[JARVIS] Wake word detected! (score={score:.2f})")
                return True
