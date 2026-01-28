import uuid
from sqlalchemy import Column, Integer, String
from ..config.database import Base

class BaseModelORM(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), default=lambda: str(uuid.uuid4()), unique=True, nullable=False)
