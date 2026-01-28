from pydantic import BaseModel

class CuentaProyectoBase(BaseModel):
    cuenta_uuid: str
    proyecto_uuid: str

class AsignarRolCuentaProyecto(BaseModel):
    cuenta_uuid: str
    rol_proyecto_uuid: str
    proyecto_uuid: str

class CuentaProyectoResponse(BaseModel):
    id: int
    uuid: str
    rol_proyecto_uuid: str

    class Config:
        orm_mode = True
    

