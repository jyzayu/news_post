from __future__ import annotations

import os
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class YTNService:
    def __init__(self) -> None:
        # Override via env; default to YTN 경제 카테고리 리스트 페이지
        self.list_url = os.getenv(
            "YTN_LIST_URL",
            "https://www.ytn.co.kr/news/list.php?mcd=0102",
        )

    def fetch_latest(self, limit: int = 10) -> List[Dict[str, str]]:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        })

        try:
            resp = session.get(self.list_url, timeout=12)
            resp.raise_for_status()
        except Exception:
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        wrap = soup.select_one("div.news_list_wrap") or soup

        # collect top links first
        link_items: List[Dict[str, str]] = []
        for block in wrap.select("div.news_list"):
            a = block.select_one(".text_area .title a")
            if not a:   
                continue
            href = a.get("href")
            if not href:
                continue
            title = a.get_text(strip=True)
            link = urljoin(self.list_url, href)
            link_items.append({"title": title, "link": link})
            if len(link_items) >= limit:
                break

        # visit each link sequentially and parse details
        detailed: List[Dict[str, str]] = []
        for li in link_items:
            try:
                d = self._parse_detail(session, li["link"])
            except Exception:
                d = {"content": "", "published_at": "", "phone": "", "email": ""}
            detailed.append({
                "title": li["title"],
                "link": li["link"],
                "content": d.get("content", ""),
                "published_at": d.get("published_at", ""),
                "phone": d.get("phone", ""),
                "email": d.get("email", ""),
            })

        return detailed

    def _parse_detail(self, session: requests.Session, url: str) -> Dict[str, str]:
        r = session.get(url, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 작성일
        date_div = soup.select_one("div.date")
        published_at = date_div.get_text(strip=True) if date_div else ""

        # 본문 span 텍스트 (요구사항: span 태그 텍스트 저장)
        # 우선 기사 영역 내 span을 찾되, 없으면 가장 긴 span 텍스트를 선택
        content_text = ""
        article_container = soup.select_one(".article, #article, .article_wrap, #CmAdContent, .content, .news, .article-view")
        span_candidates = []
        if article_container:
            span_candidates = article_container.select("span")
        if not span_candidates:
            span_candidates = soup.select("span")
        if span_candidates:
            # choose the span with the longest text
            texts = [s.get_text("\n", strip=True) for s in span_candidates]
            content_text = max(texts, key=lambda t: len(t)) if texts else ""

        # 전화/메일 추출
        full_text = soup.get_text("\n", strip=True)
        phone = self._extract_after_marker(full_text, "[전화]")
        email = self._extract_after_marker(full_text, "[메일]")

        return {
            "published_at": published_at,
            "content": content_text,
            "phone": phone,
            "email": email,
        }

    @staticmethod
    def _extract_after_marker(text: str, marker: str) -> str:
        import re
        # capture everything after marker up to a line break
        # e.g., "[전화] 02-398-8585" -> "02-398-8585"
        pattern = re.compile(re.escape(marker) + r"\s*([^\n\r<]+)")
        m = pattern.search(text)
        return m.group(1).strip() if m else ""