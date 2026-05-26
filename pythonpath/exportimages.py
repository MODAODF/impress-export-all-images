import traceback

import easymacro as app
from easymacro.easyuno import IOStream

from i18n import _

TITLE = "Impress Export All Images"
_IMAGE_SERVICE = "com.sun.star.drawing.GraphicObjectShape"

# Map an image MIME subtype to a sensible file extension.
_EXT_MAP = {
    "jpeg": "jpg",
    "svg+xml": "svg",
    "x-ms-bmp": "bmp",
    "tiff": "tif",
}


def run():
    try:
        _run()
    except Exception:
        app.msgbox(
            _("Export error:\n\n{tb}").format(tb=traceback.format_exc()),
            _(TITLE))


def _run():
    doc = app.active
    if doc is None or doc.type != "impress":
        app.msgbox(_("Please open an Impress presentation first."), _(TITLE))
        return

    images = _collect_images(doc)
    if not images:
        app.msgbox(_("This presentation contains no images."), _(TITLE))
        return

    folder = app.paths.get_dir()
    if not folder:
        return

    count = 0
    for name, shape in images:
        if _save_image(shape, app.paths.join(folder, name)):
            count += 1

    app.msgbox(
        _("Exported {n} image(s) to:\n{path}").format(n=count, path=folder),
        _(TITLE))


def _collect_images(doc):
    """Return [(filename, shape), ...] for every picture across all slides."""
    images = []
    pages = doc.obj.DrawPages
    for s in range(pages.Count):
        page = pages.getByIndex(s)
        n = 0
        for i in range(page.Count):
            shape = page.getByIndex(i)
            if not shape.supportsService(_IMAGE_SERVICE):
                continue
            n += 1
            images.append((f"slide{s + 1}_image{n}.{_ext_of(shape)}", shape))
    return images


def _ext_of(shape):
    try:
        mime = shape.Graphic.MimeType  # e.g. "image/png"
    except Exception:
        mime = ""
    sub = mime.split("/")[-1].lower() if mime else ""
    return _EXT_MAP.get(sub, sub or "png")


def _save_image(shape, path):
    """Write the original, unmodified image bytes to path."""
    try:
        data = IOStream.to_bin(shape.GraphicStream)
        if not data:
            return False
        app.paths.save_bin(path, data)
        return True
    except Exception:
        return False
