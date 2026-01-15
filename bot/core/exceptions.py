"""Custom exceptions for the bot."""

from typing import Any


class BotException(Exception):
    """Base exception for bot errors."""
    
    def __init__(self, message: str, user_message: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.user_message = user_message or message


class APIConnectionError(BotException):
    """Raised when API connection fails."""
    
    def __init__(self, message: str = "API connection failed") -> None:
        super().__init__(
            message=message,
            user_message="server_connection_error",
        )


class APIError(BotException):
    """Raised when API returns an error."""
    
    def __init__(
        self,
        status: int,
        data: Any,
        message: str | None = None,
    ) -> None:
        super().__init__(message=message or f"API error {status}")
        self.status = status
        self.data = data


class InsufficientBalanceError(BotException):
    """Raised when user doesn't have enough balance."""
    
    def __init__(self) -> None:
        super().__init__(
            message="Insufficient balance",
            user_message="insufficient_balance",
        )


class ActiveGenerationError(BotException):
    """Raised when user already has active generation."""
    
    def __init__(self, active_request_id: int | None = None) -> None:
        super().__init__(
            message="Active generation exists",
            user_message="active_generation_exists",
        )
        self.active_request_id = active_request_id


class RateLimitExceededError(BotException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after: int = 60) -> None:
        super().__init__(
            message="Rate limit exceeded",
            user_message="rate_limit_exceeded",
        )
        self.retry_after = retry_after


class ValidationError(BotException):
    """Raised when validation fails."""
    
    def __init__(self, field: str, message: str) -> None:
        super().__init__(
            message=f"Validation error: {field} - {message}",
            user_message="validation_error",
        )
        self.field = field


class ModelNotFoundError(BotException):
    """Raised when model is not found."""
    
    def __init__(self, model_id: int) -> None:
        super().__init__(
            message=f"Model {model_id} not found",
            user_message="model_not_found",
        )
        self.model_id = model_id


class PromptRequiredError(BotException):
    """Raised when prompt is required but not provided."""
    
    def __init__(self) -> None:
        super().__init__(
            message="Prompt is required",
            user_message="prompt_required",
        )
