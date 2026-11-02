"""One-time setup for chat notifications: create a VAPID key and store it on Vercel.

Run from the project root:  backend\\venv\\Scripts\\python.exe backend\\setup_push_key.py
The key goes straight to Vercel as a sensitive variable and is never printed or saved locally.
Running it again does nothing if the key exists (a new key would switch off everyone's notifications).
"""
import base64
import shutil
import subprocess
import sys

from cryptography.hazmat.primitives.asymmetric import ec

vercel = shutil.which("vercel") or shutil.which("vercel.cmd")
if not vercel:
    sys.exit("The Vercel CLI was not found. Install it with: npm i -g vercel")

existing = subprocess.run([vercel, "env", "ls", "production"], capture_output=True, text=True)
if "VAPID_PRIVATE_KEY" in existing.stdout:
    sys.exit("VAPID_PRIVATE_KEY is already set on Vercel. Nothing to do.")

private = ec.generate_private_key(ec.SECP256R1()).private_numbers().private_value.to_bytes(32, "big")
key = base64.urlsafe_b64encode(private).rstrip(b"=").decode()
result = subprocess.run([vercel, "env", "add", "VAPID_PRIVATE_KEY", "production", "--sensitive"],
                        input=key, text=True, capture_output=True)
if result.returncode != 0:
    sys.exit("Vercel refused the key:\n" + (result.stderr or result.stdout))
print("Done! VAPID_PRIVATE_KEY was added to Vercel. Tell Claude 'done' so it can redeploy.")
