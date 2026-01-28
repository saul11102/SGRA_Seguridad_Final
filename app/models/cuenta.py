from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum

class EstadoCuentaEnum(str, Enum):
    INACTIVO = "INACTIVO"
    ACTIVO = "ACTIVO"


class Cuenta(BaseModelORM):
    __tablename__ = "cuentas"
    estadoCuenta = Column(SAEnum(EstadoCuentaEnum), default=EstadoCuentaEnum.ACTIVO, nullable=False)

    rol_id = Column(Integer, ForeignKey("roles.id"))
    rol = relationship("Rol", back_populates="cuentas")
    proyectos = relationship("CuentaProyecto", back_populates="cuenta", cascade="all, delete-orphan")
    solicitud = relationship("SolicitudCuenta", back_populates="cuenta", uselist=False)
    historias_creadas = relationship(
        "HistoriaUsuario",
        foreign_keys="HistoriaUsuario.creado_por_id",
        back_populates="creado_por"
    )