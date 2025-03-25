from sqlalchemy.orm import Session
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import EmailStr
from app.enums import Role, AccountStatus
from app.security.dependencies import require_admin 
from app.db.models.models import Usuario
from app.db.database import get_db
from app.admin.schemas import UsersSchema, UserUpdateRequest, UsuarioStatus
from app.security.hashing import hash_password, verify_password
import logging


router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



@router.post("/admin/")
def admin_panel(user: Usuario = Depends(require_admin)): 
    return {"message": "Bienvenido, administrador"}


@router.post("/admin/lista_usuarios", response_model= List[UsersSchema])
def lista_usuarios(user: Usuario = Depends(require_admin), db: Session = Depends(get_db)):
    usuarios = db.query(Usuario).all()
    return usuarios


@router.put("/admin/elegir_estado/{email}")
def elegir_estado(
    email: EmailStr,
    datos: UsuarioStatus, 
    admin: Usuario = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    try:
        usuario = db.query(Usuario).filter(Usuario.email == email).first()
        if not usuario:
            logger.warning(f"Intento de actualizar estado de usuario inexistente: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )
        
        if not datos.new_status or datos.new_status == None:
            logger.info("Solicitud de actualización de estado sin cambios")
            return {"message": "No se proporcionó un nuevo estado"}

        try:
            new_status = AccountStatus(datos.new_status)
        except ValueError:
            valid_statuses = [s.value for s in AccountStatus]
            logger.error(f"Intento de asignar estado inválido: {datos.new_status}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Estado inválido. Opciones válidas: {valid_statuses}"
            )

        # Verificar si hay cambios reales
        if usuario.account_status == new_status:
            logger.info(f"Estado actual ya es {new_status} para usuario {email}")
            return {"message": "El estado actual es igual al solicitado"}

        # Actualizar estado
        usuario.account_status = new_status
        db.commit()
        db.refresh(usuario)
        
        logger.info(f"Usuario {email} actualizado a estado {new_status} por admin {admin.email}")

        return {
            "message": "Estado actualizado correctamente",
            "email": usuario.email,
            "nuevo_estado": usuario.account_status.value
        }

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error inesperado actualizando estado: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al actualizar el estado"
        )


@router.put("/admin/actualizar_usuario/{email}")
def actualizar_usuario(
    email: EmailStr,
    datos: UserUpdateRequest,
    db: Session = Depends(get_db),
    admin: Usuario = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.email == email).first() 
    logger.info(f"Iniciando proceso de actualización para usuario con correo electrónico: {email}")   
    if not usuario:
        logger.error("Usuario no encontrado.")
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    cambios = False

    if datos.email and datos.email != usuario.email:
        logger.info(f"Verificando disponibilidad del correo electrónico: {datos.email}")
        email_existente = db.query(Usuario).filter(Usuario.email == datos.email).first()
        if email_existente:
            logger.error("El nuevo correo electrónico ya está en uso.")
            raise HTTPException(status_code=400, detail="El nuevo email ya está en uso")
        usuario.email = datos.email
        cambios = True

    if datos.two_factor_enabled is not None and usuario.two_factor_enabled != datos.two_factor_enabled:
        logger.info(f"Actualizando el estado de 2FA para el usuario: {usuario.id}")
        usuario.two_factor_enabled = datos.two_factor_enabled
        cambios = True

    if datos.password:
        if not verify_password(datos.password, usuario.password_hash): 
            logger.info("Contraseña cambiada con éxito.") 
            usuario.password_hash = hash_password(datos.password)  
            cambios = True

    if datos.role:
        try:
            if datos.role != Role(usuario.role):
                usuario.role = datos.role.name
                cambios = True
                logger.info(f"Rol actualizado a: {datos.role.name}")

        except ValueError as e:
            logger.error(f"Rol inválido: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rol inválido. Opciones válidas: {[r.value for r in Role]}"
            )
        
    if not cambios:
        logger.info("No se actualizo ningun dato")
        return {"message": "No se actualizó ningún dato"}

    db.commit()
    db.refresh(usuario)

    return {
        "message": "Usuario actualizado correctamente",
        "user": {
            "email": usuario.email,
            "two_factor_enabled": usuario.two_factor_enabled,
            "role": usuario.role
        }
    }