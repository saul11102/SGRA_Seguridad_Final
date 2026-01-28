from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from datetime import date
from app.models.enums.estado_sprint_enum import EstadoSprint


class SprintBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=100)
    fecha_inicio: date
    fecha_fin: date
    objetivo: str = Field(..., min_length=10, max_length=500)
    
    @field_validator('fecha_fin')
    @classmethod
    def validar_fechas(cls, fecha_fin, info):
        if 'fecha_inicio' in info.data:
            fecha_inicio = info.data['fecha_inicio']
            if fecha_fin <= fecha_inicio:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return fecha_fin


class SprintCreate(SprintBase):
    uuid_proyecto: str


class SprintUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    objetivo: Optional[str] = Field(None, min_length=10, max_length=500)
    estado: Optional[EstadoSprint] = None
    
    @field_validator('fecha_fin')
    @classmethod
    def validar_fechas(cls, fecha_fin, info):
        if fecha_fin and 'fecha_inicio' in info.data and info.data['fecha_inicio']:
            if fecha_fin <= info.data['fecha_inicio']:
                raise ValueError('La fecha de fin debe ser posterior a la fecha de inicio')
        return fecha_fin


class Sprint(SprintBase):
    uuid: str
    estado: EstadoSprint

    model_config = ConfigDict(from_attributes=True)


class SprintCambiarEstado(BaseModel):
    nuevo_estado: EstadoSprint


class SprintListItem(BaseModel):
    uuid: str
    nombre: str
    fecha_inicio: date
    fecha_fin: date
    objetivo: str
    estado: EstadoSprint

    model_config = ConfigDict(from_attributes=True)


class SprintBasicItem(BaseModel):
    uuid: str
    nombre: str
    estado: EstadoSprint

    model_config = ConfigDict(from_attributes=True)


class AsignarHistoriaSprint(BaseModel):
    sprint_uuid: str
    historia_uuid: str
    uuid_creador: str


class RemoverHistoriaSprint(BaseModel):
    sprint_uuid: str
    historia_uuid: str
    uuid_creador: str
