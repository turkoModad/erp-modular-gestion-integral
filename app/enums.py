import enum

class AccountStatus(enum.Enum):
    active = "active"
    pending = "pending"
    banned = "banned"
    deleted = "deleted"


class Role(enum.Enum):
    ADMIN = "ADMIN"
    CLIENT = "CLIENTE"
    STOCK_MANAGER = "GESTOR_STOCK"
    SALES_MANAGER = "GESTOR_VENTAS"