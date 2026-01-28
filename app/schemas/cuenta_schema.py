from pydantic import BaseModel, root_validator, ValidationError, ConfigDict, EmailStr
from enum import Enum
from typing import Optional, Any
from uuid import UUID

class EstadoCuentaEnum(str, Enum):
    INACTIVO = "INACTIVO"
    ACTIVO = "ACTIVO"

class CambiarRol(BaseModel):
    uuid_usuario: str
    rol_nombre: str

class CuentaResponse(BaseModel):
    uuid: UUID
    estadoCuenta: EstadoCuentaEnum

    model_config = ConfigDict(from_attributes=True)

class CuentaDetailResponse(BaseModel):
    id: int
    uuid: UUID
    nombre: str
    apellido: str
    correo: EmailStr
    estadoCuenta: str
    rol: str
    rol_id: int

    model_config = ConfigDict(from_attributes=True)

class EstadoCuentaUpdate(BaseModel):
    estadoCuenta: EstadoCuentaEnum

    @root_validator(pre=True)
    def validar_estado_cuenta(cls, values: dict[str, Any]):
        estado = values.get("estadoCuenta")
        
        if estado not in EstadoCuentaEnum.__members__:
            raise ValueError("Por favor, elija un valor válido: 'INACTIVO' o 'ACTIVO'")
        
        return values

    model_config = ConfigDict(from_attributes=True)
