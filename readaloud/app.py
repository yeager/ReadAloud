"""GTK4/Adwaita Application class for ReadAloud."""

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw, Gio

from readaloud.window import ReadAloudWindow
from readaloud.i18n import _


class ReadAloudApp(Adw.Application):
    """Main application class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_resource_base_path("/se/readaloud")

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = ReadAloudWindow(application=self)
        win.present()

    def do_startup(self):
        Adw.Application.do_startup(self)
        self._setup_actions()

    def _setup_actions(self):
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda *_: self.quit())
        self.add_action(quit_action)
        self.set_accels_for_action("app.quit", ["<Ctrl>q"])

    def _on_about(self, action, param):
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="ReadAloud",
            application_icon="accessories-text-editor",
            version="1.0.0",
            developer_name="ReadAloud Team",
            license_type=Gtk.License.GPL_3_0,
            comments=_("Scan printed text and have it read aloud"),
            website="https://github.com/yeager/ReadAloud",
        )
        about.present()
