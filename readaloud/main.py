"""Main entry point for the ReadAloud application."""

import sys
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from readaloud import __app_id__
from readaloud.app import ReadAloudApp


def main():
    app = ReadAloudApp(application_id=__app_id__)
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
