import io
from typing import Dict, Any, Optional

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image


_mp_pose = mp.solutions.pose


def _dist(a, b):
    return float(np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float)))


def _point(lms, idx):
    lm = lms[idx]
    return (lm.x, lm.y, lm.visibility)


def _visible(lms, idx, threshold=0.55):
    return lms[idx].visibility >= threshold


def _ratio_label(value: float, low: float, high: float, low_label: str, mid_label: str, high_label: str):
    if value < low:
        return low_label
    if value > high:
        return high_label
    return mid_label


def _decode_image(image_bytes: bytes):
    pil = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    rgb = np.array(pil)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return rgb, bgr


def _lighting_ok(bgr):
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    mean = float(gray.mean())
    return 45 <= mean <= 220, round(mean, 1)


def extract_local_visual_profile(image_bytes: bytes) -> Dict[str, Any]:
    rgb, bgr = _decode_image(image_bytes)
    lighting_ok, brightness = _lighting_ok(bgr)

    with _mp_pose.Pose(
        static_image_mode=True,
        model_complexity=1,
        enable_segmentation=False,
        min_detection_confidence=0.55,
    ) as pose:
        result = pose.process(rgb)

    if not result.pose_landmarks:
        return {
            "ok": False,
            "mode": "local_vision",
            "error": "未检测到稳定人体姿态，请确保身体进入画面并改善光线。",
            "profile": {
                "frame_quality": {
                    "full_body_visible": False,
                    "face_visible": False,
                    "feet_visible": False,
                    "lighting_ok": lighting_ok,
                    "camera_angle_ok": False,
                    "issues": ["未检测到完整人体姿态"],
                }
            },
        }

    lms = result.pose_landmarks.landmark
    P = _mp_pose.PoseLandmark

    required = {
        "nose": P.NOSE.value,
        "left_shoulder": P.LEFT_SHOULDER.value,
        "right_shoulder": P.RIGHT_SHOULDER.value,
        "left_hip": P.LEFT_HIP.value,
        "right_hip": P.RIGHT_HIP.value,
        "left_knee": P.LEFT_KNEE.value,
        "right_knee": P.RIGHT_KNEE.value,
        "left_ankle": P.LEFT_ANKLE.value,
        "right_ankle": P.RIGHT_ANKLE.value,
    }

    face_visible = _visible(lms, required["nose"])
    feet_visible = _visible(lms, required["left_ankle"]) and _visible(lms, required["right_ankle"])
    shoulders_visible = _visible(lms, required["left_shoulder"]) and _visible(lms, required["right_shoulder"])
    hips_visible = _visible(lms, required["left_hip"]) and _visible(lms, required["right_hip"])
    knees_visible = _visible(lms, required["left_knee"]) and _visible(lms, required["right_knee"])
    full_body_visible = face_visible and shoulders_visible and hips_visible and knees_visible and feet_visible

    ls = _point(lms, required["left_shoulder"])
    rs = _point(lms, required["right_shoulder"])
    lh = _point(lms, required["left_hip"])
    rh = _point(lms, required["right_hip"])
    la = _point(lms, required["left_ankle"])
    ra = _point(lms, required["right_ankle"])
    nose = _point(lms, required["nose"])

    shoulder_width = _dist(ls[:2], rs[:2])
    hip_width = max(_dist(lh[:2], rh[:2]), 1e-6)
    shoulder_hip_ratio = shoulder_width / hip_width

    mid_shoulder = ((ls[0] + rs[0]) / 2, (ls[1] + rs[1]) / 2)
    mid_hip = ((lh[0] + rh[0]) / 2, (lh[1] + rh[1]) / 2)
    mid_ankle = ((la[0] + ra[0]) / 2, (la[1] + ra[1]) / 2)

    torso_len = _dist(mid_shoulder, mid_hip)
    leg_len = _dist(mid_hip, mid_ankle)
    torso_leg_ratio = torso_len / max(leg_len, 1e-6)

    visible_y = [
        lm.y for lm in lms
        if lm.visibility >= 0.55 and -0.2 <= lm.y <= 1.2
    ]
    body_height = max(visible_y) - min(visible_y) if visible_y else 0.0
    shoulder_norm = shoulder_width / max(body_height, 1e-6)

    shoulder_width_impression = _ratio_label(
        shoulder_norm, 0.20, 0.28, "偏窄", "中等", "偏宽"
    )
    shoulder_to_waist_relation = _ratio_label(
        shoulder_hip_ratio, 1.05, 1.28, "接近髋宽", "肩部略宽", "肩部明显更宽"
    )
    torso_length_impression = _ratio_label(
        torso_leg_ratio, 0.43, 0.58, "偏短", "中等", "偏长"
    )
    leg_length_impression = (
        "偏长" if torso_leg_ratio < 0.43
        else "中等" if torso_leg_ratio <= 0.58
        else "偏短"
    )

    centered = abs(mid_shoulder[0] - mid_hip[0]) < 0.08
    camera_angle_ok = shoulders_visible and hips_visible and centered

    issues = []
    if not full_body_visible:
        issues.append("建议让头顶到脚部完整进入画面")
    if not lighting_ok:
        issues.append("光线偏暗或过曝")
    if not camera_angle_ok:
        issues.append("建议尽量正对镜头、自然站立")
    if not face_visible:
        issues.append("脸部未稳定识别")
    if not feet_visible:
        issues.append("脚部未完整识别")

    next_views = []
    if not full_body_visible:
        next_views.append("向后站，让头顶到脚完整入镜")
    if full_body_visible:
        next_views.append("保持自然正面站姿数个样本")
        next_views.append("再提供左/右侧面站姿，完善比例档案")

    profile = {
        "frame_quality": {
            "full_body_visible": full_body_visible,
            "face_visible": face_visible,
            "feet_visible": feet_visible,
            "lighting_ok": lighting_ok,
            "camera_angle_ok": camera_angle_ok,
            "issues": issues,
            "brightness_mean": brightness,
        },
        "face_and_head": {
            "face_shape": "",
            "face_length_impression": "",
            "jawline_impression": "",
            "forehead_visibility": "",
            "head_shape_notes": ["本地Lite版暂不对脸型做不可靠的单帧推断"],
            "confidence": 0.0,
        },
        "hair": {
            "length": "",
            "volume": "",
            "texture_impression": "",
            "current_shape": "",
            "styling_notes": ["本地Lite版暂不做发型语义识别"],
            "confidence": 0.0,
        },
        "body_proportions": {
            "shoulder_width_impression": shoulder_width_impression,
            "shoulder_to_waist_relation": shoulder_to_waist_relation,
            "torso_length_impression": torso_length_impression,
            "leg_length_impression": leg_length_impression,
            "head_to_body_ratio_impression": "",
            "overall_build_impression": "",
            "posture_notes": ["正面姿态较稳定" if camera_angle_ok else "当前姿态/角度可能影响比例判断"],
            "confidence": 0.82 if full_body_visible and camera_angle_ok else 0.58,
            "measurements": {
                "normalized_shoulder_width": round(shoulder_norm, 4),
                "shoulder_to_hip_ratio": round(shoulder_hip_ratio, 4),
                "torso_to_leg_ratio": round(torso_leg_ratio, 4),
            },
        },
        "clothing_fit_baseline": {
            "top_fit": "",
            "bottom_fit": "",
            "waist_position_impression": "",
            "hem_length_notes": [],
            "silhouette_notes": ["本地Lite版先建立人体比例基线，服装语义由高阶视觉模块补充"],
        },
        "style_relevant_summary": [
            f"肩部视觉：{shoulder_width_impression}",
            f"肩髋关系：{shoulder_to_waist_relation}",
            f"躯干长度：{torso_length_impression}",
            f"腿部长度：{leg_length_impression}",
        ],
        "recommended_next_views": next_views,
        "source": "local_mediapipe_pose",
    }

    return {
        "ok": True,
        "mode": "local_vision",
        "profile": profile,
    }
