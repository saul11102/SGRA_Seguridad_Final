from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional


class LoginRequest(BaseModel):
    correo: EmailStr
    contrasena: str


class LoginResponse(BaseModel):
    uuid: Optional[str] = None
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    rol: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"

    model_config = ConfigDict(from_attributes=True)

class TokenData(BaseModel):
    id: Optional[str] = None

class authSchema:
    pass