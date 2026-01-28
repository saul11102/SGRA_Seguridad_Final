from pydantic import BaseModel, ConfigDict
from typing import Optional, Any, TypeVar, Generic

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """
    Esquema de respuesta API estandarizado.
    """
    code: int
    msg: str
    data: Optional[T] = None

    model_config = ConfigDict(from_attributes=True)
