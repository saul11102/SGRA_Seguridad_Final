from sqlalchemy import Column, Integer, String
from ..config.database import Base

class Ejemplo(Base):
    __tablename__ = "ejemplos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(255), nullable=False)
    descripcion = Column(String(500), nullable=True)
