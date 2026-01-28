from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

class Rol(BaseModelORM):
    __tablename__ = "roles"
    nombre = Column(String(50), unique=True, nullable=False)

    cuentas = relationship("Cuenta", back_populates="rol")
