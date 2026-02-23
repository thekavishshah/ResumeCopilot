import subprocess
import tempfile
from pathlib import Path


class CompilationError(Exception):
    pass


def compile_pdf(tex_source: str) -> bytes:
    """
    Compile a LaTeX string to PDF and return the PDF bytes.
    Runs pdflatex twice for stable output. Cleans up temp files after.

    Raises:
        CompilationError: if pdflatex exits non-zero.
        FileNotFoundError: if pdflatex is not on PATH.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        tex_file = tmp / "resume.tex"
        tex_file.write_text(tex_source, encoding="utf-8")

        cmd = [
            "pdflatex",
            "-interaction=nonstopmode",
            "-output-directory", str(tmp),
            str(tex_file),
        ]

        for pass_num in range(2):
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=tmpdir)
            if result.returncode != 0:
                log_path = tmp / "resume.log"
                log_tail = ""
                if log_path.exists():
                    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
                    log_tail = "\n".join(lines[-40:])
                raise CompilationError(
                    f"pdflatex failed on pass {pass_num + 1} "
                    f"(exit {result.returncode}):\n{log_tail}"
                )

        pdf_path = tmp / "resume.pdf"
        if not pdf_path.exists():
            raise CompilationError("pdflatex succeeded but resume.pdf not found.")

        return pdf_path.read_bytes()
