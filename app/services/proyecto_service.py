from sqlalchemy.orm import Session
from ..models.proyecto import Proyecto
from ..schemas.proyecto_schema import ProyectoCreate

class ProyectoService:
    def __init__(self, db: Session):
        self.db = db

    def create_proyecto(self, proyecto: ProyectoCreate):
        db_proyecto = Proyecto(nombre=proyecto.nombre, descripcion=proyecto.descripcion)
        self.db.add(db_proyecto)
        self.db.commit()
        self.db.refresh(db_proyecto)
        return db_proyecto

    def get_proyecto(self, proyecto_id: int):
        return self.db.query(Proyecto).filter(Proyecto.id == proyecto_id).first()

    def get_proyectos(self):
        return self.db.query(Proyecto).all()
