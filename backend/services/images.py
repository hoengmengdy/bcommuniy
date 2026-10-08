"""Validate and normalize profile images before storing them in the database."""
import base64
import binascii
import warnings
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from backend.utils.validation import APIError


def profile_image(value):
    try:
        header, encoded = value.split(",", 1)
        if header not in {"data:image/png;base64", "data:image/jpeg;base64",
                          "data:image/webp;base64", "data:image/gif;base64"}:
            raise ValueError()
        raw = base64.b64decode(encoded, validate=True)
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError()
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {"PNG", "JPEG", "WEBP", "GIF"}:
                    raise ValueError()
                if image.width * image.height > 20_000_000:
                    raise ValueError()
                image.load()
                # Re-encoding strips metadata and retains only a small first frame.
                normalized = ImageOps.exif_transpose(image).convert("RGB")
                normalized = ImageOps.fit(normalized, (256, 256))
                output = BytesIO()
                normalized.save(output, format="WEBP", quality=82)
        return "data:image/webp;base64," + base64.b64encode(output.getvalue()).decode("ascii")
    except (ValueError, binascii.Error, OSError, UnidentifiedImageError,
            Image.DecompressionBombWarning, Image.DecompressionBombError) as error:
        raise APIError("Choose a valid JPEG, PNG, WebP or GIF image under 5 MB (maximum 20 megapixels).") from error
