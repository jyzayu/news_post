from __future__ import annotations

import os
import time
from typing import Dict, List, Set
from concurrent.futures import ThreadPoolExecutor

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright


class YTNService:
    def __init__(self) -> None:
        # Override via env; default to YTN 경제 카테고리 리스트 페이지
        self.list_url = os.getenv(
            "YTN_LIST_URL",
            "https://www.ytn.co.kr",
        )

    def fetch_latest(self, limit: int = 10) -> List[Dict[str, str]]:
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://www.ytn.co.kr/",
            "Connection": "keep-alive",
        })

        link_items: List[Dict[str, str]] = []
        seen_links: Set[str] = set()

        # Use Playwright to render and collect anchors from both ULs (top document only)
        try:
            with sync_playwright() as p:
                headless_env = os.getenv("PLAYWRIGHT_HEADLESS", "1").strip()
                headless_flag = False if headless_env in {"0", "false", "False"} else True
                browser = p.chromium.launch(headless=headless_flag)
                context = browser.new_context()
                page = context.new_page()
                # Lower timeouts and block non-essential resources for speed
                try:
                    page.set_default_timeout(8000)
                    page.set_default_navigation_timeout(12000)
                except Exception:
                    pass
                try:
                    def _block_non_essential(route, request):
                        rt = request.resource_type
                        if rt in {"image", "media", "font", "stylesheet"}:
                            try:
                                route.abort()
                            except Exception:
                                route.continue_()
                        else:
                            route.continue_()
                    context.route("**/*", _block_non_essential)
                except Exception:
                    pass

                page.goto(self.list_url, timeout=12000, wait_until="domcontentloaded")

                # Collect anchors using a single DOM evaluation
                try:
                    anchors = page.evaluate(
                        """
                        () => {
                          const sels = ['ul.YTN_CSA_popularnews a', 'ul#ranking_hide a'];
                          const seen = new Set();
                          const out = [];
                          for (const sel of sels) {
                            for (const a of document.querySelectorAll(sel)) {
                              const href = (a.getAttribute('href')||'').trim();
                              const title = (a.textContent||'').trim();
                              if (!href || href.toLowerCase().startsWith('javascript:') || !title) continue;
                              try {
                                const url = new URL(href, location.href).href;
                                if (seen.has(url)) continue;
                                seen.add(url);
                                out.push({ title, link: url });
                              } catch (e) { /* ignore */ }
                            }
                          }
                          return out;
                        }
                        """
                    ) or []
                except Exception:
                    anchors = []

                for item in anchors:
                    if limit and len(link_items) >= limit:
                        break
                    link = (item.get("link") or "").strip()
                    title = (item.get("title") or "").strip()
                    if not link or not title:
                        continue
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    link_items.append({"title": title, "link": link})

                # Note: Do not collect from iframes per user request

                context.close()
                browser.close()
        except Exception:
            # If Playwright fails entirely, fall back to returning empty list here
            pass


        # Visit each link and parse details concurrently
        detailed: List[Dict[str, str]] = []
        def _fetch_detail(li: Dict[str, str]) -> Dict[str, str]:
            try:
                s = requests.Session()
                s.headers.update(session.headers)
                d = self._parse_detail(s, li.get("link", ""))
            except Exception:
                d = {"content": "", "published_at": "", "phone": "", "email": "", "reporter_name": "", "category": ""}
            return {
                "title": li.get("title", ""),
                "link": li.get("link", ""),
                "content": d.get("content", ""),
                "published_at": d.get("published_at", ""),
                "phone": d.get("phone", ""),
                "email": d.get("email", ""),
                "reporter_name": d.get("reporter_name", ""),
                "category": d.get("category", ""),
            }

        max_workers = min(8, max(1, os.cpu_count() or 4))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            for item in executor.map(_fetch_detail, link_items):
                detailed.append(item)

        return detailed

    def _parse_detail(self, session: requests.Session, url: str) -> Dict[str, str]:
        r = session.get(url, timeout=12)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # 작성일
        date_div = soup.select_one("div.date")
        published_at = date_div.get_text(strip=True) if date_div else ""

        # 카테고리: HTML <title> 내 대괄호 안 텍스트 추출 (예: [경제])
        import re
        page_title = (soup.title.string or soup.select_one("title").get_text(strip=True)) if (soup.title or soup.select_one("title")) else ""
        bracket_texts = re.findall(r"\[([^\]]+)\]", page_title)
        category = bracket_texts[0].strip() if bracket_texts else ""

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
        email_from_marker = self._extract_after_marker(full_text, "[메일]")

        # 기자명/기자이메일 추출: 콘텐츠 내 "당신의 제보가 뉴스가 됩니다" 문구 앞에서
        reporter_name, reporter_email = self._parse_reporter_from_content(content_text)
        if not reporter_email:
            reporter_email = email_from_marker

        # 추가 규칙 1: "제작 | 이름" 또는 "제작 : 이름" 패턴에서 이름 추출
        if not reporter_name:
            prod_name = self._extract_name_after_production_marker(full_text)
            if prod_name:
                reporter_name = prod_name

        # 추가 규칙 2: "대담 발췌 : 이름" 또는 "대담 발췌 | 이름" 패턴에서 이름 추출
        if not reporter_name:
            excerpt_name = self._extract_name_after_interview_excerpt_marker(full_text)
            if excerpt_name:
                reporter_name = excerpt_name

        return {
            "published_at": published_at,
            "content": content_text,
            "phone": phone,
            "email": reporter_email,
            "reporter_name": reporter_name,
            "category": category,
        }

    @staticmethod
    def _extract_after_marker(text: str, marker: str) -> str:
        import re
        # capture everything after marker up to a line break
        # e.g., "[전화] 02-398-8585" -> "02-398-8585"
        pattern = re.compile(re.escape(marker) + r"\s*([^\n\r<]+)")
        m = pattern.search(text)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _parse_reporter_from_content(text: str) -> (str, str):
        """Extract reporter name and email from a snippet like
        "YTN 홍길동 (hong@ytn.co.kr)" that appears before the marker
        "당신의 제보가 뉴스가 됩니다". Returns (name, email) or ("", "").
        """
        if not text:
            return "", ""
        marker = "당신의 제보가 뉴스가 됩니다"
        segment = text
        idx = text.find(marker)
        if idx != -1:
            segment = text[:idx]
        import re
        # Find the last occurrence to avoid earlier unrelated matches
        pattern = re.compile(r"YTN\s+([^()\n\r]+?)\s*\(([^)\s]+@[^)\s]+)\)")
        matches = list(pattern.finditer(segment))
        if not matches:
            return "", ""
        last = matches[-1]
        name = last.group(1).strip()
        email = last.group(2).strip()
        return name, email

    @staticmethod
    def _extract_name_after_production_marker(text: str) -> str:
        """Extract a name after a production marker like "제작 | 이름" or "제작 : 이름".
        Returns the captured name or an empty string if not found.
        """
        if not text:
            return ""
        import re
        m = re.search(r"제작\s*[|:]\s*([^\n\r]+)", text)
        return m.group(1).strip() if m else ""

    @staticmethod
    def _extract_name_after_interview_excerpt_marker(text: str) -> str:
        """Extract a name after an interview excerpt marker like
        "대담 발췌 : 이름" or "대담 발췌 | 이름".
        """
        if not text:
            return ""
        import re
        m = re.search(r"대담\s*발췌\s*[|:]\s*([^\n\r]+)", text)
        return m.group(1).strip() if m else ""