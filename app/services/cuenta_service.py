from sqlalchemy.orm import Session
from ..models.cuenta import Cuenta, EstadoCuentaEnum
from ..models.rol import Rol
from uuid import UUID

class cuenta_service:
    def __init__(self, db: Session):
        self.db = db
    
    def get_cuenta(self, cuenta_id: int) -> Cuenta:
        cuenta = self.db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        return cuenta

    def asignar_rol(self, uuid: str, rol_nombre: str) -> str:
        rol_nombre = rol_nombre.strip().upper()
        cuenta = self.validar_cuenta(uuid)
        rol = self.validar_rol(rol_nombre, cuenta)
        
        cuenta.rol_id = rol.id
        self.db.commit()  
        return "Rol asignado correctamente"
        
    def validar_cuenta(self, uuid: str) -> Cuenta:
        cuenta = self.db.query(Cuenta).filter(Cuenta.uuid == uuid).first()
        if not cuenta:
            raise ValueError("No existe la cuenta")
        if cuenta.estadoCuenta == EstadoCuentaEnum.INACTIVO:
            raise ValueError("La cuenta se encuentra inactiva")
        return cuenta
    
    def validar_rol(self, rol: str, cuenta: Cuenta) -> Rol:
        aux_rol = self.db.query(Rol).filter(Rol.nombre == rol).first()
        if not aux_rol:
            raise ValueError("No existe el rol especificado")
        if cuenta.rol_id == aux_rol.id:
            raise ValueError("La cuenta ya tiene este rol asignado")
        return aux_rol

    def desactivar_cuenta(self, cuenta_id: int) -> Cuenta:
        cuenta = self.get_cuenta(cuenta_id)
        
        cuenta.estadoCuenta = EstadoCuentaEnum.INACTIVO
        self.db.add(cuenta)
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

    def get_cuentas(self) -> list[Cuenta]:
        """
        Devuelve todos los usuarios (cuentas) del sistema.
        """
        return self.db.query(Cuenta).all()
    
    def actualizar_estado_cuenta(self, cuenta_uuid: UUID, nuevo_estado: EstadoCuentaEnum) -> Cuenta:
        cuenta = self.db.query(Cuenta).filter(Cuenta.uuid == str(cuenta_uuid)).first()
        if not cuenta:
            raise ValueError("Cuenta no encontrada")
        
        cuenta.estadoCuenta = nuevo_estado
        self.db.add(cuenta)
        self.db.commit()
        self.db.refresh(cuenta)
        return cuenta

