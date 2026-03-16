"""Text-to-Speech module using Piper TTS."""

import os
import shutil
import subprocess
import tempfile
import threading

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


class TTSEngine:
    """Piper TTS engine with Swedish Alma and English voices."""

    VOICES = {
        "sv_female": "sv_SE-nst-medium",       # Alma
        "en_female": "en_US-lessac-medium",
        "en_male": "en_US-ryan-medium",
    }

    def __init__(self):
        self._process = None
        self._thread = None
        self._piper_bin = self._find_piper()
        Gst.init(None)

    def _find_piper(self):
        for path in [shutil.which("piper"), "/usr/bin/piper",
                     "/usr/local/bin/piper", "/opt/homebrew/bin/piper"]:
            if path and os.path.isfile(path):
                return path
        return None

    @property
    def backend_name(self):
        return "piper" if self._piper_bin else "none"

    @property
    def is_available(self):
        return self._piper_bin is not None

    @property
    def is_speaking(self):
        return self._process is not None and self._process.poll() is None

    def get_voice(self, voice="swedish"):
        if voice == "swedish":
            return self.VOICES["sv_female"]
        elif voice == "english_male":
            return self.VOICES["en_male"]
        return self.VOICES["en_female"]

    def speak(self, text, voice="swedish", on_done=None):
        self.stop()
        if not self._piper_bin or not text.strip():
            if on_done:
                on_done()
            return

        model = self.get_voice(voice)

        def _run():
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    wav_path = f.name

                self._process = subprocess.Popen(
                    [self._piper_bin, "--model", model, "--output_file", wav_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self._process.communicate(input=text.encode("utf-8"))

                if os.path.exists(wav_path) and os.path.getsize(wav_path) > 44:
                    for cmd in [["aplay"], ["paplay"], ["pw-play"],
                                ["ffplay", "-nodisp", "-autoexit"]]:
                        if shutil.which(cmd[0]):
                            self._process = subprocess.Popen(
                                cmd + [wav_path],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            self._process.wait()
                            break

                try:
                    os.unlink(wav_path)
                except OSError:
                    pass
            except (OSError, subprocess.SubprocessError):
                pass
            finally:
                self._process = None
                if on_done:
                    on_done()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._process and self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self._process.kill()
        self._process = None

    def pause(self):
        import signal
        if self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGSTOP)

    def resume(self):
        import signal
        if self._process:
            self._process.send_signal(signal.SIGCONT)
