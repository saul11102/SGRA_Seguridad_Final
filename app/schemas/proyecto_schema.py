from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

from app.models.enums.estado_proyecto_enum import EstadoProyecto, TipoProyecto

class ProyectoBase(BaseModel):
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    tipo: TipoProyecto

class ProyectoCreate(ProyectoBase):
    uuid_usuario: str

class ProyectoUpdate(BaseModel):
    codigo: Optional[str] = None
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    estado: Optional[EstadoProyecto] = None
    tipo: Optional[TipoProyecto] = None

class Proyecto(ProyectoBase):
    id: int
    uuid: str
    version_actual: int
    estado: EstadoProyecto

    model_config = ConfigDict(from_attributes=True)