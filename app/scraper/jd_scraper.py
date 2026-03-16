"""
Job Description Scraper
Supports scraping from common job application platforms:
- Workday
- Greenhouse
- SmartRecruiters
- Lever
- Generic fallback for other sites
"""

import re
import json
from typing import Optional, Dict, Any
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup


class JobDescriptionScraper:
    """Scrapes job descriptions from various job posting platforms"""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

    def detect_platform(self, url: str) -> str:
        """Detect the job posting platform from URL"""
        url_lower = url.lower()

        if "myworkdayjobs.com" in url_lower or "workday.com" in url_lower:
            return "workday"
        elif "greenhouse.io" in url_lower or "boards.greenhouse.io" in url_lower:
            return "greenhouse"
        elif "smartrecruiters.com" in url_lower:
            return "smartrecruiters"
        elif "lever.co" in url_lower or "jobs.lever.co" in url_lower:
            return "lever"
        elif "ashbyhq.com" in url_lower:
            return "ashby"
        elif "jobvite.com" in url_lower:
            return "jobvite"
        elif "icims.com" in url_lower:
            return "icims"
        elif "taleo.net" in url_lower or "taleo.com" in url_lower:
            return "taleo"
        else:
            return "generic"

    async def fetch_page(self, url: str) -> Optional[str]:
        """Fetch HTML content from URL"""
        try:
            async with httpx.AsyncClient(follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.text
        except Exception as e:
            print(f"Error fetching page: {e}")
            return None

    def _scrape_workday(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """
        Scrape job description from Workday

        Workday uses JavaScript rendering, but includes job data in:
        1. OpenGraph meta tags
        2. JSON-LD structured data (schema.org)
        3. HTML bullet points in the description
        """
        try:
            title = None
            description = None
            quals = []

            # Method 1: Try JSON-LD structured data (most reliable)
            json_ld_script = soup.find("script", type="application/ld+json")
            if json_ld_script:
                try:
                    job_data = json.loads(json_ld_script.string)
                    if job_data.get("@type") == "JobPosting":
                        title = job_data.get("title")
                        description = job_data.get("description")
                except (json.JSONDecodeError, AttributeError) as e:
                    print(f"Warning: Could not parse JSON-LD: {e}")

            # Method 2: Try OpenGraph meta tags as fallback
            if not title:
                title_meta = soup.find("meta", property="og:title")
                if title_meta:
                    title = title_meta.get("content")

            if not description:
                desc_meta = soup.find("meta", property="og:description")
                if desc_meta:
                    description = desc_meta.get("content")

            # Extract bullet points from description
            if description:
                # Method 1: Try to extract HTML bullet points first
                desc_soup = BeautifulSoup(description, "html.parser")
                list_elements = desc_soup.find_all(["ul", "ol"])

                for list_elem in list_elements:
                    items = list_elem.find_all("li")
                    for item in items:
                        bullet_text = item.get_text(strip=True)
                        if len(bullet_text) >= 15:
                            quals.append(bullet_text)

                # Method 2: If no HTML bullets, parse plain text by sections
                if not quals:
                    text = desc_soup.get_text(separator=" ")

                    # Define section headers that typically contain bullet points
                    # Note: Using [\u2019\u2018'] to match straight (') and curly (' ') apostrophes
                    # Some headers have colons, some don't - match both
                    section_patterns = [
                        # Responsibilities/Tasks
                        r"What You[\u2019\u2018']ll (?:Do|Be Doing):?",
                        r"What You Will Do:?",
                        r"Impact You[\u2019\u2018']ll Make:?",
                        r"Your (?:Role|Responsibilities):?",
                        r"(?:Key |Primary |Main )?(?:Responsibilities|Duties|Tasks):?",
                        r"In This Role You Will:?",

                        # Qualifications
                        r"What (?:You[\u2019\u2018']ll Bring|We (?:Need to See|Are Looking For)):?",
                        r"What We Are Looking For \(Must-Haves?\):?",
                        r"We[\u2019\u2018']d Love to See:?",
                        r"Ways to Stand Out(?: from the Crowd)?:?",
                        r"Bonus Points? \(Nice-to-Haves?\):?",
                        r"(?:Minimum |Basic |Required |Essential )?(?:Qualifications?|Requirements?|Skills?):?",
                        r"(?:Preferred |Desired |Nice to Have |Bonus )(?:Qualifications?|Requirements?|Skills?):?",
                        r"You (?:Must Have|Should Have|Will Have):?",
                        r"We[\u2019\u2018']re Looking For:?",
                        r"Position Requires?:?",
                        r"Must Have:?",
                        r"Ideal Candidate:?",
                    ]

                    # Build regex to find sections
                    combined_pattern = "|".join(f"({p})" for p in section_patterns)

                    # Find all section matches
                    matches = list(re.finditer(combined_pattern, text, re.IGNORECASE))

                    # Define end markers that signal the end of relevant job content
                    end_markers = [
                        # TransUnion markers
                        "TransUnion complies",
                        "Adherence to",
                        "This job is assigned",
                        "View TransUnion",
                        "Beware of scams",

                        # NVIDIA markers
                        "NVIDIA's invention of",
                        "NVIDIA is widely considered",
                        "NVIDIA is the world leader",
                        "NVIDIA pioneered",
                        "Our GPUs are being used",

                        # Salesforce markers
                        "Unleash Your Potential",
                        "When you join Salesforce",
                        "Accommodations If you require",
                        "Posting Statement",
                        "Salesforce is an equal opportunity",
                        "Know your rights:",
                        "This policy applies to current",
                        "Recruiting, hiring, and promotion",
                        "In the United States, compensation",
                        "Salesforce offers a variety",
                        "Slack is a messaging app",

                        # Generic markers
                        "Applicants must be authorized",
                        "Qualified applicants with arrest",
                        "Benefits:",
                        "We are committed to being",
                        "As an equal opportunity",
                        "Pay Scale Information",
                        "Your base salary will be determined",
                        "The base salary range",
                        "Applications for this job",
                        "This posting is for",
                        "Internal Job Title:",
                        "Company:",
                        "is a global",
                        "If you're creative, autonomous",
                    ]

                    for i, match in enumerate(matches):
                        section_start = match.end()

                        # Find where this section ends (start of next section or end of text)
                        if i + 1 < len(matches):
                            section_end = matches[i + 1].start()
                        else:
                            section_end = len(text)

                        section_text = text[section_start:section_end].strip()

                        # Check if section contains end markers - if so, truncate there
                        for marker in end_markers:
                            marker_pos = section_text.find(marker)
                            if marker_pos != -1:
                                section_text = section_text[:marker_pos].strip()
                                break

                        # Check if this section uses labeled bullets (Salesforce format)
                        # Pattern: "Label Name: Description text."
                        labeled_pattern = r'([A-Z][A-Za-z &/-]+):\s+([A-Z][^:]+?)(?=\s+[A-Z][A-Za-z &/-]+:|$)'
                        labeled_matches = re.findall(labeled_pattern, section_text)

                        if len(labeled_matches) >= 3:  # If we find 3+ labeled bullets, use that format
                            for label, description in labeled_matches:
                                # Clean up the description
                                description = description.strip().rstrip('.')
                                label_lower = label.lower()

                                # Skip if label is too generic, description too short,
                                # or it's an "ideal candidate" trait rather than a requirement
                                if (len(description) < 30 or
                                    label_lower in ['about', 'note', 'important'] or
                                    description.lower().startswith(('we are seeking', 'the ideal')) or
                                    # Skip "ideal candidate" trait labels
                                    label_lower.startswith(('a ', 'the ')) or
                                    label_lower in ['technical', 'builder', 'communicator', 'customer-focused', 'leader']):
                                    continue

                                # Include both label and description
                                quals.append(f"{label}: {description}")
                        else:
                            # Fall back to sentence splitting
                            sentences = re.split(r'\.\s+(?=[A-Z])', section_text)

                            for sentence in sentences:
                                sentence = sentence.strip()
                                sentence = sentence.rstrip('.')

                                # Only include substantial bullets (15+ chars, max 300)
                                # Skip generic intro sentences and fragments
                                sentence_lower = sentence.lower()

                                # Skip if it's too short or too long
                                if not (40 <= len(sentence) <= 300):
                                    continue

                                # Skip if it starts with generic marketing/intro text
                                if sentence_lower.startswith((
                                    # Generic intros
                                    'we are seeking', 'the ideal candidate', 'this role offers',
                                    'the company does not', 'spousal,', 'additionally,', 'components of',
                                    'at transunion,', 'at salesforce', 'certain positions',
                                    'if you received', 'be wary', 'contact careers',
                                    'we make trust', 'we do this', 'through our',
                                    'as a result,', 'we call this',
                                    # Salesforce/company marketing & "ideal candidate" traits
                                    'trailblazers who', 'ready to level', 'about the role',
                                    'agentforce is', 'we work at', 'we\'re building',
                                    'a senior engineer', 'a builder:', 'customer-focused:',
                                    'technical:', 'a communicator:', 'a leader:',
                                    'your technical problem', 'will be essential',
                                    'you\'ll take complete', 'you will collaborate',
                                    'as a senior engineer', 'involves advocating',
                                    'you will coordinate', 'this includes',
                                    'you\'ll be responsible', 'your role',
                                    # Legal/benefits
                                    'this policy applies', 'recruiting, hiring',
                                    'the same goes', 'in the united states',
                                    'certain roles may', 'salesforce offers',
                                    'more details about', 'slack is a messaging',
                                    'it\'s a platform', 'and everything happens',
                                    'ensuring a diverse', 'we welcome people',
                                    'we are an equal', 'come do the best',
                                    '– without regard', 'it also applies'
                                )):
                                    continue

                                # Skip sentences that are fragments or don't look like requirements
                                if (sentence_lower.startswith(('for ', 'into ', 'and ', 'ed at', 'will be', 'of ', 'with ', ', and')) or
                                    'we\'re looking for' in sentence_lower or
                                    'our team is' in sentence_lower):
                                    continue

                                quals.append(sentence)

                # Method 3: If still no bullets, look for text with bullet markers
                if not quals:
                    lines = text.split("\n")
                    for line in lines:
                        line = line.strip()
                        if re.match(r'^[\u2022\u2023\u25E6\u2043\u2219\*\-\+•]\s+', line):
                            bullet_text = re.sub(r'^[\u2022\u2023\u25E6\u2043\u2219\*\-\+•]\s+', '', line).strip()
                            if len(bullet_text) >= 15:
                                quals.append(bullet_text)

            # Remove duplicates while preserving order
            seen = set()
            quals = [x for x in quals if not (x in seen or seen.add(x))]

            if not title and not description:
                return None

            return {
                "title": title or "Unknown Position",
                "description": description or "",
                "qualifications": quals,
                "platform": "workday"
            }
        except Exception as e:
            print(f"Error scraping Workday: {e}")
            return None

    def _scrape_greenhouse(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Scrape job description from Greenhouse"""
        try:
            # Job title
            title_elem = soup.find("h1", class_="app-title")
            if not title_elem:
                title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"

            # Job description
            description = ""
            desc_container = soup.find("div", id="content")
            if not desc_container:
                desc_container = soup.find("div", class_=re.compile(r"content|job-description"))

            if desc_container:
                description = desc_container.get_text(separator="\n", strip=True)

            # Extract qualifications
            quals = []
            qual_sections = soup.find_all(["ul", "ol"])
            for section in qual_sections:
                items = section.find_all("li")
                quals.extend([item.get_text(strip=True) for item in items])

            if not description and not quals:
                return None

            return {
                "title": title,
                "description": description,
                "qualifications": quals,
                "platform": "greenhouse"
            }
        except Exception as e:
            print(f"Error scraping Greenhouse: {e}")
            return None

    def _scrape_smartrecruiters(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Scrape job description from SmartRecruiters"""
        try:
            # Job title
            title_elem = soup.find("h1", class_=re.compile(r"job-title|position-title"))
            if not title_elem:
                title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"

            # Job description
            description = ""
            desc_container = soup.find("div", class_=re.compile(r"job-description|details-description"))
            if desc_container:
                description = desc_container.get_text(separator="\n", strip=True)

            # Extract qualifications
            quals = []
            qual_sections = soup.find_all(["ul", "ol"])
            for section in qual_sections:
                items = section.find_all("li")
                quals.extend([item.get_text(strip=True) for item in items])

            if not description and not quals:
                return None

            return {
                "title": title,
                "description": description,
                "qualifications": quals,
                "platform": "smartrecruiters"
            }
        except Exception as e:
            print(f"Error scraping SmartRecruiters: {e}")
            return None

    def _scrape_lever(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Scrape job description from Lever"""
        try:
            # Job title
            title_elem = soup.find("h2", class_="posting-headline")
            if not title_elem:
                title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"

            # Job description
            description = ""
            desc_container = soup.find("div", class_="posting-description")
            if desc_container:
                description = desc_container.get_text(separator="\n", strip=True)

            # Extract qualifications
            quals = []
            qual_sections = soup.find_all(["ul", "ol"])
            for section in qual_sections:
                items = section.find_all("li")
                quals.extend([item.get_text(strip=True) for item in items])

            if not description and not quals:
                return None

            return {
                "title": title,
                "description": description,
                "qualifications": quals,
                "platform": "lever"
            }
        except Exception as e:
            print(f"Error scraping Lever: {e}")
            return None

    def _scrape_generic(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Generic fallback scraper for unknown platforms"""
        try:
            # Try to find title
            title_elem = soup.find("h1")
            title = title_elem.get_text(strip=True) if title_elem else "Unknown Position"

            # Try to find main content
            description = ""

            # Common content selectors
            content_selectors = [
                ("div", {"class": re.compile(r"job-description|description|content|posting")}),
                ("div", {"id": re.compile(r"job-description|description|content")}),
                ("main", {}),
                ("article", {}),
            ]

            for tag, attrs in content_selectors:
                desc_container = soup.find(tag, attrs)
                if desc_container:
                    description = desc_container.get_text(separator="\n", strip=True)
                    break

            # Extract qualifications
            quals = []
            qual_sections = soup.find_all(["ul", "ol"])
            for section in qual_sections:
                items = section.find_all("li")
                quals.extend([item.get_text(strip=True) for item in items if item.get_text(strip=True)])

            # Filter out very short or likely navigation items
            quals = [q for q in quals if len(q) > 10][:50]  # Limit to 50 most relevant

            if not description and not quals:
                return None

            return {
                "title": title,
                "description": description,
                "qualifications": quals,
                "platform": "generic"
            }
        except Exception as e:
            print(f"Error in generic scraper: {e}")
            return None

    async def scrape(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Main scraping method

        Args:
            url: URL of the job posting

        Returns:
            Dictionary containing:
            - title: Job title
            - description: Full job description text
            - qualifications: List of qualification/requirement strings
            - platform: Platform name
            Returns None if scraping fails
        """
        # Fetch page
        html = await self.fetch_page(url)
        if not html:
            return None

        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, "lxml")

        # Detect platform and use appropriate scraper
        platform = self.detect_platform(url)

        scrapers = {
            "workday": self._scrape_workday,
            "greenhouse": self._scrape_greenhouse,
            "smartrecruiters": self._scrape_smartrecruiters,
            "lever": self._scrape_lever,
            "ashby": self._scrape_generic,
            "jobvite": self._scrape_generic,
            "icims": self._scrape_generic,
            "taleo": self._scrape_generic,
            "generic": self._scrape_generic,
        }

        scraper_func = scrapers.get(platform, self._scrape_generic)
        result = scraper_func(soup)

        if result:
            result["url"] = url

        return result


# Convenience function for easy importing
async def scrape_job_description(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Scrape job description from a URL

    Args:
        url: URL of the job posting
        timeout: Request timeout in seconds

    Returns:
        Dictionary with job info or None if scraping fails
    """
    scraper = JobDescriptionScraper(timeout=timeout)
    return await scraper.scrape(url)
