from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from ..models.solicitud_cuenta import SolicitudCuenta, EstadoSolicitudEnum
from ..models.cuenta import Cuenta, EstadoCuentaEnum
from ..core.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM
from ..utils.utils import verify_password
from ..core.get_db import get_db
from ..schemas.auth_schema import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def login(db: Session, correo: str, contrasena: str):
    # Buscar solicitud con correo, estado APROBADO y que tenga cuenta asociada
    solicitud = db.query(SolicitudCuenta).filter(
        SolicitudCuenta.correo == correo,
        SolicitudCuenta.estado == EstadoSolicitudEnum.APROBADO,
        SolicitudCuenta.cuenta_id.isnot(None)
    ).first()
    
    if not solicitud:
        raise ValueError("Credenciales inválidas")
    
    # Verificar contraseña
    if not verify_password(contrasena, solicitud.contrasena):
        raise ValueError("Credenciales inválidas")
    
    # Verificar que la cuenta esté activa
    cuenta = solicitud.cuenta
    if not cuenta or cuenta.estadoCuenta != EstadoCuentaEnum.ACTIVO:
        raise ValueError("Cuenta inactiva o no encontrada")

    # Generar JWT con la info mínima funcional
    token_data = {
        "rol_id": cuenta.rol_id,
        "uuid": str(cuenta.uuid)
    }
    access_token = create_access_token(subject=str(cuenta.id), data=token_data)

    return {
        "uuid": str(cuenta.uuid),
        "nombre": solicitud.nombre,
        "apellido": solicitud.apellido,
        "rol": cuenta.rol.nombre,
        "access_token": access_token,
        "token_type": "bearer"
    }

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Cuenta:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(id=user_id)
    except JWTError:
        raise credentials_exception
    
    user = db.query(Cuenta).filter(Cuenta.id == token_data.id).first()
    if user is None:
        raise credentials_exception
    
    if user.estadoCuenta != EstadoCuentaEnum.ACTIVO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="La cuenta está inactiva",
        )
        
    return user

