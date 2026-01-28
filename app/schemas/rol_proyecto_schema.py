from pydantic import BaseModel
from typing import List
from .permiso_schema import Permiso
from pydantic import ConfigDict

class RolProyectoBase(BaseModel):
    nombre: str
    descripcion: str | None = None

class RolProyectoCreate(RolProyectoBase):
    permisos_uuids: List[str] = [] 
    proyecto_uuid: str

class RolProyecto(RolProyectoBase):
    id: int
    uuid: str
    permisos: List[Permiso] = []

    model_config = ConfigDict(from_attributes=True)
