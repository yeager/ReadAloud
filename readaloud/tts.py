"""Text-to-Speech module with Swedish voice support."""

import os
import shutil
import subprocess
import tempfile
import threading

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


class TTSEngine:
    """Text-to-Speech engine with support for multiple backends."""

    def __init__(self):
        self._process = None
        self._thread = None
        self._paused = False
        self._gst_pipeline = None
        self._backend = self._detect_backend()
        
        # Initialize GStreamer
        Gst.init(None)

    def _detect_backend(self):
        """Detect available TTS backend."""
        # Check for piper binary
        if shutil.which("piper"):
            return "piper"
        # Check for piper via pip
        try:
            import piper
            return "piper-pip"
        except ImportError:
            pass
        # espeak-ng has Swedish support
        if shutil.which("espeak-ng"):
            return "espeak-ng"
        # macOS say command
        if shutil.which("say"):
            return "say"
        # pyttsx3 as last resort
        try:
            import pyttsx3
            return "pyttsx3"
        except ImportError:
            pass
        return None

    @property
    def backend_name(self):
        return self._backend or "none"

    @property
    def is_speaking(self):
        return self._process is not None and self._process.poll() is None

    def speak(self, text, voice="swedish", on_done=None):
        """Speak text asynchronously.

        Args:
            text: Text to speak.
            voice: Voice hint - 'swedish' or 'english'.
            on_done: Callback when speech finishes.
        """
        self.stop()
        self._paused = False

        def _run():
            try:
                self._speak_sync(text, voice)
            finally:
                self._process = None
                if on_done:
                    on_done()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def _speak_sync(self, text, voice):
        """Synchronous speech synthesis."""
        if self._backend == "piper":
            self._piper_speak(text, voice)
        elif self._backend == "piper-pip":
            self._piper_pip_speak(text, voice)
        elif self._backend == "espeak-ng":
            lang = "sv" if voice == "swedish" else "en"
            self._process = subprocess.Popen(
                ["espeak-ng", "-v", lang, "-s", "150", text],
                stderr=subprocess.DEVNULL,
            )
            self._process.wait()

        elif self._backend == "say":
            # macOS say command
            voice_name = "Alva" if voice == "swedish" else "Samantha"
            self._process = subprocess.Popen(
                ["say", "-v", voice_name, text],
                stderr=subprocess.DEVNULL,
            )
            self._process.wait()

        elif self._backend == "pyttsx3":
            import pyttsx3
            engine = pyttsx3.init()
            voices = engine.getProperty("voices")
            for v in voices:
                if "swedish" in v.name.lower() or "sv" in v.id.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.setProperty("rate", 150)
            engine.say(text)
            engine.runAndWait()

    def _piper_speak(self, text, voice):
        """Speak using Piper binary with GStreamer playback."""
        # Try to find Swedish Alma voice first
        if voice == "swedish":
            model_paths = [
                "sv_SE-nst-medium",
                "/opt/homebrew/share/piper-voices/sv_SE-nst-medium.onnx",
                os.path.expanduser("~/.local/share/piper-voices/sv_SE-nst-medium.onnx"),
            ]
        else:
            model_paths = ["en_US-lessac-medium"]
        
        model = model_paths[0]  # Default to first option
        
        # Generate WAV data with Piper
        self._process = subprocess.Popen(
            ["piper", "--model", model, "--output_file", "-"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        
        wav_data, _ = self._process.communicate(input=text.encode("utf-8"))
        
        # Play with GStreamer
        if wav_data:
            self._play_with_gstreamer(wav_data)
    
    def _piper_pip_speak(self, text, voice):
        """Speak using Piper Python package."""
        try:
            import piper
            import numpy as np
            
            # Try to load Swedish voice
            if voice == "swedish":
                # Look for downloaded Swedish voice
                voice_files = [
                    "sv_SE-nst-medium.onnx",
                    os.path.expanduser("~/.local/share/piper-voices/sv_SE-nst-medium.onnx"),
                ]
                voice_file = None
                for vf in voice_files:
                    if os.path.exists(vf):
                        voice_file = vf
                        break
                
                if not voice_file:
                    # Fallback to espeak for Swedish
                    self._speak_espeak(text, "sv")
                    return
            else:
                voice_file = "en_US-lessac-medium.onnx"  # Default English
            
            # Synthesize speech
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                with piper.PiperVoice.load(voice_file) as voice:
                    voice.synthesize(text, wav_file)
                wav_file.flush()
                
                # Play with GStreamer
                with open(wav_file.name, 'rb') as f:
                    wav_data = f.read()
                self._play_with_gstreamer(wav_data)
                
                os.unlink(wav_file.name)
                
        except Exception as e:
            # Fallback to espeak
            lang = "sv" if voice == "swedish" else "en"
            self._speak_espeak(text, lang)
    
    def _play_with_gstreamer(self, wav_data):
        """Play WAV data using GStreamer."""
        try:
            # Create a simple playback pipeline
            pipeline_desc = "fdsrc ! wavparse ! audioconvert ! audioresample ! autoaudiosink"
            self._gst_pipeline = Gst.parse_launch(pipeline_desc)
            
            # Get the fdsrc element and feed it data
            fdsrc = self._gst_pipeline.get_by_name("fdsrc0")
            if not fdsrc:
                # Fallback - write to temp file and use filesrc
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp.write(wav_data)
                    tmp.flush()
                    
                pipeline_desc = f"filesrc location={tmp.name} ! wavparse ! audioconvert ! audioresample ! autoaudiosink"
                self._gst_pipeline = Gst.parse_launch(pipeline_desc)
            
            # Play the audio
            self._gst_pipeline.set_state(Gst.State.PLAYING)
            
            # Wait for completion
            bus = self._gst_pipeline.get_bus()
            while True:
                message = bus.timed_pop_filtered(Gst.CLOCK_TIME_NONE, Gst.MessageType.EOS | Gst.MessageType.ERROR)
                if message:
                    if message.type == Gst.MessageType.ERROR:
                        break
                    elif message.type == Gst.MessageType.EOS:
                        break
            
            self._gst_pipeline.set_state(Gst.State.NULL)
            
        except Exception:
            # Ultimate fallback - use aplay if available
            if shutil.which("aplay"):
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                    tmp.write(wav_data)
                    tmp.flush()
                    subprocess.run(["aplay", tmp.name], stderr=subprocess.DEVNULL)
                    os.unlink(tmp.name)
    
    def _speak_espeak(self, text, lang):
        """Fallback to espeak-ng."""
        self._process = subprocess.Popen(
            ["espeak-ng", "-v", lang, "-s", "150", text],
            stderr=subprocess.DEVNULL,
        )
        self._process.wait()

    def stop(self):
        """Stop current speech."""
        self._paused = False
        if self._gst_pipeline:
            self._gst_pipeline.set_state(Gst.State.NULL)
            self._gst_pipeline = None
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def pause(self):
        """Pause speech."""
        import signal
        if self._gst_pipeline:
            self._gst_pipeline.set_state(Gst.State.PAUSED)
            self._paused = True
        elif self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGSTOP)
            self._paused = True

    def resume(self):
        """Resume paused speech."""
        import signal
        if self._gst_pipeline and self._paused:
            self._gst_pipeline.set_state(Gst.State.PLAYING)
            self._paused = False
        elif self._process and self._paused:
            self._process.send_signal(signal.SIGCONT)
            self._paused = False
