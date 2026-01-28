from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.cuenta_proyecto import CuentaProyecto

class cuenta_proyecto_service:
    
    def get_cuenta_proyecto(db:Session, cuenta_proyecto_id: int):
        return db.query(CuentaProyecto).filter(CuentaProyecto.id == cuenta_proyecto_id).first()