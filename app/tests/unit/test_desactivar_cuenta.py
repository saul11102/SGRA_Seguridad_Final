import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.get_db import get_db
from app.models.base_model_orm import BaseModelORM
from app.models.cuenta import Cuenta, EstadoCuentaEnum
from app.models.rol import Rol

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Crear las tablas necesarias en la base de datos
BaseModelORM.metadata.create_all(bind=engine)

client = TestClient(app)

@pytest.fixture(autouse=True)
def limpiar_bd():
    db = TestingSessionLocal()
    db.query(Cuenta).delete()
    db.commit()
    db.close()

def test_01_desactivar_cuenta_correcta():
    db = TestingSessionLocal()
    rol = Rol(nombre="rol_test")
    db.add(rol)
    db.commit()
    db.refresh(rol)

    cuenta = Cuenta(
        uuid="123e4567-e89b-12d3-a456-426614174001",
        estadoCuenta=EstadoCuentaEnum.ACTIVO,
        rol_id=rol.id
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)

    # Desactivar cuenta correctamente
    response = client.post(f"/Cuenta/{cuenta.uuid}/estado", json={"estadoCuenta": "INACTIVO"})

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data["msg"] == "Estado de la cuenta actualizado correctamente"
    assert json_data["data"]["estadoCuenta"] == "INACTIVO"
    assert json_data["data"]["uuid"] == str(cuenta.uuid)

    # Verificar que el estado de la cuenta se actualizó correctamente en la DB
    db2 = TestingSessionLocal()
    cuenta_db = db2.query(Cuenta).filter(Cuenta.uuid == cuenta.uuid).first()
    assert cuenta_db.estadoCuenta == EstadoCuentaEnum.INACTIVO
    db2.close()
    db.close()

def test_02_desactivar_cuenta_no_existente():
    # Intentar desactivar una cuenta que no existe
    response = client.post("/Cuenta/9999-9999-9999-9999-9999-9999-9999-9999/estado", json={"estadoCuenta": "INACTIVO"})

    assert response.status_code == 404
    json_data = response.json()
    assert json_data["detail"] == "Cuenta no encontrada"

def test_03_errores_estado_invalido():
    # Probar un valor de estado inválido
    response = client.post("/Cuenta/124e4567-e89b-12d3-a456-426614174002/estado", json={"estadoCuenta": "ACTIASVO"})

    assert response.status_code == 422  # Error 422 es para validaciones de Pydantic
    json_data = response.json()
    assert "detail" in json_data
    assert json_data["detail"][0]["msg"] == "Por favor, elija un valor válido: 'INACTIVO' o 'ACTIVO'"
    assert json_data["detail"][0]["input"] == "ACTIASVO"
    
def test_04_activar_cuenta():
    # Crear una cuenta en estado INACTIVO para probar la activación
    db = TestingSessionLocal()
    rol = Rol(nombre="rol_test")
    db.add(rol)
    db.commit()
    db.refresh(rol)

    cuenta = Cuenta(
        uuid="124e4567-e89b-12d3-a456-426614174002",
        estadoCuenta=EstadoCuentaEnum.INACTIVO,
        rol_id=rol.id
    )
    db.add(cuenta)
    db.commit()
    db.refresh(cuenta)

    # Activar cuenta
    response = client.post(f"/cuentas/{cuenta.uuid}/estado", json={"estadoCuenta": "ACTIVO"})

    assert response.status_code == 200
    json_data = response.json()
    assert json_data["code"] == 200
    assert json_data["msg"] == "Estado de la cuenta actualizado correctamente"
    assert json_data["data"]["estadoCuenta"] == "ACTIVO"
    assert json_data["data"]["uuid"] == str(cuenta.uuid)

    # Verificar que el estado de la cuenta se actualizó correctamente a ACTIVO
    db2 = TestingSessionLocal()
    cuenta_db = db2.query(Cuenta).filter(Cuenta.uuid == cuenta.uuid).first()
    assert cuenta_db.estadoCuenta == EstadoCuentaEnum.ACTIVO
    db2.close()
    db.close()
