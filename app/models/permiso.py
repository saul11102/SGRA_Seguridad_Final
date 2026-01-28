from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

class Permiso(BaseModelORM):
    __tablename__ = "permisos"
    nombre = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)

    roles_permiso = relationship("RolPermiso", back_populates="permiso", viewonly=True)