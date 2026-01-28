from pydantic import BaseModel, ConfigDict

class EjemploCreate(BaseModel):
    nombre: str
    descripcion: str | None = None

class EjemploResponse(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None

    model_config = ConfigDict(from_attributes=True)
