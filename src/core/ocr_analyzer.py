# src/core/ocr_analyzer.py
"""
Advanced screen content analysis with OCR
"""

import os
import shutil
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

import cv2
import numpy as np
import pytesseract
import win32gui
from PIL import ImageGrab

from src.config.constants import DEFAULT_TESSERACT_PATH, CHANGE_THRESHOLD, TESSERACT_RATE_LIMIT_SECONDS, OCR_MAX_TEXT_LENGTH
from src.utils.logger import logger


class OCRAnalyzer:
    """Analyze screen content to understand what user is reading"""

    def __init__(self):
        self.last_text: str = ""
        self.content_type: str = "unknown"
        self.analysis_running: bool = False
        self.cache: Dict = {}
        self.last_capture_time: float = 0
        self.change_threshold: float = CHANGE_THRESHOLD
        self.ocr_enabled: bool = True

        # Configurable Tesseract path
        tesseract_path = os.getenv('TESSERACT_PATH', DEFAULT_TESSERACT_PATH)
        if shutil.which(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.info(f"Tesseract found at {tesseract_path}")
        else:
            logger.warning(f"Tesseract not found at {tesseract_path}. Disabling OCR.")
            self.ocr_enabled = False

    def capture_window(self, hwnd: int) -> Optional[np.ndarray]:
        """Capture window content as image"""
        try:
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)
            width = right - left
            height = bottom - top

            img = ImageGrab.grab(bbox=(left, top, right, bottom))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"Failed to capture window {hwnd}: {e}")
            return None

    def extract_text(self, hwnd: int) -> str:
        """Extract text from window using OCR"""
        img = self.capture_window(hwnd)
        if img is None:
            return ""

        # Preprocess image
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]

        # OCR
        try:
            text = pytesseract.image_to_string(gray)
            self.last_text = text[:OCR_MAX_TEXT_LENGTH]
            return text
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def detect_content_type(self, text: str) -> str:
        """Detect what type of content user is viewing"""
        text_lower = text.lower()

        code_keywords = ["def ", "class ", "import ", "function", "var ", "const "]
        if any(kw in text_lower for kw in code_keywords):
            return "code"

        doc_keywords = ["documentation", "docs", "reference", "api"]
        if any(kw in text_lower for kw in doc_keywords):
            return "documentation"

        article_keywords = ["article", "blog", "post", "read more"]
        if any(kw in text_lower for kw in article_keywords):
            return "article"

        social_keywords = ["comment", "like", "share", "post", "friend"]
        if any(kw in text_lower for kw in social_keywords):
            return "social"

        email_keywords = ["inbox", "subject", "reply", "forward"]
        if any(kw in text_lower for kw in email_keywords):
            return "email"

        return "unknown"

    def _has_content_changed(self, new_text: str) -> bool:
        """Check if content has changed significantly"""
        if not self.last_text:
            return True

        old_words = set(self.last_text.lower().split())
        new_words = set(new_text.lower().split())

        if not old_words or not new_words:
            return len(new_text.strip()) > MIN_TEXT_LENGTH

        intersection = len(old_words.intersection(new_words))
        union = len(old_words.union(new_words))

        if union == 0:
            return False

        similarity = intersection / union
        return similarity < (1 - self.change_threshold)

    def classify_content(self, text: str) -> str:
        """Classify content type (alias for detect_content_type)"""
        return self.detect_content_type(text)

    def analyze(self, hwnd: int) -> Dict[str, Any]:
        """Full analysis of screen content with change detection"""
        if hwnd is None or hwnd == 0:
            return {
                "content_type": "unknown",
                "word_count": 0,
                "focus_adjustment": 0,
            }

        if not self.analysis_running:
            return {
                "content_type": "unknown",
                "word_count": 0,
                "focus_adjustment": 0,
            }

        if not self.ocr_enabled:
            return {
                "content_type": "unknown",
                "word_count": 0,
                "focus_adjustment": 0,
            }

        current_time = time.time()
        if current_time - self.last_capture_time < TESSERACT_RATE_LIMIT_SECONDS:
            return {
                "content_type": self.content_type,
                "word_count": len(self.last_text.split()),
                "focus_adjustment": 0,
            }

        text = self.extract_text(hwnd)

        if not self._has_content_changed(text):
            return {
                "content_type": self.content_type,
                "word_count": len(self.last_text.split()),
                "focus_adjustment": 0,
            }

        self.last_capture_time = current_time
        self.last_text = text
        self.content_type = self.detect_content_type(text)

        focus_adjustment = self.get_focus_adjustment(self.content_type)

        return {
            "text": text[:OCR_MAX_TEXT_LENGTH],
            "content_type": self.content_type,
            "has_code": "code" in self.content_type,
            "has_docs": "documentation" in self.content_type,
            "word_count": len(text.split()),
            "focus_adjustment": focus_adjustment,
            'raw_text_length': len(text),
        }

    def get_focus_adjustment(self, content_type: str) -> int:
        """Get focus adjustment based on content type"""
        adjustments = {
            "code": 15,
            "documentation": 10,
            "article": 5,
            "unknown": 0,
            "social": -20,
            "email": -5,
        }
        return adjustments.get(content_type, 0)

    def get_stats(self) -> Dict[str, Any]:
        """Get OCR statistics"""
        return {
            "last_content_type": self.content_type,
            "last_text_length": len(self.last_text),
            "cache_size": len(self.cache),
            "analysis_enabled": True,
        }

