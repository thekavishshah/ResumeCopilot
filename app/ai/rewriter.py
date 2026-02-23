import json
import re
from google import genai
from app.config import GEMINI_API_KEY, AI_MODEL, MAX_RETRIES

client = genai.Client(api_key=GEMINI_API_KEY)


def _strip_markdown_json(text: str) -> str:
    """Remove markdown code block markers from JSON response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def _extract_numbers(text: str) -> set[str]:
    """Extract all numbers from text, including decimals and percentages."""
    return set(re.findall(r"\d+\.?\d*%?", text))


def validate_bullet(original: str, rewritten: str) -> tuple[bool, str]:
    """
    Validate that a rewritten bullet meets constraints.
    Returns (True, "") if valid, or (False, reason) if not.
    """
    len_diff = abs(len(rewritten) - len(original))
    if len_diff > 5:
        return False, f"Length difference is {len_diff} chars (max 5 allowed)"

    missing = _extract_numbers(original) - _extract_numbers(rewritten)
    if missing:
        return False, f"Missing numbers: {missing}"

    return True, ""


def _call_gemini(prompt: str) -> list[str]:
    """Call Gemini and parse the JSON array response."""
    response = client.models.generate_content(model=AI_MODEL, contents=prompt)
    text = _strip_markdown_json(response.text)
    result = json.loads(text)
    if not isinstance(result, list):
        raise ValueError("Response is not a JSON array")
    return result


def rewrite_bullets(bullets: list[str], quals: list[str]) -> list[str]:
    """
    Batch rewrite all bullets in one Gemini call.
    """
    prompt = f"""You are a resume optimization AI. Rewrite these resume bullet points to better align with the job qualifications.

STRICT RULES:
1. Stay within ±5 characters of the original bullet length
2. Preserve ALL numbers and metrics EXACTLY as they appear
3. Return ONLY the bullet text - NO LaTeX commands, NO bullet markers (\\item, -, *)
4. If a bullet has no overlap with the qualifications, return it UNCHANGED
5. Return a JSON array with the rewritten bullets in the SAME ORDER

Job Qualifications:
{json.dumps(quals)}

Original Bullets:
{json.dumps(bullets)}

Return ONLY a JSON array of rewritten bullets, nothing else."""

    rewritten = _call_gemini(prompt)

    if len(rewritten) != len(bullets):
        raise ValueError(
            f"Gemini returned {len(rewritten)} bullets, expected {len(bullets)}"
        )

    return rewritten


def rewrite_single_with_retry(bullet: str, quals: list[str]) -> str:
    """
    Rewrite a single bullet with validation + retry. Falls back to original.
    """
    for attempt in range(MAX_RETRIES):
        try:
            rewritten = rewrite_bullets([bullet], quals)[0]
            is_valid, reason = validate_bullet(bullet, rewritten)

            if is_valid:
                return rewritten

            print(f"  Validation failed (attempt {attempt + 1}/{MAX_RETRIES}): {reason}")

            if attempt < MAX_RETRIES - 1:
                retry_prompt = f"""Previous rewrite failed validation: {reason}

Original bullet: {bullet}
Your rewrite: {rewritten}

Please rewrite again, fixing the issue. Return ONLY a JSON array with one bullet."""
                result = _call_gemini(retry_prompt)
                if result:
                    rewritten = result[0]
                    is_valid, _ = validate_bullet(bullet, rewritten)
                    if is_valid:
                        return rewritten

        except Exception as e:
            print(f"  Error on attempt {attempt + 1}/{MAX_RETRIES}: {e}")
            if attempt == MAX_RETRIES - 1:
                print("  All retries exhausted, returning original.")
                return bullet

    return bullet


def rewrite_all(bullets: list[str], quals: list[str]) -> list[str]:
    """
    Rewrite all bullets. Tries batch first; falls back to per-bullet retry
    for any that fail validation.
    """
    try:
        rewritten_bullets = rewrite_bullets(bullets, quals)

        final: list[str] = []
        for i, (original, rewritten) in enumerate(zip(bullets, rewritten_bullets)):
            is_valid, reason = validate_bullet(original, rewritten)
            if is_valid:
                final.append(rewritten)
            else:
                print(f"\nBullet {i + 1} failed validation: {reason}. Retrying...")
                final.append(rewrite_single_with_retry(original, quals))

        return final

    except Exception as e:
        print(f"Batch rewrite failed: {e}\nFalling back to per-bullet processing...")
        return [rewrite_single_with_retry(b, quals) for b in bullets]
