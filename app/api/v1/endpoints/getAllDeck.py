from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.deck import DeckSchemaBase
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.user_type import UserTypeSchemaBase

router = APIRouter()

@router.get(
    "/all",
    summary="Recuperar todos os baralhos",
    description="Busca todos os baralhos com seus respectivos IDs, nomes e disponibilidade para o usuário.",
    response_description="Uma lista de baralhos com seus IDs, nomes e disponibilidade.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de baralhos.",
            "content": {
                "application/json": {
                    "example": {
                        "decks": [
                            {"id": 1, "name": "Baralho Cigano", "available": True},
                            {"id": 2, "name": "Tarô Rider-Waite", "available": False}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao buscar os baralhos."}
                }
            },
        },
    },
)
async def get_all_decks(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    try:
        decks = await DeckSchemaBase.get_all_decks(session=db)
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="token information is missing")

        user_id = getattr(token_info, "id", None)
        if user_id is None:
            raise HTTPException(status_code=400, detail="User id not found in token")
        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="User does not exist.")

        type_user = await UserSchemaBase.get_user_type_by_id(db, user_id)
        accessible_card_types = await UserTypeSchemaBase.get_accessible_card_types_by_user_type(
            db, type_user
        )

        decks_response = []
        for deck in decks:
            available = deck.id in accessible_card_types
            decks_response.append({
                "id": deck.id,
                "name": deck.name,
                "available": available
            })

        return {"decks": decks_response}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
