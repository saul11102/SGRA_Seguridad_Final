from pydantic import BaseModel, ConfigDict, EmailStr
from ..models.requisito import Metodo_verificacion_requisito_Enum, Riesgo_Requisito_Enum, TipoRequisitoEnum, PrioridadRequisitoEnum, EstadoRequisitoEnum, Categoria_requisito_Enum
from datetime import datetime
from typing import Optional, List


class RequisitoBase(BaseModel):
    identificador: str
    nombre: Optional[str] = None

class Requisito(RequisitoBase):
    uuid: str
    model_config = ConfigDict(from_attributes=True)

class Obtener_Identificador(BaseModel):
    proyecto_uuid: str
    tipo_requisito: TipoRequisitoEnum

class schema_guardar_requisito(BaseModel):
    proyecto_uuid: str
    nombre: str
    descripcion: str
    tipo_requisito: TipoRequisitoEnum
    prioridad: PrioridadRequisitoEnum   
    fuente: Optional[str] = None
    metodo_verificacion: Metodo_verificacion_requisito_Enum
    categoria: Categoria_requisito_Enum
    horas_esfuerzo_estimado: Optional[int] = None
    riesgo: Riesgo_Requisito_Enum
    comentarios: Optional[str] = None

class schema_modificar_requisito(BaseModel):
    requisito_uuid: str
    nombre: str
    descripcion: str
    tipo_requisito: TipoRequisitoEnum
    prioridad: PrioridadRequisitoEnum  
    fuente: Optional[str] = None
    metodo_verificacion: Optional[str] = None
    categoria: Optional[str] = None
    horas_esfuerzo_estimado: Optional[int] = None
    riesgo: Optional[str] = None
    comentarios: Optional[str] = None

class schema_listar_historial(BaseModel):
    requisito_uuid: str

class schema_cambiar_estado_requisito(BaseModel):
    requisito_uuid: str
    nuevo_estado: EstadoRequisitoEnum
    razon_obsoleto: Optional[str] = None


class ResponseRequisitoCompleto(BaseModel):
    uuid: str
    identificador: str
    versionActual: int
    nombre: str
    descripcion: str
    fecha_creacion: datetime
    fecha_ultima_modificacion: datetime
    tipo: TipoRequisitoEnum
    prioridad: PrioridadRequisitoEnum
    estado: EstadoRequisitoEnum
    fuente: Optional[str] = None
    metodo_verificacion: Metodo_verificacion_requisito_Enum
    categoria: Categoria_requisito_Enum
    horas_esfuerzo_estimado: Optional[int] = None
    riesgo: Riesgo_Requisito_Enum
    comentarios: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    razon_obsoleto: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
    
class ResponseRequisitoCompletoObsoleto(BaseModel):
    uuid: str
    identificador: str
    versionActual: int
    nombre: str
    descripcion: str
    fecha_creacion: datetime
    fecha_ultima_modificacion: datetime
    tipo: TipoRequisitoEnum
    prioridad: PrioridadRequisitoEnum
    estado: EstadoRequisitoEnum
    fuente: Optional[str] = None
    metodo_verificacion: Metodo_verificacion_requisito_Enum
    categoria: Categoria_requisito_Enum
    horas_esfuerzo_estimado: Optional[int] = None
    riesgo: Riesgo_Requisito_Enum
    comentarios: Optional[str] = None
    razon_obsoleto: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class schema_historial_response(BaseModel):
    identificador: str
    nombre: str
    descripcion: str
    estado: EstadoRequisitoEnum
    prioridad: PrioridadRequisitoEnum
    fuente: Optional[str] = None
    tipo: TipoRequisitoEnum
    metodo_verificacion: Metodo_verificacion_requisito_Enum
    categoria: Categoria_requisito_Enum
    horas_esfuerzo_estimado: Optional[int] = None
    riesgo: Riesgo_Requisito_Enum
    comentarios: Optional[str] = None
    razon_obsoleto: Optional[str] = None
    razon_obsoleto: Optional[str] = None

class SchemaHistorialVersionResponse(BaseModel):
    version: int
    fecha: datetime
    cambios: list[str]
    requirement: schema_historial_response

class RequisitoListResponse(BaseModel):
    requisitos: List[ResponseRequisitoCompleto]
    total: int
    
class schema_responder_aprobacion(BaseModel):
    requisito_uuid: str
    aprobar: bool 
    motivo_rechazo: Optional[str] = None 