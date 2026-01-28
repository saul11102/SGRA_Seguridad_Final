from pydantic import BaseModel, Field, validator
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.defecto import TipoSeveridadEnum, EstadoDefectoEnum, TipoDefectoEnum, PrioridadDefectoEnum

class DefectoBase(BaseModel):
    titulo: str = Field(..., min_length=5)
    descripcion_detallada: Optional[str] = None
    foto: Optional[str] = None
    tipo_defecto: TipoDefectoEnum
    prioridad: PrioridadDefectoEnum
    severidad: TipoSeveridadEnum

class DefectoCreate(DefectoBase):
    historia_usuario_uuid: UUID
    fecha_limite: Optional[datetime] = None

class DefectoUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=5)
    descripcion_detallada: Optional[str] = None
    foto: Optional[str] = None
    tipo_defecto: Optional[TipoDefectoEnum] = None
    prioridad: Optional[PrioridadDefectoEnum] = None
    severidad: Optional[TipoSeveridadEnum] = None
    fecha_limite: Optional[datetime] = None

class DefectoEstadoUpdate(BaseModel):
    estado: EstadoDefectoEnum
    comentario: Optional[str] = None

class DefectoAsignarEncargado(BaseModel):
    cuenta_proyecto_uuid: UUID

class HistorialDefectoResponse(BaseModel):
    estado_anterior: Optional[EstadoDefectoEnum] = None
    estado_nuevo: EstadoDefectoEnum
    fecha_cambio: datetime
    modificado_por: Optional[str] = "Sistema"
    comentario: Optional[str] = None

    class Config:
        from_attributes = True

class DefectoResponse(DefectoBase):
    uuid: UUID
    codigo: str
    estado: EstadoDefectoEnum
    fecha_creacion: datetime
    fecha_limite: Optional[datetime] = None
    
    class Config:
        from_attributes = True
        
class DefectoDetailResponse(DefectoResponse):
    historial_estados: List[HistorialDefectoResponse] = []