from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import relationship
from app.models.requisito import TipoRequisitoEnum, PrioridadRequisitoEnum, EstadoRequisitoEnum 
from enum import Enum


class   HistorialRequisito(BaseModelORM):
    __tablename__ = "historial_requisitos"

    identificador = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False)  
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=False)
    fecha = Column(DateTime, server_default=func.now(), nullable=False)
    tipo = Column(SAEnum(TipoRequisitoEnum), nullable=False)
    prioridad = Column(SAEnum(PrioridadRequisitoEnum), nullable=False)
    estado = Column(SAEnum(EstadoRequisitoEnum), nullable=False)
    tipo_cambio = Column(String(100), nullable=False)
    fuente = Column(String(100), nullable=True) 
    metodo_verificacion = Column(String(100), nullable=True) 
    categoria = Column(String(100), nullable=True)
    horas_esfuerzo_estimado = Column(Integer, nullable=True) 
    riesgo = Column(String(100), nullable=True) 
    comentarios = Column(String(255), nullable=True)
    razon_obsoleto = Column(String(255), nullable=True)
    requisito_id = Column(Integer, ForeignKey('requisitos.id'), nullable=False)
    requisito_padre = relationship("Requisito", back_populates="historial")
    