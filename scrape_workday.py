#!/usr/bin/env python3
"""
Interactive Workday Job Scraper
Prompts for a Workday job URL and extracts all bullet points
"""
import asyncio
from app.scraper import scrape_job_description


async def main():
    """Main function to scrape Workday job descriptions"""
    print("=" * 80)
    print("Workday Job Description Bullet Point Scraper")
    print("=" * 80)
    print()

    # Prompt for URL
    url = input("Enter Workday job URL: ").strip()

    if not url:
        print("Error: No URL provided")
        return

    # Validate it's a Workday URL
    if "workday" not in url.lower():
        print("Warning: This doesn't appear to be a Workday URL")
        confirm = input("Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled")
            return

    print()
    print("Fetching job description...")
    print("-" * 80)

    # Scrape the job description
    result = await scrape_job_description(url)

    if not result:
        print("Failed to scrape job description")
        print("This could be due to:")
        print("  - Invalid URL")
        print("  - Network issues")
        print("  - Job posting no longer available")
        print("  - Workday page format has changed")
        return

    # Display results
    print()
    print("SUCCESS!")
    print("=" * 80)
    print(f"Job Title: {result.get('title')}")
    print(f"Platform: {result.get('platform')}")
    print(f"URL: {result.get('url')}")
    print("=" * 80)
    print()

    bullets = result.get('qualifications', [])

    if bullets:
        print(f"Extracted {len(bullets)} bullet points:")
        print("-" * 80)
        for i, bullet in enumerate(bullets, 1):
            print(f"{i}. {bullet}")
            print()
    else:
        print("No bullet points found in this job description")
        print()
        print("The full description text is available in result['description']")
        print("You may need to check the job posting format")

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
