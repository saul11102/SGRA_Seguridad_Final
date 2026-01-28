from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.rol_proyecto import RolProyecto

class rol_proyecto_service:
    
    def get_rol_proyecto(db:Session, rol_proyecto_id: int):
        return db.query(RolProyecto).filter(RolProyecto.id == rol_proyecto_id).first()