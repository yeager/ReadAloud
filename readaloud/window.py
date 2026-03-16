"""Main application window for ReadAloud."""

import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, GLib, Gdk, GdkPixbuf

from readaloud.i18n import _
from readaloud.ocr import scan_and_extract
from readaloud.tts import TTSEngine


class ReadAloudWindow(Adw.ApplicationWindow):
    """Main window with scan, display, and playback controls."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("ReadAloud")
        self.set_default_size(600, 700)

        self._tts = TTSEngine()
        self._scanned_text = ""

        self._build_ui()
        self._update_tts_status()

    def _build_ui(self):
        """Build the complete UI."""
        # Main layout
        toolbar_view = Adw.ToolbarView()
        self.set_content(toolbar_view)

        # Header bar
        header = Adw.HeaderBar()
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu = Gio_menu()
        menu.append(_("About"), "app.about")
        menu.append(_("Quit"), "app.quit")
        menu_button.set_menu_model(menu)
        header.pack_end(menu_button)
        toolbar_view.add_top_bar(header)

        # Content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        content_box.set_margin_top(12)
        content_box.set_margin_bottom(12)
        content_box.set_margin_start(12)
        content_box.set_margin_end(12)

        # Status bar for TTS backend
        self._status_label = Gtk.Label()
        self._status_label.add_css_class("dim-label")
        self._status_label.set_halign(Gtk.Align.START)
        content_box.append(self._status_label)

        # Camera preview area
        self._preview_frame = Gtk.Frame()
        self._preview_frame.set_size_request(-1, 200)
        self._preview_picture = Gtk.Picture()
        self._preview_picture.set_content_fit(Gtk.ContentFit.CONTAIN)
        placeholder_label = Gtk.Label(label=_("Camera preview will appear here"))
        placeholder_label.add_css_class("dim-label")
        self._preview_frame.set_child(placeholder_label)
        content_box.append(self._preview_frame)

        # Scan button - large and accessible
        self._scan_button = Gtk.Button(label=_("Scan Text"))
        self._scan_button.set_icon_name("camera-photo-symbolic")
        self._scan_button.add_css_class("suggested-action")
        self._scan_button.add_css_class("pill")
        self._scan_button.set_size_request(-1, 56)
        self._scan_button.set_tooltip_text(_("Take a photo and extract text"))
        self._scan_button.connect("clicked", self._on_scan_clicked)
        content_box.append(self._scan_button)

        # Scanned text display
        text_label = Gtk.Label(label=_("Scanned Text"))
        text_label.add_css_class("heading")
        text_label.set_halign(Gtk.Align.START)
        content_box.append(text_label)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_min_content_height(150)

        self._text_view = Gtk.TextView()
        self._text_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self._text_view.set_editable(True)
        self._text_view.set_left_margin(8)
        self._text_view.set_right_margin(8)
        self._text_view.set_top_margin(8)
        self._text_view.set_bottom_margin(8)
        # Accessible font size
        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("textview { font-size: 16px; }")
        self._text_view.get_style_context().add_provider(
            css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        scrolled.set_child(self._text_view)
        content_box.append(scrolled)

        # Language selector
        lang_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lang_label = Gtk.Label(label=_("Language:"))
        lang_box.append(lang_label)

        self._lang_dropdown = Gtk.DropDown.new_from_strings(
            [_("Swedish"), _("English"), _("Swedish + English")]
        )
        self._lang_dropdown.set_selected(2)  # Default: swe+eng
        self._lang_dropdown.set_tooltip_text(_("Select OCR and speech language"))
        lang_box.append(self._lang_dropdown)
        content_box.append(lang_box)

        # Playback controls - large buttons for accessibility
        controls_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        controls_box.set_halign(Gtk.Align.CENTER)
        controls_box.set_margin_top(8)

        self._play_button = Gtk.Button(label=_("Read Aloud"))
        self._play_button.set_icon_name("media-playback-start-symbolic")
        self._play_button.add_css_class("suggested-action")
        self._play_button.add_css_class("pill")
        self._play_button.set_size_request(160, 52)
        self._play_button.set_tooltip_text(_("Start reading the text aloud"))
        self._play_button.connect("clicked", self._on_play_clicked)
        self._play_button.set_sensitive(False)
        controls_box.append(self._play_button)

        self._pause_button = Gtk.Button(label=_("Pause"))
        self._pause_button.set_icon_name("media-playback-pause-symbolic")
        self._pause_button.add_css_class("pill")
        self._pause_button.set_size_request(120, 52)
        self._pause_button.set_tooltip_text(_("Pause reading"))
        self._pause_button.connect("clicked", self._on_pause_clicked)
        self._pause_button.set_sensitive(False)
        controls_box.append(self._pause_button)

        self._stop_button = Gtk.Button(label=_("Stop"))
        self._stop_button.set_icon_name("media-playback-stop-symbolic")
        self._stop_button.add_css_class("destructive-action")
        self._stop_button.add_css_class("pill")
        self._stop_button.set_size_request(120, 52)
        self._stop_button.set_tooltip_text(_("Stop reading"))
        self._stop_button.connect("clicked", self._on_stop_clicked)
        self._stop_button.set_sensitive(False)
        controls_box.append(self._stop_button)

        content_box.append(controls_box)

        # Apply high-contrast accessible styling
        self._apply_accessible_css()

        toolbar_view.set_content(content_box)

    def _apply_accessible_css(self):
        """Apply CSS for accessibility (high contrast, large targets)."""
        css = b"""
        .scan-button {
            font-size: 18px;
            font-weight: bold;
        }
        window {
            font-size: 14px;
        }
        """
        provider = Gtk.CssProvider()
        provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    def _update_tts_status(self):
        """Show which TTS backend is active."""
        backend = self._tts.backend_name
        self._status_label.set_text(_("TTS engine: %s") % backend)

    def _get_ocr_lang(self):
        """Get Tesseract language code from dropdown selection."""
        idx = self._lang_dropdown.get_selected()
        return ["swe", "eng", "swe+eng"][idx]

    def _get_tts_voice(self):
        """Get TTS voice hint from dropdown selection."""
        idx = self._lang_dropdown.get_selected()
        return ["swedish", "english", "swedish"][idx]

    def _on_scan_clicked(self, button):
        """Handle scan button click."""
        self._scan_button.set_sensitive(False)
        self._scan_button.set_label(_("Scanning..."))

        lang = self._get_ocr_lang()

        def do_scan():
            frame, text = scan_and_extract(lang=lang)
            GLib.idle_add(self._on_scan_done, frame, text)

        threading.Thread(target=do_scan, daemon=True).start()

    def _on_scan_done(self, frame, text):
        """Handle scan completion on main thread."""
        self._scan_button.set_sensitive(True)
        self._scan_button.set_label(_("Scan Text"))

        if frame is None:
            self._show_error(_("Could not access camera. Check permissions."))
            return

        # Show preview
        self._show_preview(frame)

        if text:
            self._scanned_text = text
            buf = self._text_view.get_buffer()
            buf.set_text(text)
            self._play_button.set_sensitive(True)
        else:
            self._show_error(_("No text detected. Try again with better lighting."))

    def _show_preview(self, frame):
        """Display captured frame in the preview area."""
        import cv2
        # Convert BGR to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, c = rgb.shape
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            rgb.tobytes(), GdkPixbuf.Colorspace.RGB, False, 8, w, h, w * c
        )
        texture = Gdk.Texture.new_for_pixbuf(pixbuf)
        self._preview_picture.set_paintable(texture)
        self._preview_frame.set_child(self._preview_picture)

    def _on_play_clicked(self, button):
        """Start TTS playback."""
        buf = self._text_view.get_buffer()
        start, end = buf.get_bounds()
        text = buf.get_text(start, end, False)
        if not text.strip():
            return

        voice = self._get_tts_voice()
        self._play_button.set_sensitive(False)
        self._pause_button.set_sensitive(True)
        self._stop_button.set_sensitive(True)

        def on_done():
            GLib.idle_add(self._on_speech_done)

        self._tts.speak(text, voice=voice, on_done=on_done)

    def _on_speech_done(self):
        """Reset controls after speech finishes."""
        self._play_button.set_sensitive(True)
        self._pause_button.set_sensitive(False)
        self._stop_button.set_sensitive(False)

    def _on_pause_clicked(self, button):
        """Toggle pause/resume."""
        if self._tts._paused:
            self._tts.resume()
            self._pause_button.set_label(_("Pause"))
            self._pause_button.set_icon_name("media-playback-pause-symbolic")
        else:
            self._tts.pause()
            self._pause_button.set_label(_("Resume"))
            self._pause_button.set_icon_name("media-playback-start-symbolic")

    def _on_stop_clicked(self, button):
        """Stop TTS."""
        self._tts.stop()
        self._on_speech_done()

    def _show_error(self, message):
        """Show error in an accessible dialog."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading=_("Error"),
            body=message,
        )
        dialog.add_response("ok", _("OK"))
        dialog.present()


def Gio_menu():
    """Create a Gio.Menu (helper to avoid import in class body)."""
    from gi.repository import Gio
    return Gio.Menu()
