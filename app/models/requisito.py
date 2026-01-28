from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, func, Enum  as SAEnum
from enum import Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.requisitos_historias_usuario import requisitos_historias_usuario


class TipoRequisitoEnum(str, Enum):
    FUNCIONAL = "FUNCIONAL"
    NO_FUNCIONAL = "NO FUNCIONAL"

class PrioridadRequisitoEnum(str, Enum):
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAJA = "BAJA"

class EstadoRequisitoEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    RECHAZADO = "RECHAZADO"
    APROBADO = "APROBADO"
    EN_CONSTRUCCION = "EN CONSTRUCCION"
    TERMINADO = "TERMINADO"
    OBSOLETO = "OBSOLETO"
    
class Metodo_verificacion_requisito_Enum(str, Enum):
    INSPECCION = "INSPECCION"
    ANALISIS = "ANALISIS"
    PRUEBA = "PRUEBA"
    DESMOTRACION = "DEMOSTRACION"
    
class Categoria_requisito_Enum(str, Enum):
    ADECUACION_FUNCIONAL = "ADECUACION_FUNCIONAL"
    EFICIENCIA_DESEMPENO = "EFICIENCIA_DESEMPENO"
    COMPATIBILIDAD = "COMPATIBILIDAD"
    USABILIDAD = "USABILIDAD"
    FIABILIDAD = "FIABILIDAD"
    SEGURIDAD = "SEGURIDAD"
    MANTENIBILIDAD = "MANTENIBILIDAD"
    PORTABILIDAD = "PORTABILIDAD"

class Riesgo_Requisito_Enum(str, Enum):
    BAJO = "BAJO"
    MEDIO = "MEDIO"
    ALTO = "ALTO"
    CRITICO = "CRITICO"

class Requisito(BaseModelORM):
    __tablename__ = "requisitos"

    identificador = Column(String(100), nullable=False)
    versionActual = Column(Integer, nullable=False, default=1)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(String(255), nullable=False)
    fecha_creacion = Column(DateTime, server_default=func.now(), nullable=False)

    # Cuando se quiera hacer una nueva versión del requisito
    # este metodo actualiza automaticamente la fecha cuando se modifica cualquier atributo
    fecha_ultima_modificacion = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    tipo = Column(SAEnum(TipoRequisitoEnum), nullable=False)
    prioridad = Column(SAEnum(PrioridadRequisitoEnum), nullable=False)
    estado = Column(SAEnum(EstadoRequisitoEnum), nullable=False)
    fuente = Column(String(100), nullable=True) # quién o que generó el requisito, osea de donde surge la necesidad de crear el requisito
    metodo_verificacion = Column(SAEnum(Metodo_verificacion_requisito_Enum), nullable=False) # cómo se verificará que el requisito ha sido cumplido
    categoria = Column(SAEnum(Categoria_requisito_Enum), nullable=False) # clasificación del requisito (por ejem plo, seguridad, usabilidad, rendimiento, etc.)
    horas_esfuerzo_estimado = Column(Integer, nullable=True) # estimación del esfuerzo en horas para completar el requisito
    riesgo = Column(SAEnum(Riesgo_Requisito_Enum), nullable=False) # impacto si no se implementa o falla.
    comentarios = Column(String(255), nullable=True) # notas adicionales o comentarios sobre el requisito
    motivo_rechazo = Column(String(255), nullable=True) # razón por la cual el requisito fue rechazado
    
    razon_obsoleto = Column(String(255), nullable=True) # razón por la cual el requisito fue marcado como obsoleto

    proyecto_id = Column(Integer, ForeignKey('proyectos.id'), nullable=False)
    proyecto = relationship("Proyecto", back_populates="requisito")
    
    
    historias_usuario = relationship(
        "HistoriaUsuario",
        secondary=requisitos_historias_usuario,
        back_populates="requisitos"
    )

    historial = relationship("HistorialRequisito", back_populates="requisito_padre", cascade="all, delete-orphan")