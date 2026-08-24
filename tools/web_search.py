"""
Pillar 4: Verified Multi-Source Live Web Crawler & Safe Page Fetcher.
Zero fabricated URLs, strict public URL validation, and concurrent scraping.
"""

import asyncio
import html
import re
import time
import urllib.parse
from typing import List, Dict, Any, Optional, Tuple
import httpx
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
]

DISALLOWED_DOMAINS = ["localhost", "127.0.0.1", "0.0.0.0", "arena.site", "e2b.app"]

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_domain(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc or parsed.path
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.split(":")[0].lower()
    except Exception:
        return ""

def is_valid_web_url(url: str) -> bool:
    if not url or not isinstance(url, str):
        return False
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        domain = extract_domain(url)
        if not domain or "." not in domain:
            return False
        if any(bad in domain for bad in DISALLOWED_DOMAINS):
            return False
        return True
    except Exception:
        return False


class RealWebCrawler:
    def __init__(self):
        self.headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }

    async def search_duckduckgo(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        results = []
        url = "https://lite.duckduckgo.com/lite/"
        data = urllib.parse.urlencode({"q": query}).encode("utf-8")
        headers = {
            "User-Agent": USER_AGENTS[0],
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-US,en;q=0.9"
        }
        try:
            async with httpx.AsyncClient(headers=headers, timeout=7.0, follow_redirects=True) as client:
                resp = await client.post(url, content=data)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    links = soup.select(".result-link")
                    snippets = soup.select(".result-snippet")
                    for l, s in zip(links, snippets):
                        raw_href = l.get("href", "")
                        title = clean_text(l.get_text())
                        snippet = clean_text(s.get_text())
                        final_url = raw_href
                        if "uddg=" in raw_href:
                            try:
                                final_url = urllib.parse.unquote(raw_href.split("uddg=")[1].split("&")[0])
                            except Exception:
                                pass
                        if is_valid_web_url(final_url):
                            results.append({
                                "source_id": len(results) + 1,
                                "url": final_url,
                                "domain": extract_domain(final_url),
                                "title": title,
                                "snippet": snippet,
                                "source_type": "web"
                            })
                            if len(results) >= max_results:
                                break
        except Exception as e:
            print(f"[RealWebCrawler] DDG error: {e}")
        return results

    async def search_wikipedia(self, query: str) -> Optional[Dict[str, Any]]:
        try:
            clean_q = re.sub(r'^(what is|who is|explain|tell me about|how does|what are)\s+', '', query, flags=re.IGNORECASE).strip()
            search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(clean_q)}&format=json&utf8=1"
            async with httpx.AsyncClient(headers=self.headers, timeout=5.0) as client:
                resp = await client.get(search_url)
                if resp.status_code == 200:
                    data = resp.json()
                    hits = data.get("query", {}).get("search", [])
                    if not hits:
                        return None
                    top_title = hits[0]["title"]
                    page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(top_title.replace(' ', '_'))}"
                    extract_url = f"https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1&titles={urllib.parse.quote(top_title)}&format=json&utf8=1"
                    resp2 = await client.get(extract_url)
                    if resp2.status_code == 200:
                        data2 = resp2.json()
                        pages = data2.get("query", {}).get("pages", {})
                        for _, p in pages.items():
                            extract = clean_text(p.get("extract", ""))
                            if extract and len(extract) > 40:
                                return {
                                    "source_id": 1,
                                    "url": page_url,
                                    "domain": "wikipedia.org",
                                    "title": f"{top_title} — Wikipedia",
                                    "snippet": extract[:350] + "...",
                                    "full_text": extract[:2500],
                                    "source_type": "encyclopedia"
                                }
        except Exception as e:
            print(f"[RealWebCrawler] Wiki error: {e}")
        return None

    async def search_google_news(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        results = []
        try:
            encoded_q = urllib.parse.quote(query)
            rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl=en-US&gl=US&ceid=US:en"
            async with httpx.AsyncClient(headers=self.headers, timeout=5.0, follow_redirects=True) as client:
                resp = await client.get(rss_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "xml")
                    items = soup.find_all("item")
                    for item in items[:max_results]:
                        title = clean_text(item.title.text if item.title else "")
                        link = item.link.text if item.link else ""
                        description = clean_text(item.description.text if item.description else "")
                        if is_valid_web_url(link):
                            results.append({
                                "source_id": len(results) + 1,
                                "url": link,
                                "domain": extract_domain(link),
                                "title": title,
                                "snippet": (description or title)[:280],
                                "source_type": "news"
                            })
        except Exception as e:
            print(f"[RealWebCrawler] News error: {e}")
        return results

    async def scrape_single_page(self, client: httpx.AsyncClient, url: str) -> Dict[str, Any]:
        if not is_valid_web_url(url):
            return {"url": url, "text": "", "success": False}
        try:
            resp = await client.get(url, timeout=5.0, follow_redirects=True)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text[:200000], "html.parser")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "form", "svg"]):
                    tag.decompose()
                paragraphs = []
                for p in soup.find_all(["p", "article", "section"]):
                    txt = clean_text(p.get_text())
                    if len(txt.split()) >= 10:
                        paragraphs.append(txt)
                full_text = " ".join(paragraphs[:6])
                return {"url": str(resp.url), "text": full_text[:1400], "success": True}
        except Exception:
            pass
        return {"url": url, "text": "", "success": False}

    async def execute_search(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        clean_q = re.sub(r'^(can you|please|could you)?\s*(tell me|search for|find|look up|show me)?\s*', '', query, flags=re.IGNORECASE).strip()
        if len(clean_q) < 2:
            clean_q = query

        tasks = [
            self.search_duckduckgo(clean_q, max_results=max_results),
            self.search_wikipedia(clean_q),
            self.search_google_news(clean_q, max_results=3)
        ]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        merged = []
        seen = set()
        for item in raw_results:
            if isinstance(item, list):
                for s in item:
                    if s["url"] not in seen and is_valid_web_url(s["url"]):
                        seen.add(s["url"])
                        merged.append(s)
            elif isinstance(item, dict) and item:
                if item["url"] not in seen and is_valid_web_url(item["url"]):
                    seen.add(item["url"])
                    merged.insert(0, item)

        merged = merged[:max_results]
        for idx, res in enumerate(merged):
            res["source_id"] = idx + 1

        # Deep scrape top pages
        scrape_candidates = [s for s in merged[:3] if not s.get("full_text")]
        if scrape_candidates:
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True) as client:
                tasks = [self.scrape_single_page(client, s["url"]) for s in scrape_candidates]
                res_list = await asyncio.gather(*tasks, return_exceptions=True)
                for s, r in zip(scrape_candidates, res_list):
                    if isinstance(r, dict) and r.get("success"):
                        s["full_text"] = r["text"]

        return merged
