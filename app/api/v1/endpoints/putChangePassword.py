from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Dict, Any
import re
import logging
from datetime import datetime, timedelta

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.core.security import pwd_context
from app.models.token_blacklist import TokenBlacklistModel
from app.models.user import UserModel


router = APIRouter()

# Simple in-memory rate limiter (per-user). For production, use Redis or shared store.
RATE_LIMIT = {}
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 60

logger = logging.getLogger(__name__)


class ChangePasswordSchema(BaseModel):
    current_password: str = Field(..., min_length=8, example="senha_atual123")
    new_password: str = Field(..., min_length=8, example="NovaSenha!23")


class ChangePasswordResponse(BaseModel):
    message: str = Field(..., example="Senha atualizada com sucesso")



class ChangePasswordResponse(BaseModel):
    message: str = Field(..., example="Senha atualizada com sucesso")


@router.put(
    "/password",
    summary="Altera a senha do usuário autenticado",
    description="Recebe a senha atual e a nova senha, valida e atualiza.",
    status_code=status.HTTP_200_OK,
    response_model=ChangePasswordResponse,
    responses={
        200: {
            "description": "Senha atualizada com sucesso",
            "content": {
                "application/json": {
                    "example": {"message": "Senha atualizada com sucesso"}
                }
            },
        },
        400: {"description": "Requisição inválida ou ID de usuário ausente"},
        401: {"description": "Token ausente ou inválido"},
        403: {"description": "Senha atual incorreta"},
        422: {"description": "Erro de validação (política de senha)"},
        429: {"description": "Muitas tentativas, tente novamente mais tarde"},
        500: {"description": "Erro interno do servidor"},
    },
)
async def change_password(
    payload: ChangePasswordSchema,
    request: Request,
    db: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    try:
        # Verify token info set by dependency
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="Token ausente ou inválido")

        user_id = getattr(token_info, "id", None)
        if not user_id:
            raise HTTPException(status_code=401, detail="Token ausente ou inválido")

        # Rate limiting (in-memory)
        now = datetime.utcnow()
        attempts = RATE_LIMIT.get(user_id, [])
        # remove old attempts
        attempts = [ts for ts in attempts if (now - ts).total_seconds() < WINDOW_SECONDS]
        if len(attempts) >= MAX_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Muitas tentativas. Tente novamente mais tarde.")
        # record attempt (we'll keep attempts for both success and failure to slow down brute force)
        attempts.append(now)
        RATE_LIMIT[user_id] = attempts

        # load user
        query_user = await db.execute(
            __import__("sqlalchemy").future.select(UserModel).where(UserModel.id == user_id)
        )
        user = query_user.scalars().first()
        if not user:
            # Do not reveal user existence
            raise HTTPException(status_code=401, detail="Token ausente ou inválido")

        # Validate current password
        if not pwd_context.verify(payload.current_password, user.password):
            raise HTTPException(status_code=403, detail="Senha atual incorreta")

        # Prevent new password equal to current plaintext
        if payload.new_password == payload.current_password:
            raise HTTPException(status_code=422, detail="Nova senha não pode ser igual à senha atual")

        # Password policy: min 8, uppercase, lowercase, digit, special
        policy = (
            r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=[\]{};':\",.<>/?]).{8,}$"
        )
        if not re.match(policy, payload.new_password):
            raise HTTPException(
                status_code=422,
                detail=(
                    "A senha deve ter no mínimo 8 caracteres, incluindo letra maiúscula, "
                    "minúscula, número e caractere especial."
                ),
            )

        # Hash and update password
        user.password = pwd_context.hash(payload.new_password)

        # Invalidate refresh tokens (clear list) and add current access token to blacklist
        try:
            # clear refresh tokens
            user.refresh_token = []

            # try to extract access token from header and blacklist it
            auth_header = request.headers.get("Authorization") or ""
            token = None
            if auth_header.startswith("Bearer "):
                token = auth_header.split("Bearer ")[1]
            if token:
                bl = TokenBlacklistModel(token=token, user_id=user_id)
                db.add(bl)

            db.add(user)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

        # Audit log
        ip = request.client.host if request.client else "unknown"
        logger.info("Password changed for user_id=%s ip=%s", user_id, ip)

        return {"message": "Senha atualizada com sucesso"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Erro ao alterar senha: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor: {str(e)}")
