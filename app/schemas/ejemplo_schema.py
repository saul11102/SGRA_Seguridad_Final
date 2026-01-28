from pydantic import BaseModel

class EjemploCreate(BaseModel):
    nombre: str
    descripcion: str | None = None

class EjemploResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None

    class Config:
        orm_mode = True
