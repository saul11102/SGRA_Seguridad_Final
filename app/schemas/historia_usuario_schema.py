from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from app.models.enums.estado_historia_usuario_enum import Estado
from app.models.enums.prioridad_historia_usuario import Prioridad

class HistoriaUsuarioBase(BaseModel):
    titulo: str = Field(..., min_length=10)
    descripcion: str = Field(..., min_length=60)
    prioridad: Prioridad
    criterios_aceptacion: str
    estimacion: int = Field(..., ge=0, le=180)
    
class HistoriaUsuarioResponse(BaseModel):
    titulo: str = Field(..., min_length=10)
    descripcion: str = Field(..., min_length=5)
    identificador: str = Field(..., min_length=1)
    prioridad: Prioridad
    criterios_aceptacion: str
    estimacion: int = Field(..., ge=0, le=180)


class HistoriaUsuarioCreate(HistoriaUsuarioBase):
    uuids_requisitos: list[str]
    uuid_responsable: Optional[str] = None


class HistoriaUsuarioUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=10)
    descripcion: Optional[str] = Field(None, min_length=60)
    prioridad: Optional[Prioridad] = None
    criterios_aceptacion: Optional[str] = None
    estimacion: Optional[int] = Field(None, ge=0, le=180)
    uuids_requisitos: Optional[list[str]] = None


class HistoriaUsuario(HistoriaUsuarioBase):
    uuid: str
    estado: Estado

    model_config = ConfigDict(from_attributes=True)


class CreadorInfo(BaseModel):
    uuid: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class RequisitoInfo(BaseModel):
    uuid: str
    identificador: str

    model_config = ConfigDict(from_attributes=True)


class HistoriaUsuarioListItem(BaseModel):
    uuid: str
    titulo: str
    identificador: Optional[str] = None
    descripcion: str
    prioridad: Prioridad
    estado: Estado
    estimacion: Optional[int] = None
    criterios_aceptacion: Optional[str] = None
    fecha_creacion: datetime
    fecha_ultima_modificacion: datetime
    sprint_uuid: Optional[str] = None
    requisitos: list[RequisitoInfo] = []
    creador: Optional[CreadorInfo] = None

    model_config = ConfigDict(from_attributes=True)


class HistoriaUsuarioListResponse(BaseModel):
    historias: list[HistoriaUsuarioListItem]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class EliminarHistoriaUsuario(BaseModel):
    uuid_historia: str

    model_config = ConfigDict(from_attributes=True)


class EditarHistoriaUsuario(BaseModel):
    uuid_historia: str
    datos: HistoriaUsuarioUpdate

    model_config = ConfigDict(from_attributes=True)

class Schema_CambiarEstadoHistoriaUsuario(BaseModel):
    uuid_historia: str
    nuevo_estado: Estado


class HistoriaUsuarioAgregarASprint(BaseModel):
    uuid_historia: str
    uuid_sprint: str


class HistoriaUsuarioQuitarDeSprint(BaseModel):
    uuid_historia: str
    uuid_sprint: str


class HistorialHistoriaUsuarioResponse(BaseModel):
    campo: str
    valor_anterior: Optional[str] = None
    valor_nuevo: Optional[str] = None
    fecha_modificacion: datetime
    modificado_por: Optional[str] = "Sistema"

    model_config = ConfigDict(from_attributes=True)
