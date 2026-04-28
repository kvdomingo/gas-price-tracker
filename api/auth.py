from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from common.settings import settings

_bearer = HTTPBearer(auto_error=False)


def verify_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    if not settings.AUTH_ENABLED:
        return

    if credentials is None or credentials.credentials not in settings.API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
