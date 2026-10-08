import base64
import binascii
from urllib.parse import urlsplit
from email_validator import EmailNotValidError, validate_email
from flask import request


class APIError(Exception):
    def __init__(self, message, status=400):
        self.message, self.status = message, status


def body(allowed):
    if not request.is_json:
        raise APIError("Content-Type must be application/json.", 415)
    data = request.get_json()
    if not isinstance(data, dict):
        raise APIError("The JSON body must be an object.")
    unknown = set(data) - set(allowed)
    if unknown:
        raise APIError("Unknown fields: " + ", ".join(sorted(unknown)))
    return data


def string(value, field, maximum=10000, required=False):
    if value is None and not required:
        return None
    if not isinstance(value, str):
        raise APIError(f"{field} must be a string.")
    value = value.strip()
    if required and not value:
        raise APIError(f"{field} is required.")
    if len(value) > maximum:
        raise APIError(f"{field} must be at most {maximum} characters.")
    return value


def password(value):
    if not isinstance(value, str) or not 8 <= len(value) <= 128:
        raise APIError("Password must contain 8 to 128 characters.")
    return value


def email(value):
    try:
        return validate_email(string(value, "email", 254, True),
                              check_deliverability=False).normalized.lower()
    except EmailNotValidError as error:
        raise APIError("Enter a valid email address.") from error


def strings(value, field):
    if not isinstance(value, list) or len(value) > 30:
        raise APIError(f"{field} must be an array of at most 30 strings.")
    return [string(item, field, 80, True) for item in value]


def choice(value, field, options):
    if value not in options:
        raise APIError(f"{field} must be one of: {', '.join(options)}.")
    return value


def boolean(value, field):
    if not isinstance(value, bool):
        raise APIError(f"{field} must be true or false.")
    return value


def integer(value, field, minimum=1):
    if isinstance(value, str) and value.isdecimal():
        value = int(value)
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise APIError(f"{field} must be an integer >= {minimum}.")
    return value


def url(value, field, image=False):
    value = string(value, field, 7_000_000 if image else 2048)
    if not value:
        return None
    if image and value.startswith(("data:image/png;base64,", "data:image/jpeg;base64,",
                                    "data:image/gif;base64,", "data:image/webp;base64,")):
        header, encoded = value.split(",", 1)
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as error:
            raise APIError(f"{field} contains invalid image data.") from error
        signatures = {"data:image/png;base64": raw.startswith(b"\x89PNG\r\n\x1a\n"),
                      "data:image/jpeg;base64": raw.startswith(b"\xff\xd8\xff"),
                      "data:image/gif;base64": raw.startswith((b"GIF87a", b"GIF89a")),
                      "data:image/webp;base64": raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"}
        if len(raw) > 5 * 1024 * 1024 or not signatures.get(header):
            raise APIError(f"{field} must be a PNG, JPEG, GIF or WebP image under 5 MB.")
        return value
    try:
        parsed = urlsplit(value)
    except ValueError as error:
        raise APIError(f"{field} must be a valid HTTP(S) URL.") from error
    if parsed.scheme not in ("http", "https") or not parsed.netloc or parsed.username:
        raise APIError(f"{field} must be an HTTP(S) URL.")
    return value


def page(query):
    from backend.extensions import db
    number = integer(request.args.get("page", "1"), "page")
    size = min(integer(request.args.get("per_page", "100"), "per_page"), 100)
    result = db.paginate(query, page=number, per_page=size, error_out=False)
    return result.items, {"page": number, "perPage": size, "total": result.total}
