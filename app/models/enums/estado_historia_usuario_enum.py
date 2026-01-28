from enum import Enum

class Estado(Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    COMPLETADA = "COMPLETADA"
    ATRASADA = "ATRASADA"
    OBSOLETA = "OBSOLETA"
