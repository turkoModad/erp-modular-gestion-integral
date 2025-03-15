from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.security.schemas import UsuarioCreate,OAuth2EmailPasswordRequestForm, UsuarioOut
from app.db.modelos import Usuario
from app.security.hashing import verify_password, hash_password
from app.security.jwt import create_access_token, get_current_user


router = APIRouter()


@router.post("/registro/", response_model=UsuarioOut)
def register(user: UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(Usuario).filter(Usuario.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    hashed_password = hash_password(user.password)
    new_user = Usuario(
        nombre = user.nombre, 
        email = user.email, 
        password = hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user



@router.post("/login")
async def login(form_data: OAuth2EmailPasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.email == form_data.email).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}



@router.get("/users/me", response_model=UsuarioOut)
async def read_users_me(current_user: Usuario = Depends(get_current_user)):
    return current_user