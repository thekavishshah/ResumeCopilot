from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Template
TEMPLATE_PATH = Path(
    os.getenv(
        "TEMPLATE_PATH",
        str(Path(__file__).parent.parent / "templates" / "resume_marked.tex"),
    )
)

# Gemini AI
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
