import streamlit as st
from sarvamai import SarvamAI
from sarvamai.play import save
import os
import tempfile
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
import time

# Load environment
load_dotenv()
SARVAM_API_KEY = st.secrets["SARVAM_API_KEY"] or os.getenv("SARVAM_API_KEY") or "YOUR_SARVAM_API_KEY"
client = SarvamAI(api_subscription_key=SARVAM_API_KEY)

# Language options
languages = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Kannada": "kn-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Bengali": "bn-IN",
    "Marathi": "mr-IN"
}

st.set_page_config(page_title="Sarvam STT ↔ Translate ↔ TTS", layout="wide")
st.title("🎙️ Real-Time Indic Speech Translator")
st.info("‼️ Source Language and Target Language MUST be different for this to work effectively. ‼️")

fs = 16000
max_duration = 30

# --- Initialize session state ---
for speaker in ['speaker1', 'speaker2']:
    st.session_state.setdefault(f"{speaker}_recording", False)
    st.session_state.setdefault(f"{speaker}_start_time", None)
    st.session_state.setdefault(f"{speaker}_audio", None)
    st.session_state.setdefault(f"{speaker}_text", "")
    st.session_state.setdefault(f"{speaker}_translated", "")
    st.session_state.setdefault(f"{speaker}_audio_path", "")
    st.session_state.setdefault(f"{speaker}_info", "")

def start_recording_speaker1():
    st.session_state.speaker1_recording = True
    st.session_state.speaker1_start_time = time.time()
    st.session_state.speaker1_audio = sd.rec(int(max_duration * fs), samplerate=fs, channels=1)
    st.session_state.speaker1_info = "🎙️ Recording Speaker 1... Please speak."

def start_recording_speaker2():
    st.session_state.speaker2_recording = True
    st.session_state.speaker2_start_time = time.time()
    st.session_state.speaker2_audio = sd.rec(int(max_duration * fs), samplerate=fs, channels=1)
    st.session_state.speaker2_info = "🎙️ Recording Speaker 2... Please speak."

# Layout
col1, col2 = st.columns(2)

languages_list = list(languages.keys())
# === SPEAKER 1 ===
with col1:
    st.subheader("🔈 Speaker 1 (Left to Right)")
    src_lang = st.selectbox("Source Language", languages_list, key="src",index=languages_list.index("Hindi"))

    if not st.session_state.speaker1_recording:
        st.button(
            "▶️ Start Recording",
            key="start1",
            on_click=start_recording_speaker1,
        )
        if st.session_state.speaker1_info:
            st.info(st.session_state.speaker1_info)
    else:
        if st.button("⏹️ Stop Recording", key="stop1"):
            st.session_state.speaker1_recording = False
            sd.stop()
            elapsed = min(int(time.time() - st.session_state.speaker1_start_time), max_duration)
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(temp_wav.name, st.session_state.speaker1_audio[:elapsed * fs], fs)

            with open(temp_wav.name, "rb") as f:
                stt_resp = client.speech_to_text.transcribe(
                    file=f,
                    model="saarika:v2.5",
                    language_code=languages[src_lang]
                )
            text = stt_resp.transcript.strip()
            st.session_state.speaker1_text = text

            tgt_code = languages[st.session_state.get("tgt", "Hindi")]
            translation = client.text.translate(
                input=text,
                source_language_code=languages[src_lang],
                target_language_code=tgt_code,
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False,
            ).translated_text
            st.session_state.speaker1_translated = translation

            tts = client.text_to_speech.convert(
                text=translation,
                target_language_code=tgt_code,
                speaker="anushka",
                enable_preprocessing=True
            )
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts, audio_path)
            st.session_state.speaker1_audio_path = audio_path

            st.session_state.speaker1_info = ""  # Clear info message

    # Always show last output if available
    if st.session_state.speaker1_text:
        st.markdown("✅ **Transcribed:**", unsafe_allow_html=True)
        st.markdown(
            f"<div style='padding: 8px 12px; background-color: #111; border-left: 4px solid #28a745;'>{st.session_state.speaker1_text}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.speaker1_translated:
        st.markdown("🌐 **Translated:**", unsafe_allow_html=True)
        st.markdown(
            f"<div style='padding: 8px 12px; background-color: #111; border-left: 4px solid #0d6efd;'>{st.session_state.speaker1_translated}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.speaker1_audio_path:
        st.audio(open(st.session_state.speaker1_audio_path, "rb").read(), format="audio/wav")

# === SPEAKER 2 ===
with col2:
    st.subheader("🔈 Speaker 2 (Right to Left)")
    tgt_lang = st.selectbox("Target Language", languages_list, key="tgt",index=languages_list.index("Kannada"))

    if not st.session_state.speaker2_recording:
        st.button(
            "▶️ Start Recording",
            key="start2",
            on_click=start_recording_speaker2,
        )
        if st.session_state.speaker2_info:
            st.info(st.session_state.speaker2_info)
    else:
        if st.button("⏹️ Stop Recording", key="stop2"):
            st.session_state.speaker2_recording = False
            sd.stop()
            elapsed = min(int(time.time() - st.session_state.speaker2_start_time), max_duration)
            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(temp_wav.name, st.session_state.speaker2_audio[:elapsed * fs], fs)

            with open(temp_wav.name, "rb") as f:
                stt_resp = client.speech_to_text.transcribe(
                    file=f,
                    model="saarika:v2.5",
                    language_code=languages[tgt_lang]
                )
            text = stt_resp.transcript.strip()
            st.session_state.speaker2_text = text

            src_code = languages[st.session_state.get("src", "English")]
            translation = client.text.translate(
                input=text,
                source_language_code=languages[tgt_lang],
                target_language_code=src_code,
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False,
            ).translated_text
            st.session_state.speaker2_translated = translation

            tts = client.text_to_speech.convert(
                text=translation,
                target_language_code=src_code,
                speaker="karun",
                enable_preprocessing=True
            )
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts, audio_path)
            st.session_state.speaker2_audio_path = audio_path

            st.session_state.speaker2_info = ""  # Clear info message

    # Always show last output if available
    if st.session_state.speaker2_text:
        st.markdown("✅ **Transcribed:**", unsafe_allow_html=True)
        st.markdown(
            f"<div style='padding: 8px 12px; background-color: #111; border-left: 4px solid #28a745;'>{st.session_state.speaker2_text}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.speaker2_translated:
        st.markdown("🌐 **Translated:**", unsafe_allow_html=True)
        st.markdown(
            f"<div style='padding: 8px 12px; background-color: #111; border-left: 4px solid #0d6efd;'>{st.session_state.speaker2_translated}</div>",
            unsafe_allow_html=True
        )

    if st.session_state.speaker2_audio_path:
        st.audio(open(st.session_state.speaker2_audio_path, "rb").read(), format="audio/wav")
