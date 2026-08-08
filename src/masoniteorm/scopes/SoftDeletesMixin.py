from typing import TYPE_CHECKING

from .SoftDeleteScope import SoftDeleteScope

if TYPE_CHECKING:
    from ..query import QueryBuilder


class SoftDeletesMixin:
    """Global scope class to add soft deleting to models."""

    __deleted_at__ = "deleted_at"

    def boot_SoftDeletesMixin(self, builder):
        builder.set_global_scope(SoftDeleteScope(self.__deleted_at__))

    if TYPE_CHECKING:

        @staticmethod
        def with_trashed() -> QueryBuilder: ...
        @staticmethod
        def only_trashed() -> QueryBuilder: ...
        @staticmethod
        def force_delete() -> QueryBuilder: ...
        @staticmethod
        def restore() -> QueryBuilder: ...

    def get_deleted_at_column(self):
        return self.__deleted_at__
