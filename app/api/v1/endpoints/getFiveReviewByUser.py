from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, conint
from typing import Dict, Any

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.draw import DrawSchemaBase
from app.schemas.review import ReviewSchemaBase

router = APIRouter()

# Pydantic model para validar o body da requisição
class ReviewCreateRequest(BaseModel):
    draw: int = Field(..., description="ID do sorteio", example=123)
    rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5", example=5)
    comment: str = Field("", description="Comentário do usuário", example="Muito bom!")

@router.get(
    "/user/{count}",
    summary="Retorna 5 avaliações de um usuário específico de acordo com o count, count 1 sendo os 5 primeiros",
    description="""
Retorna 5 avaliações de um usuário específico de acordo com o count, count 1 sendo os 5 primeiros.
""",
    response_description="Detalhes das avaliações retornadas",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Avaliações retornadas com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Avaliações retornadas com sucesso.",
                        "reviews": [
                            {
                                "id": 1,
                                "user": 1,
                                "draw": 1,
                                "rating": 5,
                                "comment": "Leitura correspondeu com a realidade!",
                                "created_at": "2023-10-10T10:00:00Z"
                            },
                            {
                                "id": 2,
                                "user": 1,
                                "draw": 2,
                                "rating": 4,
                                "comment": "Me senti seguro lendo a interpretação!",
                                "created_at": "2023-10-10T10:00:00Z"
                            }
                        ]
                    }
                }
            }
        },
        400: {"description": "Erro de validação ou sorteio inválido"},
        401: {"description": "Token inválido ou ausente"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def get_five_review_by_user(
    count: int,
    request: Request,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if not token_info or not getattr(token_info, "id", None):
            raise HTTPException(status_code=401, detail="Usuário não autenticado.")

        user_id = token_info.id

        # Verifica se o usuário existe
        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="Usuário não encontrado.")

        # Retorna as 5 avaliações mais recentes do usuário, de acordo com o count
        reviews = await ReviewSchemaBase.get_reviews_by_user(db, user_id, count)
        

        return {
            "reviews": reviews
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )
