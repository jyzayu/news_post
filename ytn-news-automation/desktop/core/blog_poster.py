import os
import re
from typing import Dict, List

from playwright.sync_api import sync_playwright


class NaverBlogPoster:
    def __init__(self) -> None:
        self.naver_id = os.getenv("NAVER_ID", "")
        self.naver_pw = os.getenv("NAVER_PW", "")

    def post_batch(self, items: List[Dict]) -> Dict[str, str]:
        if not self.naver_id or not self.naver_pw:
            raise RuntimeError("NAVER_ID/NAVER_PW not set")
        results: Dict[str, str] = {}    
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # Login
            page.goto("https://nid.naver.com/nidlogin.login", timeout=60000)
            page.fill("#id", self.naver_id)
            page.fill("#pw", self.naver_pw)
            page.click("#log\.login")
            page.wait_for_load_state("networkidle")

            for item in items[:3]:
                blog_url = self._post_single(page, item)
                if blog_url:
                    doc_id = item.get("id") or item.get("doc_id") or ""
                    if doc_id:
                        results[doc_id] = blog_url

            context.close()
            browser.close()
        return results

    def _post_single(self, page, item: Dict) -> str:
        title = item.get("title") or "제목 없음"
        content = item.get("content") or ""

        # Go to write form
        # page.goto(f"https://blog.naver.com/{self.naver_id}?Redirct=Write&", timeout=60000)
        page.goto("https://blog.naver.com/GoBlogWrite.naver", timeout=60000)

        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1000)
        try:
            frame_loc = page.frame_locator("#mainFrame")
            popup = frame_loc.locator("div.se-popup-alert-confirm").first
            if popup.count() > 0 and popup.is_visible():
                cancel_span = popup.locator("span.se-popup-button-text").filter(has_text=re.compile(r"^\s*취소\s*$"))
                if cancel_span.count() > 0 and cancel_span.last.is_visible():
                    cancel_span.last.locator("xpath=ancestor::button[1]").click()
        except Exception:
            # Fallback to main document
            try:
                popup_top = page.locator("div.se-popup-alert-confirm").first
                if popup_top.count() > 0 and popup_top.is_visible():
                    cancel_span_top = popup_top.locator("span.se-popup-button-text").filter(has_text=re.compile(r"^\s*취소\s*$"))
                    if cancel_span_top.count() > 0 and cancel_span_top.last.is_visible():
                        cancel_span_top.last.locator("xpath=ancestor::button[1]").click()
            except Exception:
                pass

        # Optionally close help panel if it appears; otherwise click 'Next'
        try:
            frame_loc = page.frame_locator("#mainFrame")
            help_panel = frame_loc.locator(".se-help-panel.se-is-on").first
            if help_panel.count() > 0 and help_panel.is_visible():
                close_btn = help_panel.locator("button.se-help-panel-close-button, .se-help-panel-close-button").first
                if close_btn.count() > 0 and close_btn.is_visible():
                    close_btn.click()
                else:
                    next_btn = help_panel.locator("button.slick-next").first
                    if next_btn.count() > 0 and next_btn.is_visible():
                        next_btn.click()
        except Exception:
            try:
                help_panel_top = page.locator(".se-help-panel.se-is-on").first
                if help_panel_top.count() > 0 and help_panel_top.is_visible():
                    close_btn_top = help_panel_top.locator("button.se-help-panel-close-button, .se-help-panel-close-button").first
                    if close_btn_top.count() > 0 and close_btn_top.is_visible():
                        close_btn_top.click()
                    else:
                        next_btn_top = help_panel_top.locator("button.slick-next").first
                        if next_btn_top.count() > 0 and next_btn_top.is_visible():
                            next_btn_top.click()
            except Exception:
                pass

        # The editor is an iframe-based editor; work inside #mainFrame first
        # Title
        try:
            page.wait_for_selector("#mainFrame", timeout=10000)
            frame_loc = page.frame_locator("#mainFrame")
            title_editable_iframe = frame_loc.locator("div.se-section-documentTitle [contenteditable='true']").first
            if title_editable_iframe.count() > 0:
                title_editable_iframe.click()
                title_editable_iframe.fill(title, timeout=5000)
            else:
                frame_loc.locator("span.se-placeholder:has-text('제목')").first.click()
                page.keyboard.insert_text(title)
        except Exception:
            try:
                # Fallback to main document if iframe path fails
                title_editable = page.locator("div.se-section-documentTitle [contenteditable='true']").first
                if title_editable.count() > 0:
                    title_editable.click()
                    title_editable.fill(title, timeout=5000)
                else:
                    placeholder = page.locator("span.se-placeholder:has-text('제목')").first
                    placeholder.click()
                    page.keyboard.insert_text(title)
            except Exception:
                try:
                    page.fill("input[placeholder='제목을 입력하세요']", title, timeout=5000)
                except Exception:
                    pass

        # Content - use placeholder span text then fallback to editor/contenteditable
        try:
            # Inside editor iframe first
            page.wait_for_selector("#mainFrame", timeout=10000)
            frame_loc = page.frame_locator("#mainFrame")
            content_editable_iframe = frame_loc.locator("div.se-section:not(.se-section-documentTitle) [contenteditable='true']").first
            if content_editable_iframe.count() > 0:
                content_editable_iframe.click()
                content_editable_iframe.fill(content, timeout=5000)
            else:
                frame_loc.locator("span.se-placeholder:has-text('최근 다녀온 곳을 지도와 함께 기록해보세요!')").first.click()
                page.keyboard.insert_text(content)
        except Exception:
            try:
                # Fallback to main document
                content_editable = page.locator("div.se-section:not(.se-section-documentTitle) [contenteditable='true']").first
                if content_editable.count() > 0:
                    content_editable.click()
                    content_editable.fill(content, timeout=5000)
                else:
                    page.locator("span.se-placeholder:has-text('최근 다녀온 곳을 지도와 함께 기록해보세요!')").first.click()
                    page.keyboard.insert_text(content)
            except Exception:
                try:
                    # Generic fallback: first contenteditable anywhere
                    page.locator("[contenteditable='true']").first.fill(content)
                except Exception:
                    try:
                        page.keyboard.insert_text(content)
                    except Exception:
                        pass

        # Publish - try inside #mainFrame first, then fallback to top document
        published_clicked = False
        try:
            page.wait_for_selector("#mainFrame", timeout=10000)
            frame_loc = page.frame_locator("#mainFrame")
            # First click the primary publish button in the toolbar area to open the layer
            try:
                pre_btn = frame_loc.locator("div.publish_btn_area__KjA2i button.publish_btn__m9KHH, [data-click-area='tpb.publish']").first
                if pre_btn.count() > 0 and pre_btn.is_visible():
                    pre_btn.click()
                    # Wait briefly for confirm layer/buttons
                    frame_loc.locator("[data-testid='seOnePublishBtn'], button.confirm_btn__WEaBq, [data-click-area='tpb*i.publish']").first.wait_for(state="visible", timeout=5000)
            except Exception:
                pass

            # Preferred selectors based on provided HTML for confirm publish
            btn_primary = frame_loc.locator('[data-testid="seOnePublishBtn"]').first
            if btn_primary.count() > 0:
                btn_primary.click()
                published_clicked = True
            else:
                btn_class = frame_loc.locator('button.confirm_btn__WEaBq').first
                if btn_class.count() > 0:
                    btn_class.click()
                    published_clicked = True
                else:
                    btn_data = frame_loc.locator('[data-click-area="tpb*i.publish"]').first
                    if btn_data.count() > 0:
                        btn_data.click()
                        published_clicked = True
                    else:
                        # Fallbacks inside iframe
                        btn = frame_loc.get_by_role("button", name="발행")
                        if btn.count() > 0:
                            btn.first.click()
                            published_clicked = True
                        else:
                            span_btn = frame_loc.locator("span:has-text('발행')").first
                            if span_btn.count() > 0:
                                span_btn.locator("xpath=ancestor::button[1]").click()
                                published_clicked = True
        except Exception:
            pass

        if not published_clicked:
            try:
                # Fallback to top document
                try:
                    pre_btn_top = page.locator("div.publish_btn_area__KjA2i button.publish_btn__m9KHH, [data-click-area='tpb.publish']").first
                    if pre_btn_top.count() > 0 and pre_btn_top.is_visible():
                        pre_btn_top.click()
                except Exception:
                    pass

                btn = page.get_by_role("button", name="발행")
                if btn.count() > 0:
                    btn.first.click()
                    published_clicked = True
                else:
                    span = page.locator("span:has-text('발행')").first
                    if span.count() > 0:
                        span.locator("xpath=ancestor::button[1]").click()
                        published_clicked = True
                    else:
                        page.click("text=발행", timeout=5000)
                        published_clicked = True
            except Exception:
                try:
                    page.click("text=등록", timeout=3000)
                except Exception:
                    pass

        # If a cancel button shows up inside the iframe after publish, click it

        # Try to get URL from address bar after publish
        try:
            return page.url
        except Exception:
            return ""

