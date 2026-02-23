import os
import re
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


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
    return set(re.findall(r'\d+\.?\d*%?', text))


def validate_bullet(original: str, rewritten: str) -> tuple[bool, str]:
    """
    Validate that a rewritten bullet meets constraints.

    Returns:
        (True, "") if valid
        (False, reason) if invalid
    """
    len_diff = abs(len(rewritten) - len(original))
    if len_diff > 5:
        return False, f"Length difference is {len_diff} chars (max 5 allowed)"

    original_numbers = _extract_numbers(original)
    rewritten_numbers = _extract_numbers(rewritten)

    missing_numbers = original_numbers - rewritten_numbers
    if missing_numbers:
        return False, f"Missing numbers: {missing_numbers}"

    return True, ""


def rewrite_bullets(bullets: list[str], quals: list[str]) -> list[str]:
    """
    Send all bullets to Gemini API in one batch call for efficiency.

    Returns:
        List of rewritten bullets in same order
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

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )

        response_text = response.text
        response_text = _strip_markdown_json(response_text)

        rewritten = json.loads(response_text)

        if not isinstance(rewritten, list):
            raise ValueError("Response is not a JSON array")

        if len(rewritten) != len(bullets):
            print(f"Warning: Gemini returned {len(rewritten)} bullets but expected {len(bullets)}")
            raise ValueError("Bullet count mismatch")

        return rewritten

    except json.JSONDecodeError as e:
        print(f"Error: Malformed JSON from Gemini - {e}")
        raise
    except Exception as e:
        print(f"Error in rewrite_bullets: {e}")
        raise


def rewrite_single_with_retry(bullet: str, quals: list[str], max_retries: int = 3) -> str:
    """
    Rewrite a single bullet with validation and retry logic.

    Falls back to original bullet if all retries fail.
    """
    for attempt in range(max_retries):
        try:
            rewritten_list = rewrite_bullets([bullet], quals)
            rewritten = rewritten_list[0]

            is_valid, reason = validate_bullet(bullet, rewritten)

            if is_valid:
                return rewritten
            else:
                print(f"Validation failed (attempt {attempt + 1}/{max_retries}): {reason}")
                if attempt < max_retries - 1:
                    feedback_prompt = f"""Previous rewrite failed validation: {reason}

Original bullet: {bullet}
Your rewrite: {rewritten}

Please rewrite again, fixing the issue. Return ONLY a JSON array with one bullet."""

                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=feedback_prompt
                    )
                    response_text = _strip_markdown_json(response.text)
                    retry_result = json.loads(response_text)

                    if isinstance(retry_result, list) and len(retry_result) > 0:
                        rewritten = retry_result[0]
                        is_valid, reason = validate_bullet(bullet, rewritten)
                        if is_valid:
                            return rewritten

        except Exception as e:
            print(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt == max_retries - 1:
                print(f"All retries exhausted, returning original bullet")
                return bullet

    return bullet


def rewrite_all(bullets: list[str], quals: list[str]) -> list[str]:
    """
    Rewrite all bullets with batch processing and per-bullet fallback.

    First attempts batch rewrite. For any failing validations, falls back
    to per-bullet retry logic.
    """
    try:
        rewritten_bullets = rewrite_bullets(bullets, quals)

        final_bullets = []
        for i, (original, rewritten) in enumerate(zip(bullets, rewritten_bullets)):
            is_valid, reason = validate_bullet(original, rewritten)

            if is_valid:
                final_bullets.append(rewritten)
            else:
                print(f"\nBullet {i + 1} failed validation: {reason}")
                print(f"Falling back to single retry for: {original[:60]}...")
                fallback = rewrite_single_with_retry(original, quals)
                final_bullets.append(fallback)

        return final_bullets

    except Exception as e:
        print(f"Batch rewrite failed: {e}")
        print("Falling back to per-bullet processing for all bullets")

        final_bullets = []
        for i, bullet in enumerate(bullets):
            print(f"\nProcessing bullet {i + 1}/{len(bullets)}...")
            rewritten = rewrite_single_with_retry(bullet, quals)
            final_bullets.append(rewritten)

        return final_bullets
