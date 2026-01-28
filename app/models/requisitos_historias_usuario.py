from sqlalchemy import Table, Column, Integer, ForeignKey
from app.models.base_model_orm import BaseModelORM

requisitos_historias_usuario = Table(
    "requisitos_historias_usuario",
    BaseModelORM.metadata,
    Column("requisito_id", Integer, ForeignKey("requisitos.id"), primary_key=True),
    Column("historia_usuario_id", Integer, ForeignKey("historias_usuario.id"), primary_key=True)
)