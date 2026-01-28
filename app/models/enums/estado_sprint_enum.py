from enum import Enum

class EstadoSprint(Enum):
    PLANIFICADO = "PLANIFICADO"
    EN_CURSO = "EN_CURSO"
    COMPLETADO = "COMPLETADO"
    CANCELADO = "CANCELADO"
