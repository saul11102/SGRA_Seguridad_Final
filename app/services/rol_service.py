from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.rol import Rol

class rol_service:
    
    def get_rol(db:Session, rol_id: int):
        return db.query(Rol).filter(Rol.id == rol_id).first()