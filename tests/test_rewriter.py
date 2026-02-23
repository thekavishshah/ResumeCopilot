from app.ai.rewriter import rewrite_all, validate_bullet

SAMPLE_BULLETS = [
    "Developed automated testing framework using Selenium, reducing QA time by 40%",
    "Led team of 5 engineers to migrate legacy monolith to microservices architecture",
    "Built ETL data pipeline processing 2.5M records daily with 99.9% uptime",
    "Implemented CI/CD pipeline reducing deployment time from 3 hours to 15 minutes"
]

SAMPLE_QUALS = [
    "Python",
    "data pipelines",
    "cross-functional teams",
    "scalable systems",
    "automation",
    "microservices"
]


def main():
    print("=" * 80)
    print("RESUME BULLET REWRITER TEST")
    print("=" * 80)
    print("\nJob Qualifications:")
    for qual in SAMPLE_QUALS:
        print(f"  - {qual}")

    print("\n" + "=" * 80)
    print("PROCESSING BULLETS...")
    print("=" * 80)

    rewritten_bullets = rewrite_all(SAMPLE_BULLETS, SAMPLE_QUALS)

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    for i, (original, rewritten) in enumerate(zip(SAMPLE_BULLETS, rewritten_bullets), 1):
        is_valid, reason = validate_bullet(original, rewritten)
        status = "✓ PASS" if is_valid else f"✗ FAIL: {reason}"

        print(f"\n[Bullet {i}] {status}")
        print(f"Original  ({len(original):3d} chars): {original}")
        print(f"Rewritten ({len(rewritten):3d} chars): {rewritten}")
        print(f"Length diff: {abs(len(rewritten) - len(original))} chars")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
