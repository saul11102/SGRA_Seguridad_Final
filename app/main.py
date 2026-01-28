from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import (
    ejemplo_controller,
    cuenta_controller,
    cuenta_proyecto_controller,
    rol_controller,
    rol_proyecto_controller,
    solicitud_controller,
    proyecto_controller,
    requisito_controller,
    historia_usuario_controller,
    tarea_controller,
    sprint_controller,
    defecto_controller,
)
from app.models import (
    solicitud_cuenta,
    cuenta,
    cuenta_proyecto,
    rol,
    rol_proyecto,
    proyecto,
    requisito,
    historia_usuario,
    historial_requisito,
    permiso,
    rol_permiso,
    tarea,
    historial_tarea,
    sprint,
    defecto,
    historial_defecto,
)
from app.config.database import engine, Base
from app.services import historial_requisito_service
from app.services import historial_tarea_service


Base.metadata.create_all(bind=engine)

# print("TABLAS REGISTRADAS ANTES:", Base.metadata.tables.keys())
# Base.metadata.drop_all(bind=engine)
# Base.metadata.create_all(bind=engine)
# print("TABLAS REGISTRADAS DESPUES:", Base.metadata.tables.keys())

app = FastAPI(
    title="API de SGRA",
    description="Una API para la gestión de requisitos ágiles",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"RUTA": "BASE"}


app.include_router(proyecto_controller.router)
app.include_router(ejemplo_controller.ejemplo_controller.router)
app.include_router(cuenta_controller.cuenta_controller.router)
app.include_router(cuenta_proyecto_controller.cuenta_proyecto_controller.router)
app.include_router(rol_controller.rol_controller.router)
app.include_router(rol_proyecto_controller.rol_proyecto_controller.router)
app.include_router(solicitud_controller.solicitud_controller.router)
app.include_router(requisito_controller.requisito_controller.router)
app.include_router(historia_usuario_controller.historia_usuario_controller.router)
app.include_router(tarea_controller.tarea_controller.router)
app.include_router(sprint_controller.router)
app.include_router(defecto_controller.defecto_controller.router)


def run():
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
