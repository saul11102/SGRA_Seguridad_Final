from pydantic import BaseModel
from typing import Optional
from pydantic import ConfigDict

class PermisoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class PermisoCreate(PermisoBase):
    pass

class Permiso(PermisoBase):
    id: int
    uuid: str

    model_config = ConfigDict(from_attributes=True)
