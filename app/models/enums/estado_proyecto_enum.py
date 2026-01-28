import enum

class EstadoProyecto(enum.Enum):
    INACTIVO = "INACTIVO"
    ACTIVO = "ACTIVO"

class EstadoActualProyecto(enum.Enum):
    PROPUESTA = "PROPUESTA"
    PLANIFICACION = "PLANIFICACION"
    EJECUCION = "EJECUCION"
    PAUSADO = "PAUSADO"
    FINALIZADO = "FINALIZADO"

class TipoProyecto(enum.Enum):
    WEB = "WEB"
    MOVIL = "MOVIL"
    ESCRITORIO = "ESCRITORIO"
