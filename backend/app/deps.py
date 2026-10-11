import time
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import User

bearer = HTTPBearer(auto_error=False)


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8")[:72], bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8")[:72], hashed.encode("utf-8"))
    except ValueError:
        return False


DUMMY_HASH = hash_password("not-a-real-password")


class LoginLimiter:
    """Blocks a client and email pair after too many failures in a window.
    ponytail: in memory, per process, so it resets on restart; use Redis or the DB if the API runs on several workers."""

    def __init__(self, max_fails: int = 5, window: int = 300):
        self.max_fails, self.window, self.fails = max_fails, window, {}

    def _recent(self, key) -> list:
        now = time.monotonic()
        self.fails[key] = [t for t in self.fails.get(key, []) if now - t < self.window]
        return self.fails[key]

    def blocked(self, key) -> bool:
        return len(self._recent(key)) >= self.max_fails

    def fail(self, key) -> None:
        self._recent(key).append(time.monotonic())

    def reset(self, key) -> None:
        self.fails.pop(key, None)

    def clear(self) -> None:
        self.fails.clear()


login_limiter = LoginLimiter()


def create_token(user_id: int) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_hours)
    return jwt.encode({"sub": str(user_id), "exp": exp}, settings.jwt_secret, algorithm="HS256")


def current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    if creds is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        data = jwt.decode(creds.credentials, settings.jwt_secret, algorithms=["HS256"])
        user = db.get(User, int(data["sub"]))
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user
