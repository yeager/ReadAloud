"""Text-to-Speech module with Swedish voice support."""

import shutil
import subprocess
import threading


class TTSEngine:
    """Text-to-Speech engine with support for multiple backends."""

    def __init__(self):
        self._process = None
        self._thread = None
        self._paused = False
        self._backend = self._detect_backend()

    def _detect_backend(self):
        """Detect available TTS backend."""
        # Prefer Piper for high-quality Swedish voices
        if shutil.which("piper"):
            return "piper"
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
            # Piper with Swedish model
            model = "sv_SE-nst-medium" if voice == "swedish" else "en_US-lessac-medium"
            self._process = subprocess.Popen(
                ["piper", "--model", model, "--output-raw"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            aplay = subprocess.Popen(
                ["aplay", "-r", "22050", "-f", "S16_LE", "-t", "raw", "-"],
                stdin=self._process.stdout,
                stderr=subprocess.DEVNULL,
            )
            self._process.stdin.write(text.encode("utf-8"))
            self._process.stdin.close()
            aplay.wait()

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

    def stop(self):
        """Stop current speech."""
        self._paused = False
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def pause(self):
        """Pause speech (by sending SIGSTOP on Linux/macOS)."""
        import signal
        if self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGSTOP)
            self._paused = True

    def resume(self):
        """Resume paused speech."""
        import signal
        if self._process and self._paused:
            self._process.send_signal(signal.SIGCONT)
            self._paused = False
