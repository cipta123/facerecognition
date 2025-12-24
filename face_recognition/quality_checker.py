"""
Quality Control (QC) untuk Face Recognition.

Dual mode:
- Strict (Database / registrasi / batch encoder): sangat ketat untuk kualitas data permanen.
- Lightweight (Real-time): lebih toleran untuk UX, tapi tetap menolak kasus fatal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, List

import cv2
import numpy as np

from face_recognition.config import (
    QC_ENABLED,
    QC_DB_BLUR_THRESHOLD,
    QC_DB_MIN_FACE_SIZE_RATIO,
    QC_DB_MAX_YAW_THRESHOLD,
    QC_DB_MIN_DETECTION_CONFIDENCE,
    QC_DB_REJECT_MULTIPLE_FACES,
    QC_RT_BLUR_THRESHOLD,
    QC_RT_MIN_FACE_SIZE_RATIO,
    QC_RT_MAX_YAW_THRESHOLD,
    QC_RT_MIN_DETECTION_CONFIDENCE,
    QC_RT_REJECT_MULTIPLE_FACES,
)


QC_USER_MESSAGES: Dict[str, str] = {
    "no_face": "Wajah tidak terdeteksi. Pastikan wajah terlihat jelas.",
    "multiple_faces": "Harap satu wajah saja.",
    "face_too_small": "Mendekatlah ke kamera.",
    "blurry": "Wajah kurang jelas (blur). Coba lagi.",
    "low_confidence": "Wajah tidak terdeteksi dengan jelas. Perbaiki pencahayaan/posisi.",
    "pose_extreme": "Hadapkan wajah ke kamera.",
}

# Severity mapping: info (biru), warning (kuning), error (merah)
QC_SEVERITY: Dict[str, str] = {
    "no_face": "error",
    "multiple_faces": "error",
    "face_too_small": "warning",
    "blurry": "warning",
    "low_confidence": "warning",
    "pose_extreme": "warning",
    "ok": "info",
}

# Hint messages yang lebih spesifik
QC_HINTS: Dict[str, str] = {
    "no_face": "Pastikan wajah menghadap kamera dan terlihat jelas",
    "multiple_faces": "Hanya satu wajah yang boleh terlihat di frame",
    "face_too_small": "Dekatkan wajah ke kamera hingga wajah mengisi sebagian besar frame",
    "blurry": "Hindari gerakan, pastikan fokus kamera jelas",
    "low_confidence": "Perbaiki pencahayaan dan pastikan wajah menghadap kamera",
    "pose_extreme": "Hadapkan wajah lurus ke kamera, hindari menengok ke samping",
    "ok": "Kualitas baik",
}


def _to_int_bbox(bbox: Any) -> Tuple[int, int, int, int]:
    arr = np.array(bbox).astype(int).tolist()
    return int(arr[0]), int(arr[1]), int(arr[2]), int(arr[3])


def _safe_crop(image_bgr: np.ndarray, bbox: Any) -> Optional[np.ndarray]:
    h, w = image_bgr.shape[:2]
    x1, y1, x2, y2 = _to_int_bbox(bbox)
    x1 = max(0, min(w - 1, x1))
    y1 = max(0, min(h - 1, y1))
    x2 = max(0, min(w, x2))
    y2 = max(0, min(h, y2))
    if x2 <= x1 or y2 <= y1:
        return None
    crop = image_bgr[y1:y2, x1:x2]
    if crop.size == 0:
        return None
    return crop


def is_blurry(face_crop_bgr: np.ndarray, threshold: float) -> Tuple[bool, float]:
    """Variance of Laplacian blur metric. Lower score = more blurry."""
    gray = cv2.cvtColor(face_crop_bgr, cv2.COLOR_BGR2GRAY)
    score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    return score < threshold, score


def face_size_ratio(image_bgr: np.ndarray, bbox: Any) -> float:
    h, w = image_bgr.shape[:2]
    x1, y1, x2, y2 = _to_int_bbox(bbox)
    face_area = max(0, x2 - x1) * max(0, y2 - y1)
    img_area = max(1, h * w)
    return float(face_area) / float(img_area)


def estimate_yaw_px(kps: Optional[Any]) -> Optional[float]:
    """
    Estimasi yaw sederhana dari 5-point landmarks (InsightFace: kps).
    yaw_px = abs(nose_x - eye_center_x)
    """
    if kps is None:
        return None
    pts = np.array(kps, dtype=np.float32)
    if pts.shape[0] < 3:
        return None
    left_eye = pts[0]
    right_eye = pts[1]
    nose = pts[2]
    eye_center_x = float((left_eye[0] + right_eye[0]) / 2.0)
    yaw = abs(float(nose[0]) - eye_center_x)
    return float(yaw)


def _multiple_faces_check(num_faces: int, reject_multiple: bool) -> Tuple[bool, str, Dict[str, Any]]:
    if num_faces == 0:
        return False, "no_face", {"num_faces": 0}
    if reject_multiple and num_faces > 1:
        return False, "multiple_faces", {"num_faces": num_faces}
    return True, "ok", {"num_faces": num_faces}


def quality_check_strict(
    image_bgr: np.ndarray,
    faces: List[Any],
) -> Tuple[bool, str, Dict[str, Any], Optional[Any]]:
    """
    QC ketat untuk database (batch encoder).
    Return: (ok, reason, details, selected_face)
    details sekarang include: severity, hint
    """
    if not QC_ENABLED:
        best = max(faces, key=lambda x: getattr(x, "det_score", 0.0)) if faces else None
        details = {"qc_enabled": False, "severity": "info", "hint": QC_HINTS.get("ok", "")}
        return True, "ok", details, best

    ok, reason, details = _multiple_faces_check(len(faces), QC_DB_REJECT_MULTIPLE_FACES)
    if not ok:
        details["severity"] = QC_SEVERITY.get(reason, "error")
        details["hint"] = QC_HINTS.get(reason, "")
        return False, reason, details, None

    face = faces[0] if len(faces) == 1 else max(faces, key=lambda x: x.det_score)
    bbox = getattr(face, "bbox", None)
    kps = getattr(face, "kps", None)
    det_score = float(getattr(face, "det_score", 0.0))

    # Confidence check
    if det_score < QC_DB_MIN_DETECTION_CONFIDENCE:
        details = {"det_score": det_score, "min": QC_DB_MIN_DETECTION_CONFIDENCE}
        details["severity"] = QC_SEVERITY.get("low_confidence", "warning")
        details["hint"] = QC_HINTS.get("low_confidence", "")
        return False, "low_confidence", details, face

    # Face size check
    ratio = face_size_ratio(image_bgr, bbox)
    if ratio < QC_DB_MIN_FACE_SIZE_RATIO:
        details = {"ratio": ratio, "min_ratio": QC_DB_MIN_FACE_SIZE_RATIO}
        details["severity"] = QC_SEVERITY.get("face_too_small", "warning")
        details["hint"] = QC_HINTS.get("face_too_small", "")
        return False, "face_too_small", details, face

    # Blur check (strict)
    crop = _safe_crop(image_bgr, bbox)
    if crop is None:
        details = {"reason": "invalid_crop"}
        details["severity"] = QC_SEVERITY.get("face_too_small", "warning")
        details["hint"] = QC_HINTS.get("face_too_small", "")
        return False, "face_too_small", details, face
    blurry, blur_score = is_blurry(crop, QC_DB_BLUR_THRESHOLD)
    if blurry:
        details = {"blur_score": blur_score, "min": QC_DB_BLUR_THRESHOLD}
        details["severity"] = QC_SEVERITY.get("blurry", "warning")
        details["hint"] = QC_HINTS.get("blurry", "")
        return False, "blurry", details, face

    # Pose check (strict)
    yaw_px = estimate_yaw_px(kps)
    if yaw_px is not None and yaw_px > QC_DB_MAX_YAW_THRESHOLD:
        details = {"yaw_px": yaw_px, "max": QC_DB_MAX_YAW_THRESHOLD}
        details["severity"] = QC_SEVERITY.get("pose_extreme", "warning")
        details["hint"] = QC_HINTS.get("pose_extreme", "")
        return False, "pose_extreme", details, face

    details = {"det_score": det_score, "ratio": ratio, "blur_score": blur_score, "yaw_px": yaw_px}
    details["severity"] = QC_SEVERITY.get("ok", "info")
    details["hint"] = QC_HINTS.get("ok", "")
    return True, "ok", details, face


def quality_check_lightweight(
    image_bgr: np.ndarray,
    faces: List[Any],
) -> Tuple[bool, str, Dict[str, Any], Optional[Any]]:
    """
    QC ringan untuk real-time recognition.
    Return: (ok, reason, details, selected_face)
    Note: pose_extreme tidak otomatis reject; hanya warning.
    details sekarang include: severity, hint
    """
    if not QC_ENABLED:
        best = max(faces, key=lambda x: getattr(x, "det_score", 0.0)) if faces else None
        details = {"qc_enabled": False, "severity": "info", "hint": QC_HINTS.get("ok", "")}
        return True, "ok", details, best

    ok, reason, details = _multiple_faces_check(len(faces), QC_RT_REJECT_MULTIPLE_FACES)
    if not ok:
        details["severity"] = QC_SEVERITY.get(reason, "error")
        details["hint"] = QC_HINTS.get(reason, "")
        return False, reason, details, None

    face = faces[0] if len(faces) == 1 else max(faces, key=lambda x: x.det_score)
    bbox = getattr(face, "bbox", None)
    kps = getattr(face, "kps", None)
    det_score = float(getattr(face, "det_score", 0.0))

    # Confidence check (real-time)
    if det_score < QC_RT_MIN_DETECTION_CONFIDENCE:
        details = {"det_score": det_score, "min": QC_RT_MIN_DETECTION_CONFIDENCE}
        details["severity"] = QC_SEVERITY.get("low_confidence", "warning")
        details["hint"] = QC_HINTS.get("low_confidence", "")
        return False, "low_confidence", details, face

    # Face size check (real-time)
    ratio = face_size_ratio(image_bgr, bbox)
    if ratio < QC_RT_MIN_FACE_SIZE_RATIO:
        details = {"ratio": ratio, "min_ratio": QC_RT_MIN_FACE_SIZE_RATIO}
        details["severity"] = QC_SEVERITY.get("face_too_small", "warning")
        details["hint"] = QC_HINTS.get("face_too_small", "")
        return False, "face_too_small", details, face

    # Blur check (real-time)
    crop = _safe_crop(image_bgr, bbox)
    if crop is None:
        details = {"reason": "invalid_crop"}
        details["severity"] = QC_SEVERITY.get("face_too_small", "warning")
        details["hint"] = QC_HINTS.get("face_too_small", "")
        return False, "face_too_small", details, face
    blurry, blur_score = is_blurry(crop, QC_RT_BLUR_THRESHOLD)
    if blurry:
        details = {"blur_score": blur_score, "min": QC_RT_BLUR_THRESHOLD}
        details["severity"] = QC_SEVERITY.get("blurry", "warning")
        details["hint"] = QC_HINTS.get("blurry", "")
        return False, "blurry", details, face

    # Pose check (real-time) - tolerant: warning only
    yaw_px = estimate_yaw_px(kps)
    pose_warning = False
    if yaw_px is not None and yaw_px > QC_RT_MAX_YAW_THRESHOLD:
        pose_warning = True

    details = {"det_score": det_score, "ratio": ratio, "blur_score": blur_score, "yaw_px": yaw_px, "pose_warning": pose_warning}
    details["severity"] = "info" if not pose_warning else "warning"
    details["hint"] = QC_HINTS.get("ok", "") if not pose_warning else QC_HINTS.get("pose_extreme", "")
    return True, "ok", details, face


def user_message_for_reason(reason: str) -> str:
    return QC_USER_MESSAGES.get(reason, "Frame kurang baik, coba lagi.")


