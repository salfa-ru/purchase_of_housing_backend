from rest_framework import permissions

NOT_OWNER = 'У вас нет прав на изменение этого объявления.'


class IsRealtyOwner(permissions.BasePermission):
    """Менять объявление может только его владелец.

    Работает и с самим объявлением, и с продажей или арендой: у них владелец
    лежит в связанном объявлении."""

    message = NOT_OWNER

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        realty = getattr(obj, 'realty', obj)
        return realty.owner_id == request.user.id
