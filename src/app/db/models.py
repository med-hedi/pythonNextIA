"""Point d'import unique de tous les modèles.

Alembic importe ce module pour découvrir les tables (autogenerate) :
pensez à y ajouter chaque nouveau modèle.
"""

from app.db.base import Base
from app.modules.items.models import Item

__all__ = ["Base", "Item"]
