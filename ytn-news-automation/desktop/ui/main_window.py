import os
import traceback
from datetime import datetime
from typing import Any, Dict, List

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication as QtApplication
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.firestore_manager import FirestoreManager
from ..core.crawler import YTNService
from ..core.blog_poster import NaverBlogPoster
from ..core.api_client import ApiClient
from .dialogs import NewsEditorDialog, NewsViewerDialog


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("YTN News Automation")
        self.resize(1200, 800)

        # Data
        self.firestore = FirestoreManager()
        self.api_client = ApiClient()
        self.crawler = YTNService()
        self.poster = NaverBlogPoster()

        # UI
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "title",
            "published_at",
            "email",
            "phone",
            "source_url",
            "status",
        ])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        

        # Controls
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search title...")
        self.btn_refresh = QPushButton("Refresh")
        self.btn_crawl = QPushButton("YTN 크롤링 실행")
        self.btn_post = QPushButton("네이버 블로그 포스팅")
        self.btn_create = QPushButton("Create")
        self.btn_read = QPushButton("Read")
        self.btn_update = QPushButton("Update")
        self.btn_delete = QPushButton("Delete")

        top_bar = QHBoxLayout()
        top_bar.addWidget(QLabel("검색:"))
        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_crawl)
        top_bar.addWidget(self.btn_post)
        top_bar.addStretch(1)
        top_bar.addWidget(self.btn_create)
        top_bar.addWidget(self.btn_read)
        top_bar.addWidget(self.btn_update)
        top_bar.addWidget(self.btn_delete)

        self.logs = QTextEdit()
        self.logs.setReadOnly(True)
        self.logs.setMinimumHeight(160)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addLayout(top_bar)
        layout.addWidget(self.table)
        layout.addWidget(QLabel("실행 로그"))
        layout.addWidget(self.logs)
        self.setCentralWidget(central)

        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Wire
        self.btn_refresh.clicked.connect(self.refresh_firestore)
        self.btn_crawl.clicked.connect(self.crawl_ytn_news)
        self.btn_post.clicked.connect(self.post_to_naver)
        self.btn_create.clicked.connect(self.create_news)
        self.btn_update.clicked.connect(self.update_news)
        self.btn_read.clicked.connect(self.read_news)
        self.btn_delete.clicked.connect(self.delete_news)
        self.search_input.textChanged.connect(self.apply_filter)

        self.refresh_firestore()

    # Utilities
    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")
        self.logs.ensureCursorVisible()

    def set_busy(self, busy: bool) -> None:
        for btn in [self.btn_refresh, self.btn_crawl, self.btn_post, self.btn_create, self.btn_read, self.btn_update, self.btn_delete]:
            btn.setEnabled(not busy)
        QtApplication.setOverrideCursor(Qt.WaitCursor if busy else Qt.ArrowCursor)

    # Data ops
    def refresh_news(self) -> None:
        try:
            self.set_busy(True)
            self.log("크롤링 시작...")
            items = self.crawler.fetch_latest(limit=10)
            self.populate_table_from_crawler(items)
            self.status.showMessage(f"Loaded {len(items)} crawler items", 3000)
            self.log(f"크롤링 완료: {len(items)}건")
        except Exception as exc:
            self.log(f"ERROR: Failed to load crawler data: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(exc))
        finally:
            self.set_busy(False)

    def refresh_firestore(self) -> None:
        try:
            self.set_busy(True)
            self.log("Firestore 불러오는 중...")
            items = self.firestore.list_news(limit=50)
            self.populate_table(items)
            self.status.showMessage(f"Loaded {len(items)} firestore items", 3000)
            self.log(f"불러오기 완료: {len(items)}건")
        except Exception as exc:
            self.log(f"ERROR: Firestore 로드 실패: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "Error", str(exc))
        finally:
            self.set_busy(False)

    def populate_table(self, items: List[Dict[str, Any]]) -> None:
        self.table.setRowCount(0)
        for item in items:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                item.get("title", ""),
                item.get("published_at", ""),
                item.get("email", ""),
                item.get("phone", ""),
                item.get("source_url", ""),
                item.get("status", ""),
            ]
            for col, value in enumerate(values):
                qitem = QTableWidgetItem(str(value))
                if col == 0 and item.get("id"):
                    qitem.setData(Qt.UserRole, item.get("id"))
                self.table.setItem(row, col, qitem)
        self.apply_filter()

    def populate_table_from_crawler(self, items: List[Dict[str, Any]]) -> None:
        mapped: List[Dict[str, Any]] = []
        for it in items:
            mapped.append({
                "title": it.get("title", ""),
                "published_at": it.get("published_at", ""),
                "email": it.get("email", ""),
                "phone": it.get("phone", ""),
                "source_url": it.get("link", ""),
                "status": it.get("status", "new"),
            })
        self.populate_table(mapped)


    def current_selection_id(self) -> str:
        row = self.table.currentRow()
        if row < 0:
            return ""
        first_col_item = self.table.item(row, 0)
        if not first_col_item:
            return ""
        doc_id = first_col_item.data(Qt.UserRole)
        return doc_id or ""

    def create_news(self) -> None:
        dialog = NewsEditorDialog(parent=self)
        if dialog.exec_() == dialog.Accepted:
            data = dialog.get_data()
            try:
                self.set_busy(True)
                doc_id = self.firestore.create_news(data)
                self.log(f"Created news: {doc_id}")
                self.refresh_firestore()
            except Exception as exc:
                self.log(f"ERROR: Create failed: {exc}")
                QMessageBox.critical(self, "Error", str(exc))
            finally:
                self.set_busy(False)

    def update_news(self) -> None:
        doc_id = self.current_selection_id()
        if not doc_id:
            QMessageBox.information(self, "Update", "Select a row first")
            return
        # Load existing
        item = self.firestore.get_news_by_id(doc_id)
        dialog = NewsEditorDialog(parent=self, initial=item)
        if dialog.exec_() == dialog.Accepted:
            data = dialog.get_data()
            try:
                self.set_busy(True)
                self.firestore.update_news(doc_id, data)
                self.log(f"Updated news: {doc_id}")
                self.refresh_firestore()
            except Exception as exc:
                self.log(f"ERROR: Update failed: {exc}")
                QMessageBox.critical(self, "Error", str(exc))
            finally:
                self.set_busy(False)

    def delete_news(self) -> None:
        doc_id = self.current_selection_id()
        if not doc_id:
            QMessageBox.information(self, "Delete", "Select a row first")
            return
        if QMessageBox.question(self, "Delete", "정말 삭제하시겠습니까?") != QMessageBox.Yes:
            return
        try:
            self.set_busy(True)
            self.firestore.delete_news(doc_id)
            self.log(f"Deleted: {doc_id}")
            self.refresh_firestore()
        except Exception as exc:
            self.log(f"ERROR: Delete failed: {exc}")
            QMessageBox.critical(self, "Error", str(exc))
        finally:
            self.set_busy(False)

    def read_news(self) -> None:
        doc_id = self.current_selection_id()
        if not doc_id:
            # Fallback: build from selected row values if no id (e.g., crawler view)
            row = self.table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Read", "Select a row first")
                return
            data = {
                "title": self.table.item(row, 0).text() if self.table.item(row, 0) else "",
                "published_at": self.table.item(row, 1).text() if self.table.item(row, 1) else "",
                "email": self.table.item(row, 2).text() if self.table.item(row, 2) else "",
                "phone": self.table.item(row, 3).text() if self.table.item(row, 3) else "",
                "source_url": self.table.item(row, 4).text() if self.table.item(row, 4) else "",
                "status": self.table.item(row, 5).text() if self.table.item(row, 5) else "",
            }
            NewsViewerDialog(self, initial=data).exec_()
            return

        try:
            self.set_busy(True)
            item = self.firestore.get_news_by_id(doc_id)
            NewsViewerDialog(self, initial=item).exec_()
        except Exception as exc:
            self.log(f"ERROR: Read failed: {exc}")
            QMessageBox.critical(self, "Error", str(exc))
        finally:
            self.set_busy(False)

    def crawl_ytn_news(self) -> None:
        try:
            self.set_busy(True)
            self.log("크롤링 시작...")
            items = self.crawler.fetch_latest(limit=10)
            self.log(f"크롤링 완료: {len(items)}건")
            # Save directly to Firestore
            saved = 0
            for it in items:
                source_url = it.get("link") or it.get("source_url") or ""
                data = {
                    "title": it.get("title", ""),
                    "published_at": it.get("published_at", ""),
                    "content": it.get("content", ""),
                    "email": it.get("email", ""),
                    "phone": it.get("phone", ""),
                    "source_url": source_url,
                    "status": "new",
                }
                if source_url:
                    self.firestore.upsert_by_source_url(source_url, data)
                else:
                    self.firestore.create_news(data)
                saved += 1
            self.log(f"Firestore 저장 완료: {saved}건")
            self.refresh_firestore()
        except Exception as exc:
            self.log(f"ERROR: 크롤링 실패: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "Crawling Error", str(exc))
        finally:
            self.set_busy(False)

    def post_to_naver(self) -> None:
        try:
            self.set_busy(True)
            self.log("네이버 블로그 포스팅 시작...")
            # Pick up to 3 items not posted yet
            items = [n for n in self.firestore.list_news(limit=50) if n.get("status") != "posted"][:3]
            results = self.poster.post_batch(items)
            # Update Firestore
            for doc_id, blog_url in results.items():
                self.firestore.update_news(doc_id, {"blog_url": blog_url, "status": "posted"})
            self.log(f"포스팅 완료: {len(results)}건")
            self.refresh_firestore()
        except Exception as exc:
            self.log(f"ERROR: 포스팅 실패: {exc}")
            traceback.print_exc()
            QMessageBox.critical(self, "Posting Error", str(exc))
        finally:
            self.set_busy(False)

    def apply_filter(self) -> None:
        text = (self.search_input.text() or "").strip().lower()
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            title = title_item.text().lower() if title_item else ""
            self.table.setRowHidden(row, text not in title)


