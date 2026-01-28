from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from ..models.tarea import PrioridadTareaEnum, EstadoTareaEnum
from datetime import datetime
from typing import Any, Optional, List

class Guardar_tarea(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    criterios_entrada: Optional[str] = None
    criterios_salida: Optional[str] = None
    fecha_limite: Optional[datetime] = None
    tipo_tarea: Optional[str] = None
    estimacion_horas: Optional[int] = None
    prioridad: PrioridadTareaEnum
    historia_usuario_uuid: str
    cuenta_proyecto_uuid: Optional[str] = None
    
class ResponsableDetalle(BaseModel):
    nombre: str
    apellido: str
    uuid_cuenta_proyecto: str
    
class HistoriaUsuarioResumen(BaseModel):
    uuid: str
    identificador: Optional[str]  # Puede ser None si la HU es antigua y no tenía ID
    titulo: str

class Tarea(BaseModel):
    uuid: str
    identificador: str
    titulo: str
    descripcion: Optional[str] = None
    criterios_entrada: Optional[str] = None
    criterios_salida: Optional[str] = None
    tipo_tarea: Optional[str] = None
    estimacion_horas: Optional[int] = None
    prioridad: PrioridadTareaEnum
    estado: EstadoTareaEnum
    fecha_limite: Optional[datetime] = None
    historia_usuario: Optional[HistoriaUsuarioResumen] = None
    responsable: Optional[ResponsableDetalle] = None
    comentario_para_ajustes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)
    
    @field_validator('responsable', mode='before')
    def extraer_nombre_responsable(cls, v: Any) -> Optional[dict]:
            if not v:
                return None
                
            if isinstance(v, dict):
                return v
                
            try:
                if v.cuenta and v.cuenta.solicitud:
                    return {
                        "nombre": v.cuenta.solicitud.nombre,
                        "apellido": v.cuenta.solicitud.apellido,
                        "uuid_cuenta_proyecto": v.uuid
                    }
            except AttributeError:
                return None
                
            return None
        
    @field_validator('historia_usuario', mode='before')
    @classmethod
    def validar_hu(cls, v: Any) -> Optional[dict]:
        if not v:
            return None
        
        if isinstance(v, dict):
            return v
        
        return {
            "uuid": str(v.uuid),
            "identificador": v.identificador,
            "titulo": v.titulo
        }
    
class Modificar_tarea(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    criterios_entrada: Optional[str] = None
    criterios_salida: Optional[str] = None
    fecha_limite: Optional[datetime] = None
    tipo_tarea: Optional[str] = None
    estimacion_horas: Optional[int] = None
    prioridad: Optional[PrioridadTareaEnum] = None
    cuenta_proyecto_uuid: Optional[str] = None # este es el responsable de la tarea
    responsable_cambio_uuid: str # UUID de la cuenta que realiza el cambio
    
class Cambiar_estado_tarea(BaseModel):
    nuevo_estado: EstadoTareaEnum
    responsable_cambio_uuid: str # UUID de la cuenta que realiza el cambio
    
class UsuarioHistorial(BaseModel):
    nombre: str
    apellido: str
    model_config = ConfigDict(from_attributes=True)

class HistorialTareaRead(BaseModel):
    id: int
    fecha_modificacion: datetime
    tipo_cambio: str
    usuario: Optional[UsuarioHistorial] = None 
    model_config = ConfigDict(from_attributes=True)

class Cambiar_asignado_tarea(BaseModel):
    cuenta_proyecto_uuid: str 
    responsable_cambio_uuid: str 
class Iniciar_tarea(BaseModel):
    responsable_cambio_uuid: str # UUID de la cuenta que va a hacer el cambio de estado de la tarea, debería de ser la misma persona asignada a la tarea
    
class Enviar_a_revision(BaseModel):
    responsable_cambio_uuid: str
    
class Revisar_tarea(BaseModel):
    aprobado: bool 
    comentario: Optional[str] 
    responsable_cambio_uuid: str #persona que revisa la tarea

class TareaListResponse(BaseModel):
    tareas: List[Tarea]
    total: int
    page: int
    page_size: int