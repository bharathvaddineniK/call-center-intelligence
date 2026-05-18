"""Retry helpers for LLM provider calls."""

NON_RETRYABLE_STATUS_CODES = {400, 401, 403}
NON_RETRYABLE_ERROR_NAMES = {
    "AuthenticationError",
    "BadRequestError",
    "PermissionDeniedError",
}
MODEL_ACCESS_STATUS_CODES = {400, 403}
MODEL_ACCESS_MARKERS = (
    "does not have access to model",
    "invalid model",
    "model_not_found",
)


def is_retryable_llm_error(exc: BaseException) -> bool:
    """Return whether an LLM provider error is worth retrying."""
    if exc.__class__.__name__ in NON_RETRYABLE_ERROR_NAMES:
        return False

    status_code = getattr(exc, "status_code", None)
    if status_code in NON_RETRYABLE_STATUS_CODES:
        return False

    return True


def is_model_access_error(exc: BaseException) -> bool:
    """Return whether an error indicates the configured model is unavailable."""
    status_code = getattr(exc, "status_code", None)
    if status_code not in MODEL_ACCESS_STATUS_CODES:
        return False

    message = str(exc).lower()
    return any(marker in message for marker in MODEL_ACCESS_MARKERS)
