from datetime import datetime

from pydantic import BaseModel


class GenerationRequestCreate(BaseModel):
    model_id: int
    prompt: str
    aspect_ratio: str | None = None
    style: str | None = None


class GenerationRequestOut(BaseModel):
    id: int
    user_id: int
    model_id: int
    prompt: str
    status: str
    aspect_ratio: str | None = None
    style: str | None = None
    references_count: int
    cost: int | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class GenerationReferenceOut(BaseModel):
    id: int
    request_id: int
    telegram_file_id: str | None = None
    url: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerationResultOut(BaseModel):
    id: int
    request_id: int
    telegram_file_id: str | None = None
    image_url: str | None = None
    seed: int | None = None
    duration_ms: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class GenerationJobOut(BaseModel):
    id: int
    request_id: int
    provider: str
    status: str
    provider_job_id: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class TrialUseOut(BaseModel):
    id: int
    user_id: int
    request_id: int | None = None
    used_at: datetime

    class Config:
        from_attributes = True
