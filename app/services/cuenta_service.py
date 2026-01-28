from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.cuenta import Cuenta

class cuenta_service:
    
    def get_cuenta(db:Session, cuenta_id: int):
        return db.query(Cuenta).filter(Cuenta.id == cuenta_id).first()