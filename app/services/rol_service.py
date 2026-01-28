from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.rol import Rol

class rol_service:
    
    def get_rol(db:Session, rol_id: int):
        return db.query(Rol).filter(Rol.id == rol_id).first()
    
    def get_roles(db: Session):
        """
        Devuelve todos los roles del sistema.
        """
        return db.query(Rol).all()
    
    @staticmethod
    def get_rol_por_nombre(db: Session, nombre: str):
        """
        Devuelve un rol por su nombre.
        """
        return db.query(Rol).filter(Rol.nombre == nombre).first()