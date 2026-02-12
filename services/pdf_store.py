"""
Temporary in-memory PDF storage with auto-expiration.

Stores generated PDFs keyed by UUID so they can be served
via a public URL for a limited time (default: 30 minutes).
After expiration, PDFs are automatically cleaned up.

Architecture:
    - Dict-based storage: {uuid: {bytes, filename, created_at, expires_at}}
    - Background cleanup thread runs every 60 seconds
    - Thread-safe via threading.Lock
    - Max store size configurable to prevent memory exhaustion

Usage:
    store = PDFStore(ttl_minutes=30, max_items=100)
    pdf_id = store.save(pdf_bytes, filename)     # Returns UUID string
    entry = store.get(pdf_id)                     # Returns dict or None
    store.delete(pdf_id)                          # Manual cleanup
"""

import uuid
import threading
from datetime import datetime, timedelta, timezone
from typing import Optional


class PDFStore:
    """Thread-safe in-memory store for temporary PDF files."""

    def __init__(self, ttl_minutes: int = 30, max_items: int = 100):
        """
        Initialize the PDF store.

        Args:
            ttl_minutes: Time-to-live for each PDF in minutes.
                         After this time, the PDF is eligible for cleanup.
            max_items:   Maximum number of PDFs to store simultaneously.
                         Oldest entries are evicted when limit is reached.
        """
        self._store: dict[str, dict] = {}
        self._lock = threading.Lock()
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_items = max_items

        # Start background cleanup thread (daemon = dies with main process)
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="pdf-store-cleanup",
        )
        self._cleanup_thread.start()

    def save(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Store a PDF and return its unique ID.

        Args:
            pdf_bytes: Raw PDF file content.
            filename:  Original filename for Content-Disposition header.

        Returns:
            UUID string that can be used to retrieve the PDF.
        """
        pdf_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        with self._lock:
            # Evict oldest if at capacity
            if len(self._store) >= self._max_items:
                self._evict_oldest()

            self._store[pdf_id] = {
                "bytes": pdf_bytes,
                "filename": filename,
                "created_at": now.isoformat(),
                "expires_at": (now + self._ttl).isoformat(),
            }

        return pdf_id

    def get(self, pdf_id: str) -> Optional[dict]:
        """
        Retrieve a stored PDF by its ID.

        Returns None if the ID doesn't exist or the PDF has expired.

        Args:
            pdf_id: UUID string from save().

        Returns:
            Dict with keys: bytes, filename, created_at, expires_at
            or None if not found / expired.
        """
        with self._lock:
            entry = self._store.get(pdf_id)
            if entry is None:
                return None

            # Check expiration
            expires_at = datetime.fromisoformat(entry["expires_at"])
            if datetime.now(timezone.utc) > expires_at:
                del self._store[pdf_id]
                return None

            return entry

    def delete(self, pdf_id: str) -> bool:
        """
        Manually delete a stored PDF.

        Args:
            pdf_id: UUID string.

        Returns:
            True if the PDF was found and deleted, False otherwise.
        """
        with self._lock:
            if pdf_id in self._store:
                del self._store[pdf_id]
                return True
            return False

    @property
    def count(self) -> int:
        """Return the number of PDFs currently stored."""
        with self._lock:
            return len(self._store)

    def _evict_oldest(self):
        """Remove the oldest entry. Must be called with lock held."""
        if not self._store:
            return
        oldest_id = min(
            self._store,
            key=lambda k: self._store[k]["created_at"],
        )
        del self._store[oldest_id]

    def _cleanup_expired(self) -> int:
        """
        Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        now = datetime.now(timezone.utc)
        removed = 0

        with self._lock:
            expired_ids = [
                pid for pid, entry in self._store.items()
                if datetime.fromisoformat(entry["expires_at"]) < now
            ]
            for pid in expired_ids:
                del self._store[pid]
                removed += 1

        return removed

    def _cleanup_loop(self):
        """Background loop that runs cleanup every 60 seconds."""
        import time
        while True:
            time.sleep(60)
            try:
                self._cleanup_expired()
            except Exception:
                pass  # Don't crash the cleanup thread