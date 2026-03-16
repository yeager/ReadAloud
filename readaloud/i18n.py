"""Internationalization support using gettext."""

import gettext
import locale
import os

DOMAIN = "readaloud"
LOCALE_DIR = os.path.join(os.path.dirname(__file__), "..", "locale")

# Try to set Swedish locale, fall back to system default
for loc in ("sv_SE.UTF-8", "sv_SE", ""):
    try:
        locale.setlocale(locale.LC_ALL, loc)
        break
    except locale.Error:
        continue

_translation = gettext.translation(DOMAIN, LOCALE_DIR, fallback=True)
_ = _translation.gettext
ngettext = _translation.ngettext
