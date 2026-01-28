from sqlalchemy.orm import Session
from ..models.ejemplo import Ejemplo
from ..schemas.ejemplo_schema import EjemploCreate

class EjemploService:
    def __init__(self, db: Session):
        self.db = db

    def crear_ejemplo(self, datos: EjemploCreate) -> Ejemplo:
        nuevo = Ejemplo(nombre=datos.nombre, descripcion=datos.descripcion)
        self.db.add(nuevo)
        self.db.commit()
        self.db.refresh(nuevo)
        return nuevo

    def obtener_todos(self):
        return self.db.query(Ejemplo).all()
