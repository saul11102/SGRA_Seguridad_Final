from pydantic import BaseModel, ConfigDict, EmailStr
from ..models.solicitud_cuenta import EstadoSolicitudEnum
from datetime import datetime

class CreateSolicitud(BaseModel):
    nombre: str
    apellido: str
    correo: EmailStr
    contrasena: str

class schema_solicitud_cuenta(BaseModel):
    uuid_usuario: str
    decision: EstadoSolicitudEnum

    model_config = ConfigDict(from_attributes=True)

class SolicitudDetail(BaseModel):
    uuid: str
    nombre: str
    apellido: str
    correo: EmailStr
    fecha_solicitud: datetime
    estado: str

    model_config = ConfigDict(from_attributes=True)

class SolicitudListResponse(BaseModel):
    solicitudes: list[SolicitudDetail]
    total: int

    model_config = ConfigDict(from_attributes=True)

class RecuperarPasswordRequest(BaseModel):
    email: EmailStr


