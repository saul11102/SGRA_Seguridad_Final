from pydantic import BaseModel, ConfigDict
from typing import List


class RolPermisoBase(BaseModel):
    rol_id: int
    permiso_id: int


class RolPermisoCreate(BaseModel):
    rol_uuid: str
    permiso_uuid: str


class RolPermiso(RolPermisoBase):
    id: int
    uuid: str

    model_config = ConfigDict(from_attributes=True)


class RolPermisoUpdate(BaseModel):
    permisos: List[str]
