from pydantic import BaseModel

class CreateSolicitud(BaseModel):
    nombre: str
    apellido: str
    correo: str
    contrasena: str


class ResponseSolicitud(BaseModel):
    msg: str
    code: int

    class Config:
        orm_mode = True
   
