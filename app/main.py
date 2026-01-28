from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.controllers import ejemplo_controller, cuenta_controller, cuenta_proyecto_controller, rol_controller, rol_proyecto_controller, solicitud_controller, proyecto_controller
from app.models import solicitud_cuenta, cuenta, cuenta_proyecto, rol, rol_proyecto, proyecto
from app.config.database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="API de SGRA",
    description="Una API para la gestión de requisitos ágiles",
    version="0.1.0"
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

app.include_router(ejemplo_controller.rol_controller.router)
app.include_router(cuenta_controller.cuenta_controller.router)
app.include_router(cuenta_proyecto_controller.cuenta_proyecto_controller.router)
app.include_router(rol_controller.rol_controller.router)
app.include_router(rol_proyecto_controller.rol_proyecto_controller.router)
app.include_router(solicitud_controller.solicitud_controller.router)
app.include_router(proyecto_controller.router)





def run():
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
