from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from pydantic import BaseModel
from app.db.session import get_db
from app.models.user import User
from app.core.security import verify_password, create_access_token, hash_password
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str = ""
    role: str = "viewer"


@router.post("/token", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    user.last_login = datetime.utcnow()
    token = create_access_token(user.username)
    return TokenResponse(
        access_token=token,
        user={"id": user.id, "username": user.username, "email": user.email,
              "full_name": user.full_name, "role": user.role},
    )


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email,
            "full_name": user.full_name, "role": user.role, "last_login": user.last_login}


@router.post("/users", status_code=201)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == payload.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already exists")
    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    await db.flush()
    return {"id": user.id, "username": user.username, "role": user.role}
