"""
Pillar 10: Multimodal Vision & Image Scene Understanding Engine.
Safe imports with fallbacks for Pillow and OpenCV.
"""

import os
import io
import re
import uuid
import base64
from typing import Dict, Any, List, Optional

try:
    from PIL import Image, ImageStat
except ImportError:
    Image = None
    ImageStat = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from config import IMAGES_DIR

class VisionImageAnalyzer:
    def __init__(self, upload_dir: Optional[str] = None):
        self.upload_dir = upload_dir or IMAGES_DIR
        os.makedirs(self.upload_dir, exist_ok=True)

    def extract_color_palette(self, pil_img, num_colors: int = 4) -> List[Dict[str, Any]]:
        try:
            small = pil_img.resize((80, 80)).convert("RGB")
            colors = small.getcolors(10000)
            if colors:
                sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)[:num_colors]
                total = sum(c[0] for c in sorted_colors) or 1
                palette = []
                for count, rgb in sorted_colors:
                    hex_val = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                    pct = round((count / total) * 100, 1)
                    palette.append({"hex": hex_val, "rgb": rgb, "percentage": pct})
                return palette
        except Exception:
            pass
        return [{"hex": "#1a1a2e", "percentage": 100}]

    def analyze_image(self, filename: str, image_bytes: bytes) -> Dict[str, Any]:
        """Analyzes image, extracts visual features, and generates clean multimodal payload."""
        os.makedirs(self.upload_dir, exist_ok=True)
        
        clean_basename = re.sub(r'[^a-zA-Z0-9._-]', '_', os.path.basename(filename)) or "image.png"
        file_uuid = uuid.uuid4().hex[:12]
        secure_filename = f"img_{file_uuid}_{clean_basename}"
        file_path = os.path.join(self.upload_dir, secure_filename)

        try:
            with open(file_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            print(f"[VisionAnalyzer] Error saving image to disk: {e}")

        width, height = 400, 300
        format_name = "JPEG"
        data_uri = ""
        palette_desc = "#1e293b (100%)"
        scene_type = "Image / Graphic"
        aspect_ratio = 1.33
        orientation = "landscape"
        significant_contours_count = 1

        if Image is not None:
            try:
                img = Image.open(io.BytesIO(image_bytes))
                width, height = img.size
                format_name = (img.format or "JPEG").upper()
                if format_name not in ("JPEG", "PNG", "WEBP"):
                    format_name = "JPEG"

                rgb_img = img.convert("RGB")
                stat = ImageStat.Stat(rgb_img)
                mean_brightness = sum(stat.mean) / 3.0
                
                palette = self.extract_color_palette(rgb_img)
                palette_desc = ", ".join([f"{c['hex']} ({c['percentage']}%)" for c in palette[:3]])

                aspect_ratio = round(width / (height or 1), 2)
                orientation = "landscape" if aspect_ratio > 1.2 else ("portrait" if aspect_ratio < 0.8 else "square")

                # Optimize image size for LLM tokens (max 512px)
                opt_img = rgb_img.copy()
                opt_img.thumbnail((512, 512), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                opt_img.save(buf, format="JPEG", quality=75, optimize=True)
                img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{img_b64}"

                if cv2 is not None and np is not None:
                    cv_img = cv2.cvtColor(np.array(rgb_img), cv2.COLOR_RGB2BGR)
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    edges = cv2.Canny(gray, 50, 150)
                    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    significant_contours_count = len([c for c in contours if cv2.contourArea(c) > 200])

                if "screenshot" in clean_basename.lower() or "chatgpt" in clean_basename.lower():
                    scene_type = "Software UI / App Screenshot"
                elif mean_brightness < 80:
                    scene_type = "Dark-Mode Interface / Low-Light Scene"
                else:
                    scene_type = "Photo / Visual Media"

            except Exception as img_err:
                print(f"[VisionAnalyzer] Error processing image: {img_err}")
                img_b64 = base64.b64encode(image_bytes).decode("utf-8")
                data_uri = f"data:image/jpeg;base64,{img_b64}"
        else:
            img_b64 = base64.b64encode(image_bytes).decode("utf-8")
            data_uri = f"data:image/jpeg;base64,{img_b64}"

        visual_summary = (
            f"Image '{clean_basename}' ({width}×{height}px, {orientation}): "
            f"Scene type: {scene_type}. Dominant palette: {palette_desc}."
        )

        return {
            "filename": clean_basename,
            "secure_filename": secure_filename,
            "file_path": file_path,
            "width": width,
            "height": height,
            "format": format_name,
            "scene_type": scene_type,
            "orientation": orientation,
            "aspect_ratio": aspect_ratio,
            "data_uri": data_uri,
            "summary": visual_summary
        }
