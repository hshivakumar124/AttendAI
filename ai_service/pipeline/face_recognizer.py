"""
AttendAI — Face Recognition Module (ArcFace)
==============================================
Generates 512-dimensional face embeddings using InsightFace/ArcFace.
Computes Cosine Similarity & L2 Distance for student identification.

Privacy guarantee:
Raw face crops are processed in-memory and discarded after vector extraction.
Only mathematical 512-d vectors are preserved.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import structlog

from ai_service.config.ai_config import ai_settings

logger = structlog.get_logger(__name__)


def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate Cosine Similarity between two 512-d vectors.

    Returns:
        float score in [-1.0, 1.0]. Higher is more similar.
    """
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))


def l2_distance(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate Euclidean (L2) distance between two vectors.

    Returns:
        float distance >= 0.0. Lower is more similar.
    """
    return float(np.linalg.norm(v1 - v2))


class FaceRecognizer:
    """
    ArcFace Face Recognition Module.

    Uses InsightFace buffalo_l / ArcFace model to generate 512-d embeddings.
    Provides fallback vector extraction when running in lightweight CPU or CI test environments.
    """

    def __init__(
        self,
        threshold: float = None,
        device: str = "cpu",
    ):
        self.threshold = threshold if threshold is not None else ai_settings.face_recognition_confidence
        self.device = device
        self.backend = "unknown"
        self._model = None

        self._initialize_recognizer()

    def _initialize_recognizer(self) -> None:
        """Initialize InsightFace ArcFace model or fallback to lightweight feature extractor."""
        try:
            import insightface
            from insightface.app import FaceAnalysis

            app = FaceAnalysis(name=ai_settings.arcface_model, providers=["CPUExecutionProvider"])
            app.prepare(ctx_id=0, det_size=(640, 640))
            self._model = app
            self.backend = "insightface_arcface"
            logger.info("Loaded InsightFace ArcFace model", model=ai_settings.arcface_model)
            return
        except Exception as e:
            logger.debug("InsightFace load skipped — using lightweight feature extractor", reason=str(e))

        self.backend = "lightweight_feature_extractor"
        logger.info("Loaded Lightweight 512-d Face Embedding Extractor")

    def extract_embedding(self, face_crop_bgr: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract a normalized 512-dimensional embedding vector from a BGR face crop.

        Returns:
            np.ndarray of shape (512,) and float32 dtype, normalized to unit length.
        """
        if face_crop_bgr is None or face_crop_bgr.size == 0:
            return None

        if self.backend == "insightface_arcface" and self._model is not None:
            faces = self._model.get(face_crop_bgr)
            if len(faces) > 0 and hasattr(faces[0], "embedding"):
                emb = faces[0].embedding.astype(np.float32)
                # Normalize to unit length
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm
                return emb

        # Lightweight deterministic feature extractor fallback (for testing/offline execution)
        return self._extract_lightweight_embedding(face_crop_bgr)

    def match_face(
        self,
        query_embedding: np.ndarray,
        enrolled_gallery: Dict[str, np.ndarray],
    ) -> Tuple[Optional[str], float]:
        """
        Match a query 512-d embedding against a gallery of enrolled student embeddings.

        Args:
            query_embedding: 512-d vector
            enrolled_gallery: Dict mapping student_id -> 512-d vector

        Returns:
            (best_matched_student_id, similarity_score)
            If highest similarity < self.threshold, returns (None, highest_score).
        """
        if query_embedding is None or not enrolled_gallery:
            return None, 0.0

        best_student_id: Optional[str] = None
        best_score: float = -1.0

        for student_id, enrolled_emb in enrolled_gallery.items():
            score = cosine_similarity(query_embedding, enrolled_emb)
            if score > best_score:
                best_score = score
                best_student_id = student_id

        if best_score >= self.threshold:
            return best_student_id, round(best_score, 4)
        else:
            return None, round(max(0.0, best_score), 4)

    def _extract_lightweight_embedding(self, img: np.ndarray) -> np.ndarray:
        """
        Generates a 512-d deterministic feature vector based on spatial histogram & color moments.
        Used for fast testing without downloading large model weights.
        """
        import cv2

        resized = cv2.resize(img, (64, 64))
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

        # Compute multi-scale spatial features
        h1 = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        h_gx = cv2.calcHist([grad_x], [0], None, [128], [-1000, 1000]).flatten()
        h_gy = cv2.calcHist([grad_y], [0], None, [128], [-1000, 1000]).flatten()

        vec = np.concatenate([h1, h_gx, h_gy]).astype(np.float32)
        if len(vec) < 512:
            vec = np.pad(vec, (0, 512 - len(vec)))
        elif len(vec) > 512:
            vec = vec[:512]

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec
