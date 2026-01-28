import bcrypt
import base64
from fastapi import HTTPException
from app.models.cuenta_proyecto import CuentaProyecto
from app.models.permiso import Permiso
from app.models.rol_permiso import RolPermiso
from app.models.cuenta import Cuenta
from fastapi import Depends
from sqlalchemy.orm import Session
from app.core.get_db import get_db
from app.core.security import get_current_user
from app.models.proyecto import Proyecto


@staticmethod
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return base64.b64encode(hashed_password).decode('utf-8')

@staticmethod
def verify_password(plain_password: str, hashed_password_str: str) -> bool:
    hashed_password = base64.b64decode(hashed_password_str.encode('utf-8'))
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password)

@staticmethod
def verificar_permiso(usuario_id: int, proyecto_id: int, permiso_requerido: str, db):
    rol = db.query(CuentaProyecto).filter_by(
        usuario_id=usuario_id,
        proyecto_id=proyecto_id
    ).first()

    if not rol:
        raise HTTPException(403, "No perteneces a este proyecto")

    permiso = db.query(Permiso).filter_by(codigo=permiso_requerido).first()

    tiene_permiso = db.query(RolPermiso).filter_by(
        rol_id=rol.rol_id,
        permiso_id=permiso.id
    ).first()

    if not tiene_permiso:
        raise HTTPException(403, "No tienes permiso para esta acción")


@staticmethod
def require_project_permission(permiso_codigo: str):
    def dependency(
        proyecto_uuid: str,
        current_user: Cuenta = Depends(get_current_user),
        db: Session = Depends(get_db)
    ):
        
        proyecto = db.query(Proyecto).filter(Proyecto.uuid == proyecto_uuid).first()
        if not proyecto:
            raise HTTPException(
                status_code=404,
                detail="Proyecto no encontrado"
            )

        # 1. Verificar que pertenece al proyecto
        cuenta_proyecto = (
            db.query(CuentaProyecto)
            .filter(
                CuentaProyecto.cuenta_id == current_user.id,
                CuentaProyecto.proyecto_id == proyecto.id
            )
            .first()
        )

        if not cuenta_proyecto:
            raise HTTPException(
                status_code=403,
                detail="No perteneces a este proyecto"
            )

        # 2. Obtener permiso requerido
        permiso = (
            db.query(Permiso)
            .filter(Permiso.nombre == permiso_codigo)
            .first()
        )

        if not permiso:
            raise HTTPException(
                status_code=404,
                detail=f"Permiso '{permiso_codigo}' no existe"
            )

        # 3. Verificar si el rol tiene el permiso
        tiene_permiso = (
            db.query(RolPermiso)
            .filter(
                RolPermiso.rol_id == cuenta_proyecto.rol_proyecto_id,
                RolPermiso.permiso_id == permiso.id
            )
            .first()
        )

        if not tiene_permiso:
            raise HTTPException(
                status_code=403,
                detail="No tienes permiso para esta acción"
            )

        return True  # autorización exitosa

    return dependency
