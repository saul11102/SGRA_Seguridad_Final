from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, Enum as SAEnum, ForeignKey, DateTime, func, Text
from sqlalchemy.orm import relationship
from enum import Enum
from datetime import datetime

class TipoDefectoEnum(str, Enum):
    FUNCIONAL = "FUNCIONAL"
    UI = "UI"
    RENDIMIENTO = "RENDIMIENTO"
    SEGURIDAD = "SEGURIDAD"

class PrioridadDefectoEnum(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"

class TipoSeveridadEnum(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    SEVERO = "SEVERO"
    CRITICO = "CRITICO"


class EstadoDefectoEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    ASIGNADO = "ASIGNADO"
    EN_DESARROLLO = "EN_DESARROLLO"
    EN_REVISION = "EN_REVISION"
    ATRASADO = "ATRASADO"
    RESUELTO = "RESUELTO"
    CANCELADO = "CANCELADO"

class Defecto(BaseModelORM):
    __tablename__ = "defectos"
    codigo = Column(String(35), unique=True, nullable=False)
    titulo = Column(String(100), nullable=False)
    descripcion_detallada = Column(Text, nullable=True)
    foto = Column(String(255), nullable=True)
    tipo_defecto = Column(SAEnum(TipoDefectoEnum), nullable=False)
    prioridad = Column(SAEnum(PrioridadDefectoEnum), nullable=False)
    severidad = Column(SAEnum(TipoSeveridadEnum), nullable=False)
    estado = Column(SAEnum(EstadoDefectoEnum), nullable=False, default=EstadoDefectoEnum.PENDIENTE)
    
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)
    fecha_limite = Column(DateTime, nullable=True)

    historia_usuario_id = Column(Integer, ForeignKey("historias_usuario.id"))
    cuenta_proyecto_id = Column(Integer, ForeignKey("cuentas_proyecto.id"), nullable=True)

    historia_usuario = relationship("HistoriaUsuario", back_populates="defectos")
    cuenta_proyecto = relationship("CuentaProyecto", back_populates="defectos")
    historial_estados = relationship("HistorialDefecto", back_populates="defecto", cascade="all, delete-orphan")
