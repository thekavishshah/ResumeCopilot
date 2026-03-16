"""
Test bullet point extraction
"""
import asyncio
from app.scraper import scrape_job_description


async def test_bullets():
    """Test bullet extraction from TransUnion"""

    url = "https://transunion.wd5.myworkdayjobs.com/en-US/TransUnion/job/Boca-Raton-Florida/Entry-Level-Software-Engineer_19038868"

    print("Testing Bullet Point Extraction")
    print("=" * 90)
    print(f"URL: {url}")
    print("=" * 90)
    print()

    result = await scrape_job_description(url)

    if result:
        print(f"✓ SUCCESS!")
        print(f"Platform: {result.get('platform')}")
        print(f"Title: {result.get('title')}")
        print()

        qualifications = result.get('qualifications', [])
        print(f"Individual Bullets Extracted: {len(qualifications)}")
        print("=" * 90)

        for i, qual in enumerate(qualifications, 1):
            print(f"\n{i}. {qual}")

        print("\n" + "=" * 90)
    else:
        print("✗ FAILED")


if __name__ == "__main__":
    asyncio.run(test_bullets())
