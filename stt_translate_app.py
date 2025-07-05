import streamlit as st
import os
import tempfile
import time
import sounddevice as sd
import soundfile as sf
from sarvamai import SarvamAI
from dotenv import load_dotenv

# ─── 1. CONFIG ────────────────────────────────────────────────────────────────
load_dotenv()
API_KEY = st.secrets.get("SARVAM_API_KEY") or os.getenv("SARVAM_API_KEY")
if not API_KEY:
    st.error("❌ Please set SARVAM_API_KEY in .env or secrets.toml")
    st.stop()
client = SarvamAI(api_subscription_key=API_KEY)

st.set_page_config(
    page_title="🎙️ STT-Translate Recorder",
    page_icon="🎧",
    layout="centered",
)

# ─── 2. UI: Mode Selection ────────────────────────────────────────────────────
st.title("🗣️ Speech-to-Text ➞ Translate")
st.markdown(
    "Either **upload** a short audio clip or **record** directly, then use Saaras-v2.5 to auto-detect, transcribe & translate."
)

mode = st.radio("Input method:", ["Upload file", "Record live"], index=0)

# ─── 3a. UPLOAD FLOW ─────────────────────────────────────────────────────────
audio_path = None
if mode == "Upload file":
    uploaded = st.file_uploader("Choose a .wav or .mp3 file", type=["wav", "mp3"])
    if uploaded:
        ext = os.path.splitext(uploaded.name)[1]
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        tmp.write(uploaded.read())
        audio_path = tmp.name
        st.audio(audio_path, format=f"audio/{ext.lstrip('.')}")


# ─── 3b. RECORD FLOW ─────────────────────────────────────────────────────────
else:
    if "recording" not in st.session_state:
        st.session_state.recording = False
        st.session_state.start_time = None
        st.session_state.audio_data = None

    fs = 16000
    max_secs = 30

    if not st.session_state.recording:
        if st.button("🔴 Start Recording"):
            st.session_state.recording = True
            st.session_state.start_time = time.time()
            st.session_state.audio_data = sd.rec(
                int(max_secs * fs), samplerate=fs, channels=1
            )
            st.info("Recording… click Stop when done")
    else:
        if st.button("⏹ Stop Recording"):
            sd.stop()
            st.session_state.recording = False
            secs = int(time.time() - st.session_state.start_time)
            st.success(f"Recorded {secs} sec")
            # save chunk
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(tmp.name, st.session_state.audio_data[: secs * fs], fs)
            audio_path = tmp.name
            st.audio(audio_path, format="audio/wav")

# ─── 4. SEND TO API ───────────────────────────────────────────────────────────
if audio_path:
    if st.button("🚀 Transcribe & Translate"):
        try:
            with open(audio_path, "rb") as f:
                resp = client.speech_to_text.translate(
                    file=f,
                    model="saaras:v2.5"
                )
        except Exception as e:
            st.error(f"API error: {e}")
        else:
            st.subheader("🔍 Raw Response")
            st.json(resp)

            detected = resp.get("detected_language", "unknown")
            transcript = resp.get("transcript") or resp.get("translated_text") or ""

            st.subheader("✅ Result")
            st.markdown(f"- **Detected Language**: `{detected}`")
            st.markdown(f"- **Transcript + Translation**:\n```\n{transcript}\n```")

# ─── 5. CREDITS SIDEBAR ───────────────────────────────────────────────────────
try:
    credits = client.account.get_credits_remaining()
    st.sidebar.markdown(f"**Credits Remaining:** {credits}")
except:
    pass
