from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, conint
from typing import Dict, Any

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.draw import DrawSchemaBase
from app.schemas.review import ReviewSchemaBase
from app.services.confirmMissionService import ConfirmMissionService    
from app.basic.mission_type import mission_types
from app.schemas.mission_type import MissionTypeSchemaBase

router = APIRouter()

# Pydantic model para validar o body da requisição
class ReviewCreateRequest(BaseModel):
    draw: int = Field(..., description="ID do sorteio", example=123)
    rating: int = Field(..., ge=1, le=5, description="Nota de 1 a 5", example=5)
    comment: str = Field("", description="Comentário do usuário", example="Muito bom!")

@router.post(
    "/new",
    summary="Cria uma nova avaliação para uma postagem específica",
    description="""
Cria uma nova avaliação para uma postagem específica, permitindo que os usuários forneçam feedback sobre o conteúdo.

- O usuário deve estar autenticado.
- A avaliação deve incluir uma nota e um comentário.
""",
    response_description="Detalhes da avaliação criada",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {
            "description": "Avaliação criada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Avaliação criada com sucesso.",
                        "review": {
                            "id": 1,
                            "user": 1,
                            "draw": 1,
                            "rating": 5,
                            "comment": "Ótima postagem!",
                            "created_at": "2023-10-10T10:00:00Z"
                        }
                    }
                }
            }
        },
        400: {"description": "Erro de validação ou sorteio inválido"},
        401: {"description": "Token inválido ou ausente"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def put_new_review(
    payload: ReviewCreateRequest,
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

        # Verifica se o sorteio pertence ao usuário
        if not await DrawSchemaBase.verify_draw_belongs_to_user(db, payload.draw, user_id):
            raise HTTPException(status_code=400, detail="Sorteio/draw não encontrado ou não pertence ao usuário.")
        
        # tem que ver se o sorteio já foi avaliado
        existing_review = await ReviewSchemaBase.get_review_by_user_and_draw(db, user_id, payload.draw)

        if existing_review:
            raise HTTPException(status_code=400, detail="Sorteio já avaliado.")

        # Cria a avaliação
        review = await ReviewSchemaBase.create_review(
            session=db,
            user_id=user_id,
            draw_id=payload.draw,
            rating=payload.rating,
            comment=payload.comment
        )
        
        
        mission_type_id = await MissionTypeSchemaBase.get_id_by_name(
            db=db,
            name="Avaliar uma tiragem gerada pela IA"
        )
        
        confirm_mission = ConfirmMissionService()
        await confirm_mission.confirm_mission(
            db=db,
            mission_type_id=mission_type_id,  # "Abrir um biscoito da sorte" é o segundo item,
            user_id=user_id,
        )

        return {
            "message": "Avaliação criada com sucesso.",
            "review": review
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno do servidor: {str(e)}"
        )
