from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.deps.wavespeed import wavespeed_client
from app.schemas.media import MediaUploadOut

router = APIRouter()


@router.post("/media/upload", response_model=MediaUploadOut)
async def upload_media(file: UploadFile = File(...)) -> MediaUploadOut:
    try:
        client = wavespeed_client()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        response = await client.upload_media_binary(
            file_bytes=content,
            filename=file.filename or "upload.bin",
            content_type=file.content_type,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Wavespeed upload failed") from exc
    download_url = response.data.get("download_url")
    if not download_url:
        raise HTTPException(status_code=502, detail="Upload failed")

    return MediaUploadOut(
        download_url=str(download_url),
        filename=str(response.data.get("filename") or file.filename or ""),
        size=int(response.data.get("size") or 0),
    )
