from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.cuenta_proyecto import CuentaProyecto
from sqlalchemy.orm import joinedload

class cuenta_proyecto_service:
    def __init__(self, db: Session):
        self.db = db
    
    def listar_cuentas_proyecto(self):
        return (
            self.db.query(CuentaProyecto)
            .options(
                joinedload(CuentaProyecto.cuenta),
                joinedload(CuentaProyecto.proyecto),
                joinedload(CuentaProyecto.rol_proyecto)
            )
            .all()
        )

    def obtener_cuenta_proyecto(self, uuid_usuario: str, uuid_proyecto: str):
        cuenta_proyecto = (
            self.db.query(CuentaProyecto)
            .join(CuentaProyecto.cuenta)
            .join(CuentaProyecto.proyecto)
            .filter(CuentaProyecto.cuenta.has(uuid=uuid_usuario))
            .filter(CuentaProyecto.proyecto.has(uuid=uuid_proyecto))
            .first()
        )

        if not cuenta_proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cuenta-Proyecto no encontrada"
            )

        cuenta_proyecto.rol_proyecto_uuid = cuenta_proyecto.rol_proyecto.uuid

        return cuenta_proyecto