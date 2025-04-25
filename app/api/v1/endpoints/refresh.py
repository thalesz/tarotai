from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import UserModel
from app.services.token import TokenAccessSchema, TokenRefreshSchema
from app.core.deps import get_session
from datetime import timedelta
from app.schemas.user import UserSchemaBase, UserSchemaUpdate
from pydantic import BaseModel
from app.core.configs import settings  # Import the settings object

router = APIRouter()


@router.post(
    "/",
    response_model=TokenAccessSchema,
    summary="Renovar o Token de Acesso",
    description="Renova o token de acesso utilizando um refresh token válido. Retorna um novo token de acesso.",
    responses={
        200: {
            "description": "Token de acesso renovado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "novo_access_token_gerado",
                        "refresh_token": "refresh_token_utilizado",
                        "token_type": "bearer",
                    }
                }
            },
        },
        400: {
            "description": "O refresh token não foi fornecido no corpo da requisição.",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh token é obrigatório"}
                }
            },
        },
        401: {
            "description": "Token inválido ou não autorizado.",
            "content": {
                "application/json": {"example": {"detail": "Refresh token inválido"}}
            },
        },
        403: {
            "description": "Token expirado.",
            "content": {
                "application/json": {"example": {"detail": "Refresh token expirado"}}
            },
        },
        404: {
            "description": "Usuário associado ao refresh token não encontrado.",
            "content": {
                "application/json": {"example": {"detail": "Usuário não encontrado"}}
            },
        },
        422: {
            "description": "Erro de validação nos dados enviados.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["body", "refresh_token"],
                                "msg": "Field required",
                                "input": {},
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def refresh_access_token(
    request: TokenRefreshSchema, db: AsyncSession = Depends(get_session)
):
    """
    Endpoint para renovar o token de acesso utilizando um token de atualização (refresh token).
    Esse endpoint valida o refresh token fornecido e retorna um novo token de acesso.
    Se o refresh token estiver expirado ou inválido, ele será removido do banco de dados, caso esteja associado a um usuário.

    - **refresh_token**: Token de atualização do usuário.
    """
    refresh_token = request.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token é obrigatório",
        )

    # Decodifica o refresh token
    payload = {}
    try:
        payload = TokenRefreshSchema.decode_token(
            refresh_token, settings.REFRESH_SECRET_KEY, settings.ALGORITHM
        )
    except HTTPException as e:
        if e.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]:
            await UserSchemaBase.remove_refresh_token(
                db, refresh_token, payload.get("id")
            )
        raise e

    user_id = payload.get("id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: falta o campo 'id'",
        )

    user: UserSchemaUpdate = await UserSchemaUpdate.get_user_by_id(db, user_id)

    if refresh_token not in user.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido",
        )

    new_access_token = TokenRefreshSchema.create_token(
        data={
            "sub": user.username,
            "id": user.id,
            "email": user.email,
            "user_type": user.user_type,
            "status": user.status,
            "full_name": user.full_name,
            "birth_date": user.birth_date,
            "birth_time": user.birth_time,
        },
        secret_key=settings.ACCESS_SECRET_KEY,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenAccessSchema(
        access_token=new_access_token, refresh_token=refresh_token, token_type="Bearer"
    )
