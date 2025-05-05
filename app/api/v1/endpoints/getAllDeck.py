from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.deck import DeckSchemaBase

router = APIRouter()

@router.get(
    "/all",
    summary="Recuperar todos os baralhos",
    description="Busca todos os baralhos com seus respectivos IDs e nomes.",
    response_description="Uma lista de baralhos com seus IDs e nomes.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de baralhos.",
            "content": {
                "application/json": {
                    "example": {
                        "decks": [
                            {"id": 1, "name": "Baralho 1"},
                            {"id": 2, "name": "Baralho 2"}
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
    db: AsyncSession = Depends(get_session)
):
    try:
        decks = await DeckSchemaBase.get_all_decks(session=db)
        return {"decks": [{"id": deck.id, "name": deck.name} for deck in decks]}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
