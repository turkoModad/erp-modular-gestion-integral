from fastapi import APIRouter, Depends
from app.security.dependencies import require_admin 
from app.db.models import Usuario


router = APIRouter()


@router.post("/admin")
def admin_panel(user: Usuario = Depends(require_admin)): 
    return {"message": "Bienvenido, administrador"}