from pydantic import BaseModel, ConfigDict

class Rol(BaseModel):
    id: int
    nombre: str
    uuid: str

    model_config = ConfigDict(from_attributes=True)
