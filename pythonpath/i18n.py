"""gettext bootstrap. Loads the bundled message catalog for the locale
that matches the LibreOffice UI language and exposes `_` for translations.
"""

import gettext

import easymacro as app

APPNAME = "impress-export-all-images"
ID_EXTENSION = "org.ossii.ImpressExportAllImages"

PATH_LOCALES = app.paths.join(app.paths.extension(ID_EXTENSION), "locales")

# app.LANGUAGE looks like "zh-TW" or "en-US"; try the full locale first,
# then the bare language, and finally fall back to the English msgids.
_loc = app.LANGUAGE.replace("-", "_")
_langs = [_loc, _loc.split("_")[0]]

t = gettext.translation(APPNAME, PATH_LOCALES, languages=_langs, fallback=True)
_ = t.gettext
