from pydantic import BaseModel


class MediaUploadOut(BaseModel):
    download_url: str
    filename: str | None = None
    size: int | None = None
