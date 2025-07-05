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

# Language mapping
languages = {
    "English": "en-IN",
    "Hindi": "hi-IN",
    "Kannada": "kn-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Bengali": "bn-IN",
    "Marathi": "mr-IN"
}

# Page config
st.set_page_config(page_title="AI Conversational Buddy", layout="wide")
st.title("🤖 AI Conversational Buddy")
st.markdown("Speak in your language, get answers in another. Hear them both clearly!")

# Persona selection
default_personas = [
    "Vegetable Vendor",
    "Cab/Auto Driver",
    "Bus Conductor (Ticket Checker)",
    "Police Official",
    "Municipality Officer",
    "Your Landlord",
    "Your Crush",
    "Custom"
]
selected_persona = st.selectbox("🧑‍🎭 Choose a Persona", default_personas)
if selected_persona == "Custom":
    persona = st.text_input("✍️ Enter Custom Persona Description").strip()
else:
    persona = selected_persona

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'recorded_audio' not in st.session_state:
    st.session_state.recorded_audio = None

# Layout columns
col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("🎙️ Your Input")
    src_lang = st.selectbox("🗣️ Your Language", list(languages.keys()), key="src_lang")
    tgt_lang = st.selectbox("🌐 Target Language for AI Reply", list(languages.keys()), key="tgt_lang")

    fs = 16000
    max_duration = 30  # seconds

    # Start button
    if not st.session_state.recording:
        if st.button("🔴 Start Recording", key="start_btn"):
            st.session_state.recording = True
            st.session_state.start_time = time.time()
            st.session_state.recorded_audio = sd.rec(
                int(max_duration * fs),
                samplerate=fs,
                channels=1
            )
            st.info("Recording started... Click Stop when you're done.")

    # Stop button & processing
    else:
        if st.button("⏹️ Stop Recording", key="stop_btn"):
            st.session_state.recording = False
            sd.stop()
            elapsed = int(time.time() - st.session_state.start_time)
            st.success(f"Recording stopped after {elapsed} seconds")

            # write to temp WAV
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(tmp.name, st.session_state.recorded_audio[: elapsed * fs], fs)

            # 1) STT
            with open(tmp.name, "rb") as f:
                stt = client.speech_to_text.transcribe(
                    file=f,
                    model="saarika:v2.5",
                    language_code=languages[src_lang]
                )
            user_text = stt.transcript.strip()
            st.subheader("📝 Transcribed Text")
            st.code(user_text)

            # 2) Translate user→AI language
            user_to_ai = client.text.translate(
                input=user_text,
                source_language_code=languages[src_lang],
                target_language_code=languages[tgt_lang],
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False
            ).translated_text

            # 3) TTS: play translation of user input
            tts1 = client.text_to_speech.convert(
                text=user_to_ai,
                target_language_code=languages[tgt_lang],
                speaker="anushka",
                enable_preprocessing=True
            )
            path1 = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts1, path1)
            st.subheader("🔁 Your Message in Target Language")
            st.write(user_to_ai)
            st.audio(path1, format="audio/wav")

            # 4) Chat completion
            prompt = [
                {
                    "role": "system",
                    "content": (
                        f"You are {persona}. Stay in character and respond in {tgt_lang}. "
                        "Always provide a respectful, probable answer even if you're guessing. "
                    )
                },
                {"role": "user", "content": user_to_ai}
            ]
            with st.spinner("🤖 Thinking..."):
                ai_resp = client.chat.completions(
                    messages=prompt,
                    temperature=0.1,
                ).choices[0].message.content.strip()

            # 5) TTS: AI reply in target language
            tts2 = client.text_to_speech.convert(
                text=ai_resp,
                target_language_code=languages[tgt_lang],
                speaker="anushka",
                enable_preprocessing=True
            )
            path2 = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts2, path2)

            # 6) Translate AI→user language
            ai_to_user = client.text.translate(
                input=ai_resp,
                source_language_code=languages[tgt_lang],
                target_language_code=languages[src_lang],
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False
            ).translated_text
            tts3 = client.text_to_speech.convert(
                text=ai_to_user,
                target_language_code=languages[src_lang],
                speaker="karun",
                enable_preprocessing=True
            )
            path3 = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts3, path3)

            # Display AI’s response
            with col2:
                st.header("🤖 AI Response")
                st.subheader(f"💬 AI Answer ({tgt_lang})")
                st.write(ai_resp)
                st.audio(path2, format="audio/wav")

                st.subheader(f"🎧 Back in Your Language ({src_lang})")
                st.write(ai_to_user)
                st.audio(path3, format="audio/wav")

                st.caption("✅ Dual-language response lets you hear both sides clearly.")
