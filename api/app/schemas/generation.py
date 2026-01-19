from datetime import datetime

from pydantic import BaseModel, Field


class GenerationRequestCreate(BaseModel):
    model_id: int
    prompt: str
    size: str | None = None
    aspect_ratio: str | None = None
    style: str | None = None


class GenerationSubmitIn(BaseModel):
    telegram_id: int
    model_id: int
    prompt: str
    size: str | None = None
    aspect_ratio: str | None = None
    resolution: str | None = None
    quality: str | None = None
    input_fidelity: str | None = None
    language: str | None = None
    reference_urls: list[str] = Field(default_factory=list)
    reference_file_ids: list[str] = Field(default_factory=list)
    chat_id: int | None = None
    message_id: int | None = None
    prompt_message_id: int | None = None


class GenerationAccessIn(BaseModel):
    telegram_id: int


class GenerationActiveOut(BaseModel):
    has_active: bool
    request_id: int | None = None
    public_id: str | None = None
    status: str | None = None


class GenerationRequestOut(BaseModel):
    id: int
    public_id: str
    user_id: int
    model_id: int
    prompt: str
    status: str
    size: str | None = None
    input_params: dict | None = None
    aspect_ratio: str | None = None
    style: str | None = None
    error_message: str | None = None
    references_count: int
    cost: int | None = None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True


class GenerationSubmitOut(BaseModel):
    request: GenerationRequestOut
    job_id: int | None = None
    provider_job_id: str | None = None
    trial_used: bool


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
