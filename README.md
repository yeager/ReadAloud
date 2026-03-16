# ReadAloud

**Skanna tryckt text med kameran och få den uppläst.**

Scan printed text with your camera and have it read aloud — with Swedish voice support.

## Features

- **Camera OCR** — Capture text from printed documents using your webcam
- **Text-to-Speech** — Read scanned text aloud with Swedish or English voices
- **Accessible UI** — Large buttons, high contrast, screen reader friendly (ARASAAC-compatible)
- **Multi-language** — Swedish as primary language, English fallback
- **Editable text** — Review and edit scanned text before reading
- **Multiple TTS backends** — Piper, espeak-ng, macOS `say`, or pyttsx3

## Installation

### System Dependencies

**Ubuntu/Debian:**

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
sudo apt install tesseract-ocr tesseract-ocr-swe
sudo apt install espeak-ng
```

**Fedora:**

```bash
sudo dnf install python3-gobject gtk4 libadwaita
sudo dnf install tesseract tesseract-langpack-swe
sudo dnf install espeak-ng
```

**macOS (Homebrew):**

```bash
brew install pygobject3 gtk4 libadwaita
brew install tesseract tesseract-lang
```

**Optional — Piper TTS (high-quality Swedish voices):**

```bash
pip install piper-tts
# Download Swedish voice model:
# https://github.com/rhasspy/piper/releases
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

### Install the App

```bash
pip install .
```

### Compile Translations

```bash
msgfmt locale/sv/LC_MESSAGES/readaloud.po -o locale/sv/LC_MESSAGES/readaloud.mo
```

## Usage

```bash
readaloud
```

Or run directly:

```bash
python -m readaloud.main
```

1. Click **"Skanna text"** to capture from your camera
2. Review the extracted text in the text area
3. Click **"Läs upp"** to hear the text read aloud
4. Use **Pause/Stop** to control playback

## Project Structure

```
ReadAloud/
├── readaloud/
│   ├── __init__.py      # Package metadata
│   ├── main.py          # Entry point
│   ├── app.py           # Gtk.Application
│   ├── window.py        # Main window UI
│   ├── ocr.py           # OpenCV + Tesseract OCR
│   ├── tts.py           # Text-to-Speech engine
│   └── i18n.py          # Internationalization
├── locale/
│   ├── readaloud.pot    # Translation template
│   └── sv/LC_MESSAGES/
│       └── readaloud.po # Swedish translation
├── data/
│   └── se.readaloud.App.desktop
├── setup.py
├── requirements.txt
└── README.md
```

## Accessibility

ReadAloud is designed for users with visual impairments and dyslexia:

- Large touch targets (minimum 52px height)
- High-contrast text (16px+ font size)
- Full keyboard navigation (Ctrl+Q to quit)
- Screen reader compatible labels and tooltips
- ARASAAC-compatible design principles

## License

GPL-3.0
