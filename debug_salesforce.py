"""
Debug script to see what Salesforce Workday returns
"""
import asyncio
from app.scraper import scrape_job_description


async def debug():
    """Debug bullet extraction for Salesforce"""

    url = "https://salesforce.wd12.myworkdayjobs.com/Slack/job/North-Carolina---Raleigh/Software-Engineer-II---Product-Backend_JR327593"

    print("Debugging Salesforce Workday Job")
    print("=" * 90)

    result = await scrape_job_description(url)

    if result:
        print(f"Title: {result.get('title')}")
        print(f"Platform: {result.get('platform')}")
        desc = result.get('description', '')
        print(f"\nDescription length: {len(desc)}")
        print("\nFull description:")
        print("-" * 90)
        print(desc)
        print("-" * 90)
        print(f"\nBullets found: {len(result.get('qualifications', []))}")

        # Check for HTML
        if '<ul>' in desc or '<li>' in desc:
            print("\n[HTML lists detected]")
            # Extract and show first few li items
            import re
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(desc, 'html.parser')
            lis = soup.find_all('li')[:10]
            print(f"Found {len(lis)} <li> items (showing first 10):")
            for i, li in enumerate(lis, 1):
                print(f"  {i}. {li.get_text(strip=True)[:100]}")
        else:
            print("\n[No HTML lists found]")

        # Check for section headers
        import re
        print("\nSearching for 'What' sections:")
        what_matches = re.findall(r'What [A-Z][^.!?]{5,60}(?:\(|:)', desc)
        for match in what_matches:
            print(f"  - {match}")

        # Find exact headers
        print("\nExact 'What' headers in the text:")
        for match in re.finditer(r'(What [^.!?]{5,80}?)(Technical|Backend|Salesforce|Your)', desc):
            snippet = match.group(0)
            print(f"  '{snippet[:80]}'")

        print("\nExact 'Bonus' headers in the text:")
        for match in re.finditer(r'(Bonus [^.!?]{5,80}?)(Salesforce|Slack|GenAI|Real-Time|Integration)', desc):
            snippet = match.group(0)
            print(f"  '{snippet[:80]}'")
    else:
        print("Failed to scrape")


if __name__ == "__main__":
    asyncio.run(debug())
