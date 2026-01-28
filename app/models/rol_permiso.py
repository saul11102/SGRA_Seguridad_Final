from app.models.base_model_orm import BaseModelORM
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

class RolPermiso(BaseModelORM):
    __tablename__ = "roles_permisos"
    
    rol_id = Column(Integer, ForeignKey("roles_proyecto.id"), nullable=False)
    permiso_id = Column(Integer, ForeignKey("permisos.id"), nullable=False)

    rol = relationship("RolProyecto", back_populates="permisos_rol")
    permiso = relationship("Permiso", back_populates="roles_permiso", viewonly=True)
