# backend/core/config.py
import os
import requests
import torch
from dataclasses import dataclass
from dotenv import load_dotenv
from openai import OpenAI

# --------------------------------------------------------------------
# 1️⃣ Load environment variables
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

# --------------------------------------------------------------------
# 2️⃣ OCR Configuration (macOS / Linux)
# --------------------------------------------------------------------
TESSERACT_PATH = os.getenv("TESSERACT_PATH", "/opt/homebrew/bin/tesseract")
POPPLER_PATH = os.getenv("POPPLER_PATH", "/opt/homebrew/opt/poppler/bin")

# --------------------------------------------------------------------
# 3️⃣ Cloud AI Configuration (A4F Gateway)
# --------------------------------------------------------------------
A4F_API_KEY = os.getenv("A4F_API_KEY", "")
A4F_BASE_URL = os.getenv("A4F_BASE_URL", "https://api.a4f.co/v1")
A4F_MODEL = os.getenv("A4F_MODEL", "provider-5/gpt-4o-mini")

# --------------------------------------------------------------------
# 4️⃣ Local LLM (Ollama) Configuration
# --------------------------------------------------------------------
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "mistral:7b-instruct")

def _is_ollama_available() -> bool:
    """Check if Ollama is running locally."""
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/version", timeout=2)
        return r.status_code == 200
    except Exception:
        return False

USE_OLLAMA = _is_ollama_available()

# --------------------------------------------------------------------
# 5️⃣ LLM Runtime Options
# --------------------------------------------------------------------
@dataclass
class LLMOptions:
    temperature: float = 0.0
    seed: int = 1
    num_ctx: int = 6144
    repeat_penalty: float = 1.0
    top_p: float = 0.9
    top_k: int = 40

LLM_OPTS = LLMOptions()

# --------------------------------------------------------------------
# 6️⃣ Initialize clients
# --------------------------------------------------------------------
a4f_client = None
ollama_client = None

try:
    if USE_OLLAMA:
        print(f"✅ Ollama detected → Using local model: {OLLAMA_MODEL}")
        ollama_client = OpenAI(base_url=f"{OLLAMA_HOST}/v1", api_key="ollama")
    elif A4F_API_KEY:
        print(f"✅ Using A4F Cloud model: {A4F_MODEL}")
        a4f_client = OpenAI(
            api_key=A4F_API_KEY,
            base_url=A4F_BASE_URL,
            default_headers={
                "x-a4f-route": "auto",
                "x-a4f-cache": "read",
                "x-a4f-metadata-project": "AI-CA",
            },
        )
    else:
        print("⚠️ No model client initialized (neither Ollama nor A4F available).")
except Exception as e:
    print(f"⚠️ LLM initialization failed: {e}")

# --------------------------------------------------------------------
# 7️⃣ Hardware Info (MPS / CUDA / CPU)
# --------------------------------------------------------------------
if torch.backends.mps.is_available():
    DEVICE = "mps"
elif torch.cuda.is_available():
    DEVICE = "cuda"
else:
    DEVICE = "cpu"

print(f"🚀 Using device: {DEVICE.upper()}")

# --------------------------------------------------------------------
# 8️⃣ Hugging Face / Tokenizer (optional)
# --------------------------------------------------------------------
HUGGINGFACE_TOKEN = os.getenv("HUGGINGFACE_TOKEN", "")

# --------------------------------------------------------------------
# 9️⃣ Exported Configuration
# --------------------------------------------------------------------
__all__ = [
    "TESSERACT_PATH",
    "POPPLER_PATH",
    "HUGGINGFACE_TOKEN",
    "A4F_API_KEY",
    "A4F_BASE_URL",
    "A4F_MODEL",
    "a4f_client",
    "OLLAMA_HOST",
    "OLLAMA_MODEL",
    "ollama_client",
    "USE_OLLAMA",
    "LLM_OPTS",
    "DEVICE",
]
