"""Environment-driven configuration. Fails fast if USER_ID is missing."""
import os

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://qae-assignment-tau.vercel.app")
USER_ID = os.getenv("USER_ID", "").strip()

# The value shipped in .env.example. Treated as "not configured", so a checkout that
# copied the template without editing it fails with one clear message instead of a
# 401 on every request.
_PLACEHOLDER_USER_ID = "your-candidate-id-here"

if not USER_ID or USER_ID == _PLACEHOLDER_USER_ID:
    raise RuntimeError(
        "USER_ID is not configured. Copy .env.example to .env and replace the placeholder "
        "with your own candidate id."
    )
