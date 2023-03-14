import fastapi
import sqlmodel as sqlm

from core import db, infra, models

router = fastapi.APIRouter()


@router.post("/", status_code=201)
def create_message_bus(
    message_bus: models.MessageBus,
    session: sqlm.Session = fastapi.Depends(db.get_session),
):
    session.add(message_bus)
    session.commit()
    session.refresh(message_bus)
    return message_bus


@router.get("/", response_model=list[models.MessageBus])
def read_message_bus(
    offset: int = 0,
    limit: int = fastapi.Query(default=100, lte=100),
    session: sqlm.Session = fastapi.Depends(db.get_session),
):
    return session.exec(
        sqlm.select(models.MessageBus).offset(offset).limit(limit)
    ).all()


@router.get("/{name}")
def read_message_bus(
    name: str, session: sqlm.Session = fastapi.Depends(db.get_session)
):
    message_bus = session.get(models.MessageBus, name)
    if not message_bus:
        raise fastapi.HTTPException(status_code=404, detail="Message bus not found")
    return {**message_bus.dict(), "topics": message_bus.infra.topic_names}


@router.post("/{name}", status_code=201)
def send_message(
    name: str,
    message: infra.Message,
    session: sqlm.Session = fastapi.Depends(db.get_session),
):
    message_bus = session.get(models.MessageBus, name)
    if not message_bus:
        raise fastapi.HTTPException(status_code=404, detail="Message bus not found")
    message_bus.infra.send(message)
