from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

class Proyecto(BaseModelORM):
    __tablename__ = "proyectos"
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    cuentas = relationship("CuentaProyecto", back_populates="proyecto", cascade="all, delete-orphan")
