import os
import io
import uuid
from pathlib import Path
from typing import List, Tuple
from fastapi import UploadFile, HTTPException
from PIL import Image

UPLOAD_DIR = Path('/data/uploads') if os.path.isdir('/data') else Path(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'data', 'uploads'))
PRODUCT_UPLOAD_DIR = UPLOAD_DIR / 'products'
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
THUMB_SIZES = {
    'thumb': (150, 150),
    'medium': (600, 400),
    'large': (1200, 800),
}


def ensure_dirs():
    PRODUCT_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def validate_image(file: UploadFile) -> None:
    ext = Path(file.filename or '').suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f'不支持的图片格式: {ext}。仅支持 jpg, png, webp'
        )


async def read_and_check_size(file: UploadFile) -> bytes:
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail='文件大小超过 5MB 限制')
    return content


def generate_thumbnails(image_data: bytes, product_slug: str) -> dict:
    """Generate thumb/medium/large versions. Returns dict of size -> relative path."""
    img = Image.open(io.BytesIO(image_data))
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    result = {}
    for size_name, (w, h) in THUMB_SIZES.items():
        thumb_dir = PRODUCT_UPLOAD_DIR / size_name / product_slug
        thumb_dir.mkdir(parents=True, exist_ok=True)
        resized = img.copy()
        resized.thumbnail((w, h), Image.LANCZOS)
        out_path = thumb_dir / f'{uuid.uuid4().hex}.jpg'
        resized.save(str(out_path), 'JPEG', quality=85)
        result[size_name] = f'/uploads/products/{size_name}/{product_slug}/{out_path.name}'

    # Also save original
    orig_dir = PRODUCT_UPLOAD_DIR / 'original' / product_slug
    orig_dir.mkdir(parents=True, exist_ok=True)
    orig_path = orig_dir / f'{uuid.uuid4().hex}.jpg'
    img.save(str(orig_path), 'JPEG', quality=95)
    result['original'] = f'/uploads/products/original/{product_slug}/{orig_path.name}'

    return result


async def upload_product_images(
    files: List[UploadFile],
    product_slug: str,
) -> List[dict]:
    """Upload multiple images for a product. Returns list of size->path dicts."""
    ensure_dirs()
    results = []
    for file in files:
        validate_image(file)
        data = await read_and_check_size(file)
        paths = generate_thumbnails(data, product_slug)
        results.append(paths)
    return results
