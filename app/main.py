from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="Resume Copilot API",
    description="Tailors resume bullet points to a job description using AI, then compiles to PDF.",
    version="0.1.0",
)

app.include_router(router)
