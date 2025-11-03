import os
from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------------------------
# 1️ Load environment variables
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

# --------------------------------------------------------------------
# 2️ Hugging Face Token
# --------------------------------------------------------------------
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")

# --------------------------------------------------------------------
# 3️ OCR Configuration (macOS paths)
# --------------------------------------------------------------------
# Default paths for Homebrew installations
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "/opt/homebrew/bin/tesseract")
POPPLER_PATH = os.getenv("POPPLER_PATH", "/opt/homebrew/opt/poppler/bin")

# --------------------------------------------------------------------
# 4️ A4F Unified AI Gateway Configuration
# --------------------------------------------------------------------
A4F_API_KEY = os.getenv("A4F_API_KEY")
A4F_BASE_URL = os.getenv("A4F_BASE_URL", "https://api.a4f.co/v1")
A4F_MODEL = os.getenv("A4F_MODEL", "provider-5/gpt-4o-mini")

# Initialize A4F-compatible OpenAI client
a4f_client = None
try:
    a4f_client = OpenAI(
        api_key=A4F_API_KEY,
        base_url=A4F_BASE_URL,
        default_headers={
            "x-a4f-route": "auto",         # Automatically choose fastest/available model
            "x-a4f-cache": "read",         # Cache repeated requests
            "x-a4f-metadata-project": "AI-CA",
        },
    )
    print(f"✅ A4F Client initialized (model={A4F_MODEL})")
except Exception as e:
    print(f"⚠️ Failed to initialize A4F client: {e}")

# --------------------------------------------------------------------
# 5️ Exported Config
# --------------------------------------------------------------------
__all__ = [
    "HUGGINGFACE_TOKEN",
    "TESSERACT_PATH",
    "POPPLER_PATH",
    "A4F_API_KEY",
    "A4F_BASE_URL",
    "A4F_MODEL",
    "a4f_client",
]
