from pydantic import BaseModel
from typing import Optional

class ProyectoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ProyectoCreate(ProyectoBase):
    pass

class Proyecto(ProyectoBase):
    id: int
    uuid: str

    class Config:
        orm_mode = True
