from sqlalchemy import event
from sqlalchemy.orm import attributes
from app.models.tarea import Tarea
from app.models.historial_tarea import HistorialTarea

CAMPOS_AUDITABLES_TAREA = [
    'titulo', 'descripcion', 'prioridad', 'estado', 'cuenta_proyecto_id'
]

DESCRIPCIONES_TAREA = {
    'titulo': 'Modificación del título',
    'descripcion': 'Modificación de la descripción',
    'prioridad': 'Cambio de prioridad',
    'estado': 'Cambio de estado',
    'cuenta_proyecto_id': 'Cambio de responsable asignado'
}

@event.listens_for(Tarea, 'before_update')
def auditar_cambios_tarea(mapper, connection, target):
    campos_cambiados = [
        campo for campo in CAMPOS_AUDITABLES_TAREA 
        if attributes.get_history(target, campo).has_changes()
    ]
    
    if not campos_cambiados:
        return

    responsable_id = getattr(target, '_usuario_autor_id', None)

    for campo in campos_cambiados:
        connection.execute(
            HistorialTarea.__table__.insert().values(
                tarea_id=target.id,
                tipo_cambio=DESCRIPCIONES_TAREA.get(campo, f"Actualización de {campo}"),
                modificado_por_id=responsable_id
            )
        )