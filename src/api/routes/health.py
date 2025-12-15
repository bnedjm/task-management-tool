"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check")
def health_check() -> dict:
    """Health check endpoint.

    Returns:
        dict: Health status.
    """
    return {"status": "healthy"}
