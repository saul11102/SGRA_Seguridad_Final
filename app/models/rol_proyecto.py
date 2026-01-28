from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

class RolProyecto(BaseModelORM):
    __tablename__ = "roles_proyecto"
    nombre = Column(String(50), unique=True, nullable=False)

    cuentas_proyecto = relationship("CuentaProyecto", back_populates="rol_proyecto")