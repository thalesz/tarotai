from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import any_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import UserModel
from app.core.deps import get_session
from app.services.token import TokenRefreshSchema
from app.schemas.user import UserSchemaUpdate

router = APIRouter()
@router.post(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Realizar Logout do usuário",
    responses={
        204: {
            "description": "Logout realizado com sucesso.",
        },
        400: {
            "description": "Refresh token é obrigatório.",
            "content": {
                "application/json": {
                    "example": {"detail": "Refresh token é obrigatório."}
                }
            },
        },
        404: {
            "description": "Usuário não encontrado ou token inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "Usuário não encontrado ou token inválido."}
                }
            },
        },
        422: {
            "description": "Erro de validação.",
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
        500: {
            "description": "Erro interno do servidor ao tentar realizar o logout.",
            "content": {
                "application/json": {"example": {"detail": "Erro interno do servidor."}}
            },
        },
    },
)
async def logout(request: TokenRefreshSchema, db: AsyncSession = Depends(get_session)):
    """
    Faz logout do usuário, invalidando o refresh token fornecido.

    - **refresh_token**: Obrigatório. Token de atualização do usuário.

    Possíveis respostas:
    - **204 No Content**: Logout realizado com sucesso.
    - **400 Bad Request**: Quando o refresh token não é fornecido.
    - **404 Not Found**: Quando o usuário não é encontrado ou o token não é válido.
    - **422 Unprocessable Entity**: Quando há erro de validação no corpo da requisição.
    - **500 Internal Server Error**: Quando ocorre um erro inesperado no servidor.
    """
    # Obtém o refresh token da requisição
    refresh_token = request.refresh_token

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token é obrigatório.",
        )
        
    # Busca o usuário associado ao refresh token no banco de dados
    user: UserSchemaUpdate = await UserSchemaUpdate.get_user_by_refresh_token(db, refresh_token)

    await UserSchemaUpdate.remove_refresh_token(db,  user.id, refresh_token,)

    return None
