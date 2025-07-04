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
SARVAM_API_KEY = st.secrets["SARVAM_API_KEY"]
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
st.title("🤖 AI Voice Chatbot Translator")
st.markdown("Speak in your language, get answers in another. Hear them both clearly!")

# Initialize session state
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'recorded_audio' not in st.session_state:
    st.session_state.recorded_audio = None

# Layout
col1, col2 = st.columns([1, 1.2])

with col1:
    st.header("🎙️ Your Input")
    src_lang = st.selectbox("🗣️ Your Language", list(languages.keys()), key="src_lang")
    tgt_lang = st.selectbox("🌐 Target Language for AI Reply", list(languages.keys()), key="tgt_lang")

    fs = 16000
    max_duration = 30

    if st.button("🔴 Start/Stop Recording"):
        if not st.session_state.recording:
            st.session_state.recording = True
            st.session_state.start_time = time.time()
            st.session_state.recorded_audio = sd.rec(int(max_duration * fs), samplerate=fs, channels=1)
            st.info("Recording started... Click again to stop.")
        else:
            st.session_state.recording = False
            sd.stop()
            elapsed_time = int(time.time() - st.session_state.start_time)
            st.success(f"Recording stopped after {elapsed_time} seconds")

            temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            sf.write(temp_wav.name, st.session_state.recorded_audio[:elapsed_time * fs], fs)

            with open(temp_wav.name, "rb") as f:
                stt = client.speech_to_text.transcribe(
                    file=f,
                    model="saarika:v2.5",
                    language_code=languages[src_lang]
                )
            user_text = stt.transcript.strip()

            st.success("📝 Transcribed Text")
            st.code(user_text)

            orig_translated = client.text.translate(
                input=user_text,
                source_language_code=languages[src_lang],
                target_language_code=languages[tgt_lang],
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False
            ).translated_text

            tts_orig_translated = client.text_to_speech.convert(
                text=orig_translated,
                target_language_code=languages[tgt_lang],
                speaker="anushka",
                enable_preprocessing=True
            )
            tts_orig_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts_orig_translated, tts_orig_path)

            st.subheader("🔁 Translated Version of Your Message")
            st.write(orig_translated)
            st.audio(tts_orig_path, format="audio/wav")

            trans_to_english = client.text.translate(
                input=user_text,
                source_language_code=languages[src_lang],
                target_language_code="en-IN",
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False
            ).translated_text

            prompt_messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. Always respond in a natural, informative way "
                        "in the language of the message. Give a probable answer please. "
                        "If the user asks about prices, locations, or real-world details, give a "
                        "probable answer based on common sense or typical rates, even if you're unsure. "
                        "Do not say 'I can't help' — always provide a useful and respectful response."
                    )
                },
                {"role": "user", "content": "Tell me about Indian classical music."},
                {"role": "assistant", "content": "Indian classical music is one of the oldest musical traditions in the world, with roots in the Vedas. It has two main traditions: Hindustani and Carnatic."},
                {"role": "user", "content": "अम्मा एप्पल कितने का है?"},
                {"role": "assistant", "content": "अम्मा, एक सेब लगभग 30 रुपये का है।"},
                {"role": "user", "content": "ಒಂದು ಸೇಬಿನ ಬೆಲೆ ಎಷ್ಟು?"},
                {"role": "assistant", "content": "ಒಂದು ಸೇಬಿನ ಬೆಲೆ ಸುಮಾರು ೩೦ ರೂಪಾಯಿ."},
                {"role": "user", "content": "அம்மா, ஆப்பிள் எவ்ளோ காசு?"},
                {"role": "assistant", "content": "ஒரு ஆப்பிள் சுமார் 30 ரூபாய் ஆகும்."},
                {"role": "user", "content": trans_to_english}
            ]

            with st.spinner("🤖 Thinking..."):
                ai_response = client.chat.completions(
                    messages=prompt_messages,
                    temperature=0.7
                ).choices[0].message.content.strip()

            translated_to_target = client.text.translate(
                input=ai_response,
                source_language_code="en-IN",
                target_language_code=languages[tgt_lang],
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False
            ).translated_text

            tts_target = client.text_to_speech.convert(
                text=translated_to_target,
                target_language_code=languages[tgt_lang],
                speaker="anushka",
                enable_preprocessing=True
            )
            tts_target_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts_target, tts_target_path)

            translated_to_user = client.text.translate(
                input=ai_response,
                source_language_code="en-IN",
                target_language_code=languages[src_lang],
                model="sarvam-translate:v1",
                mode="formal",
                speaker_gender="Male",
                enable_preprocessing=False
            ).translated_text

            tts_user = client.text_to_speech.convert(
                text=translated_to_user,
                target_language_code=languages[src_lang],
                speaker="karun",
                enable_preprocessing=True
            )
            tts_user_path = tempfile.NamedTemporaryFile(delete=False, suffix=".wav").name
            save(tts_user, tts_user_path)

            with col2:
                st.header("🤖 AI Response")

                st.subheader("💬 AI Answer (English)")
                st.write(ai_response)

                st.subheader(f"🗣️ Spoken in {tgt_lang}")
                st.write(translated_to_target)
                st.audio(tts_target_path, format="audio/wav")

                st.subheader(f"🎧 Back in Your Language ({src_lang})")
                st.write(translated_to_user)
                st.audio(tts_user_path, format="audio/wav")

                st.caption("✅ Dual-language response lets you learn and understand both sides.")