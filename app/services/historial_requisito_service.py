from sqlalchemy import event, inspect
from sqlalchemy.orm import attributes
from app.models.requisito import Requisito
from app.models.historial_requisito import HistorialRequisito

# lista de atributos que, si se modifican, generan un registro en el historial
CAMPOS_AUDITABLES = [
    'nombre',
    'descripcion',
    'tipo',
    'prioridad',
    'estado',
    'fuente',
    'metodo_verificacion',
    'categoria',
    'horas_esfuerzo_estimado',
    'riesgo',
    'comentarios'
]

DESCRIPCION_CAMPOS = {
    'nombre': 'Cambio en el nombre',
    'descripcion': 'Cambio en la descripción',
    'tipo': 'Cambio en el tipo de requisito',
    'prioridad': 'Cambio en la prioridad',
    'estado': 'Cambio en el estado',
    'fuente': 'Cambio en la fuente',
    'metodo_verificacion': 'Cambio en el método de verificación',
    'categoria': 'Cambio en la categoría',
    'horas_esfuerzo_estimado': 'Cambio en las horas de esfuerzo estimado',
    'riesgo': 'Cambio en el riesgo',
    'comentarios': 'Cambio en los comentarios'
}

def get_old_value(target, field_name):
    hist = attributes.get_history(target, field_name)
    if hist.has_changes():
        return hist.deleted[0]
    return getattr(target, field_name)

@event.listens_for(Requisito, 'before_update')
def auditar_cambios(mapper, connection, target):
    campos_cambiados = [campo for campo in CAMPOS_AUDITABLES if attributes.get_history(target, campo).has_changes()]
    if not campos_cambiados:
        return

    for campo in campos_cambiados:
        valores_antiguos = {
            'requisito_id': target.id,
            'tipo_cambio': campo,
            'identificador': target.identificador,
            'version': target.versionActual,
            'nombre': get_old_value(target, 'nombre'),
            'descripcion': get_old_value(target, 'descripcion'),
            'tipo': get_old_value(target, 'tipo'),
            'prioridad': get_old_value(target, 'prioridad'),
            'estado': get_old_value(target, 'estado'),
            'fuente': get_old_value(target, 'fuente'),
            'metodo_verificacion': get_old_value(target, 'metodo_verificacion'),
            'categoria': get_old_value(target, 'categoria'),
            'horas_esfuerzo_estimado': get_old_value(target, 'horas_esfuerzo_estimado'),
            'riesgo': get_old_value(target, 'riesgo'),
            'comentarios': get_old_value(target, 'comentarios')
        }

        connection.execute(HistorialRequisito.__table__.insert().values(**valores_antiguos))

    # Incrementar versión después de guardar historial
    target.versionActual += 1

    

