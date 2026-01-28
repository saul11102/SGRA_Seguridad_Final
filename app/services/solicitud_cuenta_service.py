from sqlalchemy import case
from sqlalchemy.orm import Session
from ..models.solicitud_cuenta import SolicitudCuenta, EstadoSolicitudEnum
from ..utils.utils import hash_password
from ..models.cuenta import Cuenta, EstadoCuentaEnum
from ..services.utils_pool import PasswordUtils
from ..services.rol_service import rol_service
from typing import Optional, Tuple
from ..models.rol import Rol

class solicitud_cuenta_service:
    def __init__(self, db: Session):
        self.db = db

    def responder_solicitud(self, uuid: str, decision: str) -> str:
        solicitud = self.validar_solicitud(uuid, decision)
        solicitud.estado = EstadoSolicitudEnum[decision]
        if solicitud.estado ==  EstadoSolicitudEnum.APROBADO:
            self.crear_cuenta(solicitud) 
        self.db.commit()
        return "Estado de la solicitud actualizado correctamente"   
    
    def crear_cuenta(self, solicitud: SolicitudCuenta) -> Cuenta:
        try:
            rol = rol_service.get_rol_por_nombre(self.db, "USUARIO_COMUN")

            if rol is None:
                rol = Rol(
                    nombre="USUARIO_COMUN"
                )
                self.db.add(rol)
                self.db.flush()  # Genera el ID sin necesidad de commit

            nueva_cuenta = Cuenta(
                estadoCuenta=EstadoCuentaEnum.ACTIVO,
                rol_id=rol.id
            )
            self.db.add(nueva_cuenta)
            self.db.flush()

            solicitud.cuenta_id = nueva_cuenta.id

            self.db.commit()

            return nueva_cuenta

        except Exception as e:
            self.db.rollback()
            raise ValueError(f"Error al crear la cuenta: {str(e)}")

        

    def validar_solicitud(self, uuid: str, decision: str) -> SolicitudCuenta:
        try:
            decision_enum = EstadoSolicitudEnum[decision]
        except KeyError:
            raise ValueError("La decisión proporcionada no es válida")

        solicitud = self.db.query(SolicitudCuenta).filter(SolicitudCuenta.uuid == uuid).first()
        
        if not solicitud:
            raise ValueError("No existe la solicitud de la cuenta")
        if solicitud.estado != EstadoSolicitudEnum.PENDIENTE:
            raise ValueError("La solicitud no se encuentra en estado 'PENDIENTE'")
        if decision_enum == EstadoSolicitudEnum.PENDIENTE:
            raise ValueError("No se puede cambiar el estado a 'PENDIENTE' nuevamente")
            
        return solicitud

    @staticmethod
    def create_solicitud(db: Session, solicitud_data) -> SolicitudCuenta:
        existing_solicitud = db.query(SolicitudCuenta).filter(SolicitudCuenta.correo == solicitud_data.correo).first()
        if existing_solicitud:
            raise ValueError("El correo ya está en uso.")

        if len(solicitud_data.contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        if not any(c.isupper() for c in solicitud_data.contrasena):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula.")
        if not any(c.islower() for c in solicitud_data.contrasena):
            raise ValueError("La contraseña debe contener al menos una letra minúscula.")
        if not any(c.isdigit() for c in solicitud_data.contrasena):
            raise ValueError("La contraseña debe contener al menos un número.")

        solicitud_data.contrasena = hash_password(solicitud_data.contrasena)
        nueva_solicitud = SolicitudCuenta(**solicitud_data.model_dump())

        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)
        return nueva_solicitud
    
    @staticmethod
    def list_solicitudes(db: Session, skip: int = 0, limit: int = 10) -> Tuple[list[SolicitudCuenta], int]:
        query = db.query(SolicitudCuenta)
        orden_estados = case(
            (SolicitudCuenta.estado == EstadoSolicitudEnum.PENDIENTE, 1),
            (SolicitudCuenta.estado == EstadoSolicitudEnum.APROBADO, 2),
            (SolicitudCuenta.estado == EstadoSolicitudEnum.RECHAZADO, 3),
            else_=4 
        )
        total = query.count()
        solicitudes = query.order_by(orden_estados.asc(), SolicitudCuenta.fecha_solicitud.desc()).offset(skip).limit(limit).all()
        return solicitudes, total

    @staticmethod
    def get_solicitud_por_correo(db: Session, correo: str) -> SolicitudCuenta:
        solicitud = db.query(SolicitudCuenta).filter(SolicitudCuenta.correo == correo).first()
        if not solicitud:
            raise ValueError("Cuenta no encontrada para el correo proporcionado")
        return solicitud

    @staticmethod
    def generar_y_guardar_password_temporal(db: Session, solicitud: SolicitudCuenta) -> str:
        temp_pass = PasswordUtils.generate_temporary_password()
        hashed = PasswordUtils.hash_password(temp_pass)
        solicitud.contrasena = hashed
        db.add(solicitud)
        db.commit()
        db.refresh(solicitud)
        return temp_pass

    @staticmethod
    def enviar_password_temporal(correo: str, temp_pass: str):
        subject = "Recuperación de contraseña"
        body = f"Su contraseña temporal es: {temp_pass}\nPor favor inicie sesión y cambie su contraseña."
        
        sent = PasswordUtils.send_email(correo, subject, body)
        if not sent:
            raise RuntimeError("No se pudo enviar el correo de recuperación")

    @staticmethod
    def recuperar_contrasena_por_correo(db: Session, correo: str):
        solicitud = solicitud_cuenta_service.get_solicitud_por_correo(db, correo)
        temp_pass = solicitud_cuenta_service.generar_y_guardar_password_temporal(db, solicitud)
        solicitud_cuenta_service.enviar_password_temporal(solicitud.correo, temp_pass)
