from pathlib import Path
from PIL import Image
import pillow_heif

pillow_heif.register_heif_opener()

SUPPORTED_INPUT_EXTENSIONS = {".heif", ".heic", ".jpg", ".jpeg", ".png", ".pdf"}
SUPPORTED_OUTPUT_FORMATS = ["HEIF", "JPEG", "PNG", "PDF"]

# Maps output format name to Pillow save format string and file extension
FORMAT_MAP = {
    "HEIF": ("HEIF", ".heic"),
    "JPEG": ("JPEG", ".jpg"),
    "PNG":  ("PNG",  ".png"),
    "PDF":  ("PDF",  ".pdf"),
}


def convert_image(
    src_path: str,
    dst_dir: str,
    output_format: str,
    quality: int = 85,
    pil_image: Image.Image | None = None,
    stem_override: str | None = None,
    rotation: int = 0,
) -> str:
    """Convert a single image file to the target format. Returns the output path.

    pil_image can be passed directly (used by pdf_handler for pre-rendered pages).
    stem_override renames the output file stem (used for PDF page numbering).
    """
    fmt_str, ext = FORMAT_MAP[output_format]
    src = Path(src_path)
    stem = stem_override if stem_override else src.stem
    dst = Path(dst_dir) / (stem + ext)

    if pil_image is not None:
        img = pil_image
    else:
        img = Image.open(src_path)

    if rotation != 0:
        img = img.rotate(rotation, expand=True)

    # HEIF requires RGB or RGBA; PDF writer requires RGB
    if fmt_str in ("HEIF", "PDF") and img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    elif fmt_str == "JPEG" and img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    save_kwargs: dict = {}
    if fmt_str == "JPEG":
        save_kwargs["quality"] = quality
        save_kwargs["optimize"] = True
    elif fmt_str == "HEIF":
        save_kwargs["quality"] = quality
    elif fmt_str == "PNG":
        # quality slider maps 0-100 → compression 9-0 (inverted)
        save_kwargs["compress_level"] = max(0, min(9, 9 - round(quality / 11)))

    img.save(str(dst), fmt_str, **save_kwargs)
    return str(dst)
