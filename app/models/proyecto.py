from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, Date, Enum
from sqlalchemy.orm import relationship

from app.models.enums.estado_proyecto_enum import EstadoProyecto, TipoProyecto

class Proyecto(BaseModelORM):
    __tablename__ = "proyectos"

    version_actual = Column(Integer, nullable=False, default=1)
    codigo = Column(String(50), unique=True, nullable=False)
    
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    fecha_inicio = Column(Date, nullable=True)
    fecha_fin = Column(Date, nullable=True)

    estado = Column(Enum(EstadoProyecto), nullable=False)
    tipo = Column(Enum(TipoProyecto), nullable=False)


    roles_proyecto = relationship("RolProyecto", back_populates="proyecto")


    requisito = relationship(
        "Requisito",
        back_populates="proyecto",
        cascade="all, delete-orphan"
    )

    cuentas = relationship(
        "CuentaProyecto",
        back_populates="proyecto",
        cascade="all, delete-orphan"
    )

