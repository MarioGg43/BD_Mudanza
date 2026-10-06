"""Los permisos viven en usuarios.permisos; se reexportan para las vistas de pedidos."""
from usuarios.permisos import requiere_permiso, tiene_permiso  # noqa: F401
