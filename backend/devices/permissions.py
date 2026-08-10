from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """Permite el acceso solo a usuarios con rol administrador o superusuarios."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Permite lectura a usuarios autenticados; escritura solo a administradores."""

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_admin or request.user.is_superuser
