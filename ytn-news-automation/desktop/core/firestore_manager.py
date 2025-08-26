import os
import sys
from typing import Any, Dict, List, Optional

import firebase_admin
from firebase_admin import credentials, firestore


class FirestoreManager:
    def __init__(self, collection_name: Optional[str] = None) -> None:
        self.collection_name = collection_name or os.getenv("FIRESTORE_COLLECTION", "news")
        if not firebase_admin._apps:
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            cred_path_env = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

            # Prefer explicitly provided file if present and exists
            if cred_path_env:
                abs_path = cred_path_env
                if not os.path.isabs(cred_path_env):
                    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                    abs_path = os.path.join(root, cred_path_env)
                if os.path.exists(abs_path):
                    cred = credentials.Certificate(abs_path)
                    firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
                else:
                    # If env var points to a missing file, unset it to avoid google.auth default error
                    try:
                        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
                    except KeyError:
                        pass

            # Try bundled or project-local default file path if present
            if not firebase_admin._apps:
                # When frozen, prefer bundled config under _MEIPASS
                base_dir = getattr(sys, "_MEIPASS", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
                default_abs = os.path.join(base_dir, "config", "serviceAccountKey.json")
                if os.path.exists(default_abs):
                    cred = credentials.Certificate(default_abs)
                    firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
                else:
                    # Fall back to Application Default Credentials on Cloud Run / GCE
                    firebase_admin.initialize_app(options={"projectId": project_id} if project_id else None)
        self.client = firestore.client()

    def _col(self):
        return self.client.collection(self.collection_name)

    def list_news(self, limit: int = 100) -> List[Dict[str, Any]]:
        docs = self._col().order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit).stream()
        items: List[Dict[str, Any]] = []
        for d in docs:
            data = d.to_dict() or {}
            data["id"] = d.id
            items.append(data)
        return items

    def get_news_by_id(self, doc_id: str) -> Dict[str, Any]:
        snap = self._col().document(doc_id).get()
        data = snap.to_dict() or {}
        data["id"] = doc_id
        return data

    def create_news(self, data: Dict[str, Any]) -> str:
        data = {**data}
        data.setdefault("status", "new")
        data.setdefault("created_at", firestore.SERVER_TIMESTAMP)
        data["updated_at"] = firestore.SERVER_TIMESTAMP
        ref = self._col().document()
        ref.set(data)
        return ref.id

    def update_news(self, doc_id: str, data: Dict[str, Any]) -> None:
        data = {**data}
        data["updated_at"] = firestore.SERVER_TIMESTAMP
        self._col().document(doc_id).set(data, merge=True)

    def delete_news(self, doc_id: str) -> None:
        self._col().document(doc_id).delete()

    def upsert_by_source_url(self, source_url: str, data: Dict[str, Any]) -> str:
        # Try match by source_url first when available
        normalized_url = (source_url or "").strip()
        if normalized_url:
            query = self._col().where("source_url", "==", normalized_url).limit(1).stream()
            docs = list(query)
            if docs:
                doc_id = docs[0].id
                self.update_news(doc_id, data)
                return doc_id

        # If not found by URL (or URL missing), attempt match by exact title
        title = (data.get("title") or "").strip()
        if title:
            title_query = self._col().where("title", "==", title).limit(1).stream()
            title_docs = list(title_query)
            if title_docs:
                doc_id = title_docs[0].id
                self.update_news(doc_id, data)
                return doc_id

        # Create new if no match found
        return self.create_news(data)






