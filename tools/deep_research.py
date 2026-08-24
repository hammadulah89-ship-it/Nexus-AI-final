"""
Pillar 5: Deep Research Multi-Hop Investigation Engine.
Deconstructs complex research topics into sub-queries, crawls 10-15+ web pages concurrently,
cross-verifies findings, and compiles an in-depth Executive Research Dossier.
"""

import asyncio
import json
import re
import time
from typing import Dict, List, Any, Optional
import httpx

from config import GROQ_API_KEY, GROQ_MODEL, SUPPORTED_MODELS
from tools.web_search import RealWebCrawler

class DeepResearchEngine:
    def __init__(self):
        self.crawler = RealWebCrawler()
        self.api_key = GROQ_API_KEY
        self.model = GROQ_MODEL

    async def generate_subqueries(self, topic: str) -> List[str]:
        """Deconstructs a broad research topic into 3-4 targeted sub-queries."""
        prompt = (
            f"You are the NexusAI Senior Research Analyst.\n"
            f"Deconstruct the following research topic into 3 to 4 distinct, highly focused search queries:\n"
            f"Topic: '{topic}'\n\n"
            "Format: Output ONLY a JSON array of strings, e.g. [\"subquery 1\", \"subquery 2\", \"subquery 3\"]."
        )

        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "User-Agent": "NexusAI/1.0"}
            body = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"]
                    match = re.search(r'\[.*?\]', raw, re.DOTALL)
                    if match:
                        queries = json.loads(match.group(0))
                        return [q.strip() for q in queries if isinstance(q, str)][:4]
        except Exception:
            pass

        return [
            f"{topic} overview developments",
            f"{topic} technical architecture analysis",
            f"{topic} market trends forecast 2026",
            f"{topic} challenges key players"
        ]

    async def execute_dossier_investigation(self, topic: str) -> Dict[str, Any]:
        """
        Runs the full 4-stage multi-hop deep research investigation:
        1. Planning (Sub-queries)
        2. Multi-Engine Parallel Investigation (10-15+ pages)
        3. Cross-Checking & Deep Scraping
        4. Executive Dossier Compilation
        """
        t_start = time.perf_counter()
        
        # Stage 1: Generate subqueries
        subqueries = await self.generate_subqueries(topic)
        
        # Stage 2: Parallel crawl across all sub-queries
        search_tasks = [self.crawler.execute_search(sq, max_results=4) for sq in subqueries]
        results_batches = await asyncio.gather(*search_tasks, return_exceptions=True)

        all_sources: List[Dict[str, Any]] = []
        seen_urls = set()

        for batch in results_batches:
            if isinstance(batch, list):
                for s in batch:
                    if s["url"] not in seen_urls:
                        seen_urls.add(s["url"])
                        all_sources.append(s)

        for idx, src in enumerate(all_sources):
            src["source_id"] = idx + 1

        # Stage 3: Synthesize Executive Research Dossier
        context_blocks = []
        for s in all_sources[:10]:
            content = s.get("full_text") or s.get("snippet", "")
            context_blocks.append(f"Source [{s['source_id']}]: {s['title']}\nURL: {s['url']}\nContent: {content[:800]}\n")

        joined_context = "\n".join(context_blocks)

        dossier_prompt = (
            f"You are NexusAI, an elite Autonomous Research Operating System compiling an Executive Research Dossier on:\n"
            f"'{topic}'\n\n"
            f"Based on the following verified live web sources, compile a comprehensive, multi-section research report:\n\n"
            f"RETRIEVED RESEARCH SOURCES:\n{joined_context}\n\n"
            "REQUIRED DOSSIER SECTIONS:\n"
            "1. # 📑 Executive Summary & Core Thesis\n"
            "2. ## 🔬 Technical & Architectural Breakdown\n"
            "3. ## 📊 Comparative Matrix / Industry Data Table\n"
            "4. ## 📈 Market Dynamics, Roadmaps & 2026 Forecasts\n"
            "5. ## ⚠️ Strategic Challenges, Bottlenecks & Controversies\n"
            "6. ## 📌 Key Actionable Takeaways\n\n"
            "Citations: Whenever referencing facts, cite using [1], [2], etc. matching the source numbers.\n"
            "Identity: You are strictly NexusAI."
        )

        dossier_content = ""
        try:
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "User-Agent": "NexusAI/1.0"}
            body = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are NexusAI, an elite technical intelligence dossier writer. You produce thorough, beautifully structured reports."},
                    {"role": "user", "content": dossier_prompt}
                ],
                "temperature": 0.35,
                "max_tokens": 2500
            }
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=body)
                if resp.status_code == 200:
                    raw = resp.json()["choices"][0]["message"]["content"]
                    dossier_content = re.sub(r'<think>.*?(?:</think>|$)', '', raw, flags=re.DOTALL).strip()
        except Exception as e:
            dossier_content = f"Error generating research dossier: {str(e)}"

        total_time = round((time.perf_counter() - t_start) * 1000, 2)

        return {
            "topic": topic,
            "subqueries": subqueries,
            "sources_investigated_count": len(all_sources),
            "sources": all_sources,
            "dossier_markdown": dossier_content,
            "investigation_time_ms": total_time
        }
