from typing import Any, Dict, Optional

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
)


class NewsEditorDialog(QDialog):
    def __init__(self, parent=None, initial: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("News Editor")
        self.inputs: Dict[str, Any] = {}

        form = QFormLayout(self)
        self.title = QLineEdit()
        self.category = QLineEdit()
        self.published_at = QLineEdit()
        self.reporter_name = QLineEdit()
        self.reporter_email = QLineEdit()
        self.source_url = QLineEdit()
        self.blog_url = QLineEdit()
        self.status = QLineEdit()
        self.content = QTextEdit()

        form.addRow("Title", self.title)
        form.addRow("Category", self.category)
        form.addRow("Published At", self.published_at)
        form.addRow("Reporter Name", self.reporter_name)
        form.addRow("Reporter Email", self.reporter_email)
        form.addRow("Source URL", self.source_url)
        form.addRow("Blog URL", self.blog_url)
        form.addRow("Status", self.status)
        form.addRow("Content", self.content)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

        if initial:
            self.title.setText(initial.get("title", ""))
            self.category.setText(initial.get("category", ""))
            self.published_at.setText(initial.get("published_at", ""))
            self.reporter_name.setText(initial.get("reporter_name", ""))
            self.reporter_email.setText(initial.get("reporter_email", ""))
            self.source_url.setText(initial.get("source_url", ""))
            self.blog_url.setText(initial.get("blog_url", ""))
            self.status.setText(initial.get("status", ""))
            self.content.setPlainText(initial.get("content", ""))

    def get_data(self) -> Dict[str, Any]:
        return {
            "title": self.title.text().strip(),
            "category": self.category.text().strip(),
            "published_at": self.published_at.text().strip(),
            "reporter_name": self.reporter_name.text().strip(),
            "reporter_email": self.reporter_email.text().strip(),
            "source_url": self.source_url.text().strip(),
            "blog_url": self.blog_url.text().strip(),
            "status": self.status.text().strip(),
            "content": self.content.toPlainText().strip(),
        }







class NewsViewerDialog(QDialog):
    def __init__(self, parent=None, initial: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("News Details")

        form = QFormLayout(self)

        self.title = QLineEdit()
        self.title.setReadOnly(True)
        self.category = QLineEdit()
        self.category.setReadOnly(True)
        self.published_at = QLineEdit()
        self.published_at.setReadOnly(True)
        self.reporter_name = QLineEdit()
        self.reporter_name.setReadOnly(True)
        self.reporter_email = QLineEdit()
        self.reporter_email.setReadOnly(True)
        self.email = QLineEdit()
        self.email.setReadOnly(True)
        self.phone = QLineEdit()
        self.phone.setReadOnly(True)
        self.source_url = QLineEdit()
        self.source_url.setReadOnly(True)
        self.blog_url = QLineEdit()
        self.blog_url.setReadOnly(True)
        self.status = QLineEdit()
        self.status.setReadOnly(True)
        self.content = QTextEdit()
        self.content.setReadOnly(True)

        form.addRow("Title", self.title)
        form.addRow("Category", self.category)
        form.addRow("Published At", self.published_at)
        form.addRow("Reporter Name", self.reporter_name)
        form.addRow("Reporter Email", self.reporter_email)
        form.addRow("Email", self.email)
        form.addRow("Phone", self.phone)
        form.addRow("Source URL", self.source_url)
        form.addRow("Blog URL", self.blog_url)
        form.addRow("Status", self.status)
        form.addRow("Content", self.content)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        form.addRow(buttons)

        initial = initial or {}
        self.title.setText(initial.get("title", ""))
        self.category.setText(initial.get("category", ""))
        self.published_at.setText(initial.get("published_at", ""))
        self.reporter_name.setText(initial.get("reporter_name", ""))
        self.reporter_email.setText(initial.get("reporter_email", ""))
        self.email.setText(initial.get("email", ""))
        self.phone.setText(initial.get("phone", ""))
        self.source_url.setText(initial.get("source_url", ""))
        self.blog_url.setText(initial.get("blog_url", ""))
        self.status.setText(initial.get("status", ""))
        self.content.setPlainText(initial.get("content", ""))

