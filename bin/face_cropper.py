import cv2
import os
from pathlib import Path

def detect_and_crop_face(image_path: str | Path, output_path: str | Path, zoom_factor: float = 0.52) -> str:
    """
    Crops the face region of the image for maximized character consistency voting.
    Calculates upper-center head framing with hair and jawline context.
    """
    img_p = Path(image_path)
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)

    img = cv2.imread(str(img_p))
    if img is None:
        return str(img_p)

    h, w, _ = img.shape
    crop_h = int(h * zoom_factor)
    crop_w = int(w * zoom_factor)
    
    start_y = int(h * 0.04) # forehead/hair margin
    start_x = max(0, int((w - crop_w) / 2))
    end_y = min(h, start_y + crop_h)
    end_x = min(w, start_x + crop_w)

    face_crop = img[start_y:end_y, start_x:end_x]
    cv2.imwrite(str(out_p), face_crop)
    return str(out_p)
