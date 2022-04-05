from __future__ import annotations
import abc
import contextlib
import uuid
import pathlib

import beaver


class DataStore(abc.ABC):
    def prepare(self):
        ...

    @abc.abstractmethod
    def store(self, kind: str, loop_part: beaver.LoopPart):
        ...

    def store_event(self, event: beaver.Event):
        return self.store("event", event)

    def store_features(self, features: beaver.Features):
        return self.store("features", features)

    def store_prediction(self, prediction: beaver.Prediction):
        return self.store("prediction", prediction)

    def store_label(self, label: beaver.Label):
        return self.store("label", label)

    @abc.abstractmethod
    def get(self, kind: str, loop_id: str | uuid.UUID):
        ...

    def get_event(self, loop_id: str | uuid.UUID):
        return self.get("event", loop_id)

    def get_features(self, loop_id: str | uuid.UUID):
        return self.get("features", loop_id)

    def get_prediction(self, loop_id: str | uuid.UUID):
        return self.get("prediction", loop_id)

    def get_label(self, loop_id: str | uuid.UUID):
        return self.get("label", loop_id)

    def clear(self):
        raise NotImplementedError


import sqlalchemy as sqla
import sqlalchemy.orm

Base = sqlalchemy.orm.declarative_base()


class Event(Base):
    __tablename__ = "events"
    loop_id = sqla.Column(sqla.Text(), primary_key=True)
    content = sqla.Column(sqla.Text())

    @classmethod
    def from_dataclass(cls, event: beaver.Event):
        return cls(loop_id=str(event.loop_id), content=event.to_json())

    def to_dataclass(self):
        return beaver.Event(loop_id=self.loop_id, content=self.content)


class SQLDataStore(DataStore):
    def __init__(self, url):
        self.engine = sqla.create_engine(url)

    def prepare(self):
        Base.metadata.create_all(self.engine)

    @contextlib.contextmanager
    def session(self):
        session_maker = sqlalchemy.orm.sessionmaker(self.engine)
        try:
            with session_maker.begin() as session:
                yield session
        finally:
            pass

    def store(self, kind, loop_part):
        row = {"event": Event}[kind].from_dataclass(loop_part)
        with self.session() as session:
            session.add(row)

    def get(self, kind, loop_id):
        klass = {"event": Event}[kind]
        with self.session() as session:
            return (
                session.query(klass)
                .filter_by(loop_id=str(loop_id))
                .first()
                .to_dataclass()
            )
