import os

from PIL import ExifTags, Image

from src.utils.logging_config import setup_logger
from src.utils.project_path import get_project_root

logger = setup_logger(__name__)


def optimize_image_for_vlm(image_path: str, max_size: int = 1024) -> str:
    """
    Resizes image to max_size while maintaining aspect ratio, fixes EXIF orientation,
    and normalizes format to optimize VRAM and inference speed.
    """
    if not os.path.exists(image_path):
        return image_path

    try:
        with Image.open(image_path) as img:
            # 1. Fix EXIF Orientation
            try:
                orientation = next(
                    (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
                )
                if orientation is None:
                    raise KeyError("Orientation tag not found")

                exif_data = img.getexif()
                if not exif_data:
                    raise KeyError("No EXIF")
                exif = dict(exif_data.items())

                if exif.get(orientation) == 3:
                    img = img.rotate(180, expand=True)
                elif exif.get(orientation) == 6:
                    img = img.rotate(270, expand=True)
                elif exif.get(orientation) == 8:
                    img = img.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                # No EXIF or no orientation tag
                pass

            # 2. Resize if needed
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                img = img.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"ImageOptimizer: Resized to {new_size}")

            # 3. Normalize & Save (Always save to cache to ensure .jpg format)
            scratch_dir = os.path.join(get_project_root(), "scratch", "vision_cache")
            os.makedirs(scratch_dir, exist_ok=True)

            base_name = os.path.basename(image_path)
            file_root, _ = os.path.splitext(base_name)
            optimized_path = os.path.join(scratch_dir, f"opt_{file_root}.jpg")

            # Convert to RGB if necessary (e.g. for PNG with alpha)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            img.save(optimized_path, "JPEG", quality=85, optimize=True)
            logger.info(f"ImageOptimizer: {base_name} optimized to {optimized_path}")
            return optimized_path
    except Exception as e:
        logger.error(f"ImageOptimizer: Failed to optimize {image_path} ({e})")
        return image_path
