# Resume Copilot API

A FastAPI-based service that automatically tailors resume bullet points to job descriptions using AI, then compiles them into a professionally formatted PDF.

## Overview

Resume Copilot extracts bullet points from a LaTeX resume template, rewrites them using Google's Gemini AI to match specific job qualifications, and generates a tailored PDF resume. This enables rapid customization of resumes for different job applications while maintaining professional LaTeX formatting.

## Features

- **AI-Powered Rewriting**: Uses Google Gemini to intelligently tailor resume bullets to job requirements
- **LaTeX Integration**: Parses, modifies, and compiles LaTeX resume templates
- **Automatic Formatting**: Applies bold formatting to key technical terms and action verbs
- **RESTful API**: Clean HTTP endpoints for integration with frontend applications
- **Validation & Retry**: Built-in validation ensures AI-generated content meets quality standards

## Architecture

```
┌─────────────────┐
│  Client/Chrome  │
│   Extension     │
└────────┬────────┘
         │ POST /tailor
         │ {quals: [...]}
         ▼
┌─────────────────────────────────────┐
│         Resume Copilot API          │
├─────────────────────────────────────┤
│  1. Extract bullets from template   │
│  2. Send to Gemini for rewriting    │
│  3. Apply bold formatting           │
│  4. Inject into LaTeX template      │
│  5. Compile to PDF                  │
└────────┬────────────────────────────┘
         │
         ▼
    PDF Resume
```

## Project Structure

```
bullet_rewriter/
├── app/
│   ├── ai/
│   │   └── rewriter.py         # Gemini API integration & rewriting logic
│   ├── latex/
│   │   ├── parser.py           # Extract bullets from LaTeX template
│   │   ├── injector.py         # Inject rewritten bullets back
│   │   ├── bold.py             # Apply formatting to technical terms
│   │   └── compiler.py         # Compile LaTeX to PDF
│   ├── scraper/                # Job description scraping utilities
│   ├── config.py               # Configuration management
│   ├── models.py               # Pydantic data models
│   ├── routes.py               # API endpoints
│   └── main.py                 # FastAPI application
├── templates/
│   └── resume_marked.tex       # LaTeX template with <<BULLET_*>> markers
├── tests/                      # Test files
├── .env.example                # Environment variable template
└── requirements.txt            # Python dependencies
```

## Setup

### Prerequisites

- Python 3.10+
- LaTeX distribution (e.g., TeX Live, MiKTeX)
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bullet_rewriter
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your Gemini API key
```

### Environment Variables

- `GEMINI_API_KEY` (required): Your Google Gemini API key
- `AI_MODEL` (optional): AI model to use (default: `gemini-2.5-flash`)
- `MAX_RETRIES` (optional): Maximum retry attempts for AI requests (default: 3)
- `TEMPLATE_PATH` (optional): Custom path to LaTeX template

## Usage

### Starting the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### API Endpoints

#### GET /bullets

Returns all bullet points extracted from the resume template.

**Response:**
```json
{
  "bullets": {
    "BULLET_1": "Original bullet point text",
    "BULLET_2": "Another bullet point"
  }
}
```

#### POST /generate-pdf

Generates a PDF with provided bullet points (bypasses AI, useful for testing).

**Request:**
```json
{
  "bullets": {
    "BULLET_1": "Custom bullet text",
    "BULLET_2": "Another custom bullet"
  }
}
```

**Response:** PDF file download

#### POST /tailor

Full pipeline: takes job qualifications and returns a tailored resume PDF.

**Request:**
```json
{
  "quals": [
    "5+ years of Python experience",
    "Experience with FastAPI and REST APIs",
    "Strong understanding of LaTeX"
  ]
}
```

**Response:** PDF file download

### Example Usage

```python
import requests

# Tailor resume to job requirements
response = requests.post(
    "http://localhost:8000/tailor",
    json={
        "quals": [
            "Experience with Python and FastAPI",
            "Knowledge of AI/ML APIs",
            "LaTeX document processing"
        ]
    }
)

# Save the PDF
with open("tailored_resume.pdf", "wb") as f:
    f.write(response.content)
```

## LaTeX Template Format

The LaTeX template should include special markers where bullet points should be inserted:

```latex
\begin{itemize}
    \item <<BULLET_1>>
    \item <<BULLET_2>>
    \item <<BULLET_3>>
\end{itemize}
```

The API will extract the original text at these markers, rewrite them using AI, and inject the tailored versions back.

## Development

### Running Tests

```bash
pytest tests/
```

### API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
