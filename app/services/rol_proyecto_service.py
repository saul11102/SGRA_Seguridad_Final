from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.rol_proyecto import RolProyecto
from ..models.rol_permiso import RolPermiso
from ..models.permiso import Permiso
from ..models.cuenta_proyecto import CuentaProyecto

from ..schemas.rol_proyecto_schema import RolProyectoCreate
from ..schemas.permiso_schema import PermisoCreate
from ..schemas.rol_permiso_schema import RolPermisoCreate
from ..schemas.cuenta_proyecto_schema import AsignarRolCuentaProyecto
from ..models.proyecto import Proyecto
from sqlalchemy.orm import joinedload
from ..models.cuenta import Cuenta


class RolProyectoService:

    def __init__(self, db: Session):
        self.db = db

    # -----------------------
    #   Crear RolProyecto
    # -----------------------
    
    def crear_rol(self, data: RolProyectoCreate):

        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == data.proyecto_uuid).first()
        if not proyecto:
            raise HTTPException(404, f"Proyecto con UUID {data.proyecto_uuid} no encontrado.")

        rol = RolProyecto(
            nombre=data.nombre,
            descripcion=data.descripcion,
            proyecto_id=proyecto.id   # ✅ ID real
        )

        self.db.add(rol)
        self.db.commit()
        self.db.refresh(rol)

        permisos_agregados = []

        if data.permisos_uuids:
            for permiso_uuid in data.permisos_uuids:
                permiso = self.db.query(Permiso).filter(Permiso.uuid == permiso_uuid).first()
                if not permiso:
                    raise HTTPException(404, f"Permiso con UUID {permiso_uuid} no encontrado.")

                rol_permiso = RolPermiso(
                    rol_id=rol.id,
                    permiso_id=permiso.id
                )
                self.db.add(rol_permiso)
                permisos_agregados.append(permiso)

        self.db.commit()
        self.db.refresh(rol)

        return rol, permisos_agregados

    # -----------------------
    #   Crear Permiso
    # -----------------------
    def crear_permiso(self, data: PermisoCreate):
        if self.db.query(Permiso).filter(Permiso.nombre == data.nombre).first():
            raise HTTPException(status_code=400, detail="Ya existe un permiso con ese nombre.")

        permiso = Permiso(**data.model_dump())
        self.db.add(permiso)
        self.db.commit()
        self.db.refresh(permiso)

        return permiso

    # ---------------------------------------------------
    #   Asociar Permiso a RolProyecto (RolPermiso)
    # ---------------------------------------------------
    def asignar_permiso_a_rol(self, rol_uuid: str, permiso_uuid: str):

        rol = self.db.query(RolProyecto).filter(RolProyecto.uuid == rol_uuid).first()
        if not rol:
            raise HTTPException(status_code=404, detail="RolProyecto no encontrado.")

        permiso = self.db.query(Permiso).filter(Permiso.uuid == permiso_uuid).first()
        if not permiso:
            raise HTTPException(status_code=404, detail="Permiso no encontrado.")

        existe = (
            self.db.query(RolPermiso)
            .filter(
                RolPermiso.rol_id == rol.id,
                RolPermiso.permiso_id == permiso.id
            )
            .first()
        )

        if existe:
            raise HTTPException(status_code=400, detail="Este rol ya tiene asignado este permiso.")

        relacion = RolPermiso(
            rol_id=rol.id,
            permiso_id=permiso.id
        )

        self.db.add(relacion)
        self.db.commit()
        return relacion

    # ------------------------------------------------------
    #   Asignar RolProyecto a un CuentaProyecto existente
    # ------------------------------------------------------
    def asignar_rol_a_cuenta_proyecto(self, data: AsignarRolCuentaProyecto):

        cuenta_proyecto = self.db.query(CuentaProyecto).filter(
            CuentaProyecto.uuid == data.cuenta_uuid
        ).first()

        if not cuenta_proyecto:
            raise HTTPException(404, "La cuenta no pertenece al proyecto")

        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == data.proyecto_uuid).first()

        if not proyecto:
            raise HTTPException(404, "Proyecto no encontrado")

        rol = self.db.query(RolProyecto).filter(RolProyecto.uuid == data.rol_proyecto_uuid).first()
        if not rol:
            raise HTTPException(404, "RolProyecto no encontrado")

        if rol.proyecto_id != proyecto.id:
            raise HTTPException(400, "El rol no pertenece al proyecto")

        cuenta_proyecto.rol_proyecto_id = rol.id
        self.db.commit()
        self.db.refresh(cuenta_proyecto)

        return cuenta_proyecto




    def listar_roles_por_proyecto(self, uuid_proyecto: str):

        proyecto = self.db.query(Proyecto).filter(Proyecto.uuid == uuid_proyecto).first()
        if not proyecto:
            raise HTTPException(404, "Proyecto no encontrado")

        roles = (
            self.db.query(RolProyecto)
            .filter(RolProyecto.proyecto_id == proyecto.id)   # ✅ ID real
            .options(
                joinedload(RolProyecto.permisos_rol)
                .joinedload(RolPermiso.permiso)
            )
            .all()
        )

        for r in roles:
            r.permisos = [rp.permiso for rp in r.permisos_rol]

        return roles

    def obtener_rol(self, uuid_rol: str):
        rol = (
            self.db.query(RolProyecto)
            .filter(RolProyecto.uuid == uuid_rol)
            .options(
                joinedload(RolProyecto.permisos_rol)
                .joinedload(RolPermiso.permiso)
            )
            .first()
        )

        if not rol:
            raise HTTPException(status_code=404, detail="Rol no encontrado")

        rol.permisos = [rp.permiso for rp in rol.permisos_rol]

        return rol

    def listar_permisos(self):
        return self.db.query(Permiso).all()
    
    def listar_rol_proyecto(self):
        roles = roles = self.db.query(RolProyecto).options(
                joinedload(RolProyecto.permisos_rol)
                .joinedload(RolPermiso.permiso)
            ).all()

        for r in roles:
            r.permisos = [rp.permiso for rp in r.permisos_rol]
        
        return roles
    

    def listar_usuarios_por_proyecto(self, uuid_proyecto: str):
        proyecto = (
            self.db.query(Proyecto)
            .filter(Proyecto.uuid == uuid_proyecto)
            .first()
        )

        if not proyecto:
            raise HTTPException(
                status_code=404,
                detail="Proyecto no encontrado"
            )

        cuentas_proyecto = (
            self.db.query(CuentaProyecto)
            .options(
                joinedload(CuentaProyecto.cuenta),
                joinedload(CuentaProyecto.rol_proyecto)
                    .joinedload(RolProyecto.permisos_rol)
                    .joinedload(RolPermiso.permiso)
            )
            .filter(CuentaProyecto.proyecto_id == proyecto.id)
            .all()
        )

        resultado = []

        for cp in cuentas_proyecto:

            permisos = []
            if cp.rol_proyecto:
                for rp in cp.rol_proyecto.permisos_rol:
                    permisos.append({
                        "permiso_uuid": rp.permiso.uuid,
                        "permiso_nombre": rp.permiso.nombre,
                        "permiso_descripcion": rp.permiso.descripcion
                    })

            resultado.append({
                "uuid": cp.uuid,
                "cuenta_uuid": cp.cuenta.uuid,
                "nombre": cp.cuenta.solicitud.nombre + " " +cp.cuenta.solicitud.apellido,
                "correo": cp.cuenta.solicitud.correo,
                "rol_uuid": cp.rol_proyecto.uuid if cp.rol_proyecto else None,
                "rol_nombre": cp.rol_proyecto.nombre if cp.rol_proyecto else None,
                "permisos": permisos
            })

        return resultado


    def update_permisos_rol_proyecto(self, rol_proyecto_uuid: str, permisos_uuids: list[str]):
        rol_proyecto = self.db.query(RolProyecto).filter(RolProyecto.uuid == rol_proyecto_uuid).first()
        if not rol_proyecto:
            raise ValueError("Rol de proyecto no encontrado.")

        # Eliminar permisos existentes
        self.db.query(RolPermiso).filter(RolPermiso.rol_id == rol_proyecto.id).delete()

        # Asignar nuevos permisos
        for permiso_uuid in permisos_uuids:
            permiso = self.db.query(Permiso).filter(Permiso.uuid == permiso_uuid).first()
            if not permiso:
                self.db.rollback()
                raise ValueError(f"Permiso con UUID {permiso_uuid} no encontrado.")
            
            rol_permiso = RolPermiso(rol_id=rol_proyecto.id, permiso_id=permiso.id)
            self.db.add(rol_permiso)
        
        self.db.commit()
        return rol_proyecto

    def delete_rol_proyecto(self, rol_proyecto_uuid: str):
        rol_proyecto = self.db.query(RolProyecto).filter(RolProyecto.uuid == rol_proyecto_uuid).first()
        if not rol_proyecto:
            raise ValueError("Rol de proyecto no encontrado.")

        # Verificar si el rol está en uso
        cuenta_usando_rol = self.db.query(CuentaProyecto).filter(CuentaProyecto.rol_proyecto_id == rol_proyecto.id).first()
        if cuenta_usando_rol:
            raise ValueError("El rol está en uso y no puede ser eliminado.")

        # Eliminar asociaciones de permisos
        self.db.query(RolPermiso).filter(RolPermiso.rol_id == rol_proyecto.id).delete()

        # Eliminar el rol
        self.db.delete(rol_proyecto)
        self.db.commit()

