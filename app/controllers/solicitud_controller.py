from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional 
from app.schemas.solicitud_cuenta_schema import CreateSolicitud, ResponseSolicitud
from sqlalchemy.orm import Session
from app.core.get_db import get_db
from app.services.solicitud_cuenta_service import solicitud_cuenta_service

class solicitud_controller:
    
    router = APIRouter(prefix="/solicitud", tags=["Solicitud"])

    @router.post("/crear-solicitud", response_model= ResponseSolicitud, status_code= status.HTTP_200_OK)
    def crear_solicitud(datos: CreateSolicitud, db: Session = Depends(get_db)):        
        try:
            solicitud_cuenta_service.create_solicitud(db, datos)
        except Exception as e:
            raise HTTPException(status_code= status.HTTP_400_BAD_REQUEST, detail= str(e))
        return ResponseSolicitud(msg="solicitud creada", code= 200)