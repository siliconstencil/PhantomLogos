import os
from PIL import Image, ExifTags
from src.utils.logging_config import setup_logger

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
                for orientation in ExifTags.TAGS.keys():
                    if ExifTags.TAGS[orientation] == 'Orientation':
                        break
                exif = dict(img._getexif().items())

                if exif[orientation] == 3:
                    img = img.rotate(180, expand=True)
                elif exif[orientation] == 6:
                    img = img.rotate(270, expand=True)
                elif exif[orientation] == 8:
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
            scratch_dir = os.path.join(os.getcwd(), "scratch", "vision_cache")
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
