from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .config import settings
from .db import get_db
from .models import LoginFailure, User

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
    """Blocks a client and email pair after too many failures in a window. Failures live in the database,
    so they survive restarts and are shared by every worker."""

    def __init__(self, max_fails: int = 5, window: int = 300):
        self.max_fails, self.window = max_fails, timedelta(seconds=window)

    def _recent(self, db, key):
        return db.query(LoginFailure).filter(LoginFailure.client == "|".join(key),
                                             LoginFailure.at > datetime.utcnow() - self.window)

    def blocked(self, db, key) -> bool:
        return self._recent(db, key).count() >= self.max_fails

    def fail(self, db, key) -> None:
        now = datetime.utcnow()
        db.query(LoginFailure).filter(LoginFailure.at < now - self.window).delete()  # forget old rows
        db.add(LoginFailure(client="|".join(key), at=now))
        db.commit()

    def reset(self, db, key) -> None:
        db.query(LoginFailure).filter(LoginFailure.client == "|".join(key)).delete()
        db.commit()


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
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid token")
    if user is None:
        raise HTTPException(status_code=401, detail="Unknown user")
    return user
