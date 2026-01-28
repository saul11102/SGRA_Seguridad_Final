from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.solicitud_cuenta import SolicitudCuenta

class solicitud_cuenta_service:
    
    def create_solicitud(db:Session, solicitud_data):
        nueva_solicitud = SolicitudCuenta(**solicitud_data.dict())
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)
        return nueva_solicitud