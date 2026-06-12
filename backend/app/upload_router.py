"""File upload API endpoints."""
from typing import List
from fastapi import APIRouter, UploadFile, HTTPException, Depends
from .auth import require_admin
from .upload import upload_product_images, validate_image, read_and_check_size, ensure_dirs

router = APIRouter()

ensure_dirs()


@router.post("/api/upload")
async def upload_files(
    files: List[UploadFile],
    product_slug: str = "",
    token=Depends(require_admin),
):
    """Upload product images. Returns list of generated paths (original + thumbnails)."""
    if not files:
        raise HTTPException(status_code=400, detail='没有上传文件')
    if len(files) > 10:
        raise HTTPException(status_code=400, detail='单次最多上传 10 个文件')

    if not product_slug:
        raise HTTPException(status_code=400, detail='请提供 product_slug 参数')

    results = await upload_product_images(files, product_slug)
    return {"uploaded": len(results), "files": results}


@router.post("/api/upload/single")
async def upload_single_file(
    file: UploadFile,
    destination: str = "products",
    token=Depends(require_admin),
):
    """Upload a single file to a specific destination folder."""
    from .upload import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
    from pathlib import Path
    import uuid

    validate_image(file)
    data = await read_and_check_size(file)

    dest_dir = UPLOAD_DIR / destination
    dest_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename or '').suffix.lower() or '.jpg'
    filename = f"{uuid.uuid4().hex}{ext}"
    out_path = dest_dir / filename
    out_path.write_bytes(data)

    relative_path = f"/uploads/{destination}/{filename}"
    return {"filename": filename, "path": relative_path}
