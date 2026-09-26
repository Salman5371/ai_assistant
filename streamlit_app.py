"""Optional single-user local Streamlit frontend."""
import hashlib
import tempfile
import time


def main():
    import streamlit as st
    from ai.memory import MemoryStore
    from assistant.pipeline import AssistantPipeline
    from assistant.models import CommandUnavailableError
    from assistant import services
    from ui.audio import decode_upload, pcm_for_stt
    st.set_page_config(page_title="Multimodal AI Assistant", layout="wide")
    st.title("Multimodal AI Assistant")
    st.caption("Speech and audio intelligence | local workspace | pretrained models")
    with st.sidebar:
        st.header("Session settings")
        backend = st.selectbox("Speech-to-text", ["google", "whisper", "auto"])
        fallback = st.checkbox("Allow Google fallback (uploads audio)", value=True)
        st.caption("Google sends audio to Google. Local models may download weights on first use.")
        desktop = st.checkbox("Allow desktop automation on this computer", value=False)
        tts = st.checkbox("Speak responses on this computer", value=False)
        st.caption("Single-user local app. SQLite memory is shared with the terminal.")

    def resolve(name):
        if name in {"start_face_detection", "start_age_gender_detection", "start_hand_tracking"}:
            raise CommandUnavailableError("Use the terminal for native webcam windows")
        if name in {"analyze_voice_emotion", "analyze_audio_events"}:
            raise CommandUnavailableError("Use the Audio workspace to record or upload a clip")
        if not desktop and name in {"open_website", "open_app", "open_folder", "search_google", "search_youtube", "shutdown_computer", "restart_computer", "cancel_shutdown"}:
            raise CommandUnavailableError("Enable desktop automation in the sidebar first")
        return getattr(services, name)

    if "pipeline" not in st.session_state:
        st.session_state.pipeline = AssistantPipeline()
        st.session_state.messages = []
    pipeline = st.session_state.pipeline
    pipeline.resolve, pipeline.emit = resolve, st.info

    def respond(command):
        response = pipeline.handle(command)
        st.session_state.messages.extend([{"role": "user", "content": command}, {"role": "assistant", "content": response.text}])
        st.write(response.text)
        if tts:
            from assistant.responses import safe_speak
            safe_speak(response.text)
        if not response.continue_running:
            st.info("Session ended. You can start another command here.")

    chat, audio_tab, memory_tab = st.tabs(["Assistant chat", "Audio workspace", "Memory"])
    with chat:
        st.subheader("Assistant chat")
        st.caption("Rule-based commands, not an LLM chatbot. Try help, remember ..., show memory, or what is the time.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
        command = st.chat_input("Type an assistant command")
        if command:
            with st.chat_message("user"):
                st.write(command)
            with st.chat_message("assistant"):
                respond(command)
    with audio_tab:
        st.subheader("Record or upload")
        source = st.radio("Audio source", ["Microphone", "WAV upload"], horizontal=True)
        upload = st.audio_input("Record a clip", sample_rate=16000) if source == "Microphone" else st.file_uploader("PCM WAV: 0.1-60 seconds, up to 20 MiB", type=["wav"])
        if upload is not None:
            raw = upload.getvalue()
            digest = hashlib.sha256(raw).hexdigest()
            if st.session_state.get("audio_digest") != digest:
                st.session_state.audio_digest = digest
                st.session_state.audio_results = {}
            results = st.session_state.audio_results
            try:
                samples, rate = decode_upload(raw)
            except Exception as error:
                st.error(f"Cannot read this audio: {error}")
            else:
                st.audio(raw, format="audio/wav")
                st.caption(f"{len(samples) / rate:.2f} seconds | {rate:,} Hz")
                columns = st.columns(4)
                for column, action in zip(columns, ["Transcribe", "Analyze emotion", "Classify sounds", "Generate plots"]):
                    if column.button(action):
                        key = {"Transcribe": "transcription", "Analyze emotion": "emotion", "Classify sounds": "events", "Generate plots": "plots"}[action]
                        results.pop(key, None)
                        start = time.perf_counter()
                        try:
                            with st.spinner(action + " (first use may load model weights)..."):
                                if key == "transcription":
                                    from voice.stt import transcribe
                                    results[key] = transcribe(pcm_for_stt(samples), rate, backend=backend, google_fallback=fallback)
                                    if not results[key]:
                                        st.warning("No transcription returned. Check audio quality/backend dependencies; typed commands remain available.")
                                elif key == "emotion":
                                    from audio_intelligence.emotion_recognition import PretrainedEmotionRecognizer
                                    if "emotion_model" not in st.session_state:
                                        st.session_state.emotion_model = PretrainedEmotionRecognizer()
                                    results[key] = st.session_state.emotion_model.recognize(samples, rate)
                                elif key == "events":
                                    from audio_intelligence.audio_event_classifier import PretrainedAudioEventClassifier
                                    if "event_model" not in st.session_state:
                                        st.session_state.event_model = PretrainedAudioEventClassifier()
                                    results[key] = st.session_state.event_model.classify(samples, rate)
                                else:
                                    from audio_intelligence.visualization import generate_audio_plots
                                    with tempfile.TemporaryDirectory(prefix="assistant-plots-") as directory:
                                        paths = generate_audio_plots(samples, rate, directory)
                                        results[key] = {name: path.read_bytes() for name, path in paths.items()}
                            results[key + "_seconds"] = time.perf_counter() - start
                        except Exception as error:
                            st.error(str(error))
                if "transcription" in results:
                    st.subheader("Transcription")
                    st.write(results["transcription"] or "No words recognized.")
                    st.caption(f"End-to-end request: {results['transcription_seconds']:.3f} s; may include fallback/model loading.")
                    if results["transcription"] and st.button("Send transcription to assistant"):
                        st.subheader("Assistant response")
                        respond(results["transcription"])
                for key, title, label in [("emotion", "Voice emotion (experimental)", "emotion"), ("events", "Audio events", "category")]:
                    if key in results:
                        result = results[key]
                        st.subheader(title)
                        if key == "emotion":
                            st.warning(result["notice"])
                        st.metric("Top prediction", result[label])
                        st.write(f"Confidence (model score): {result['confidence']:.1%}")
                        st.dataframe(result["top_predictions"], hide_index=True)
                        st.caption(f"Request latency: {results[key + '_seconds']:.3f} s; may include model loading. Scores are not calibrated certainty.")
                for name, png in results.get("plots", {}).items():
                    st.image(png, caption=name.replace("_", " ").title())
                    st.download_button(f"Download {name}", png, file_name=f"{name}.png", mime="image/png", key=f"download_{name}")
        else:
            st.info("Record in your browser or choose a WAV. Analysis runs only when requested.")
    with memory_tab:
        st.subheader("Private local memory")
        st.caption("UTC timestamps. Legacy rows show import time, not an original creation time.")
        try:
            store = MemoryStore()
            records = store.list()
            if records:
                st.dataframe(records, hide_index=True)
            else:
                st.info("No memories saved yet.")
            text = st.text_input("New memory")
            if st.button("Save memory"):
                store.add(text)
                st.rerun()
            if st.checkbox("Confirm clearing active SQLite memory") and st.button("Clear memory"):
                store.clear()
                st.rerun()
            st.caption("memory.txt is retained as a migration backup; clear removes database rows, not the backup.")
        except Exception as error:
            st.error(f"Memory storage unavailable: {error}")


if __name__ == "__main__":
    main()
