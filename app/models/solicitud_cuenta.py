from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum as SAEnum
from enum import Enum
from sqlalchemy.orm import relationship
from datetime import datetime

class EstadoSolicitudEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    RECHAZADO = "RECHAZADO"
    APROBADO = "APROBADO"

class SolicitudCuenta(BaseModelORM):
    __tablename__ = "solicitudes_cuenta"

    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    correo = Column(String(150), unique=True, nullable=False)
    contrasena = Column(String(255), nullable=False)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)
    estado = Column(SAEnum(EstadoSolicitudEnum), default=EstadoSolicitudEnum.PENDIENTE, nullable=False)
    
    cuenta_id = Column(Integer, ForeignKey("cuentas.id"), nullable=True)
    cuenta = relationship("Cuenta", back_populates="solicitud")


