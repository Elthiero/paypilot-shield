from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..deps import current_user
from ..schemas import ChatIn
from ..services.agent import run_agent

router = APIRouter(prefix="/agent", tags=["agent"], dependencies=[Depends(current_user)])


@router.post("/chat")
def chat(body: ChatIn, db: Session = Depends(get_db)):
    return run_agent(db, body.message)
