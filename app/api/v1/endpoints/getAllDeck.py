from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.deck import DeckSchemaBase

router = APIRouter()

@router.get(
    "/all",
    summary="Retrieve all decks",
    description="Fetches all decks with their respective IDs and names.",
    response_description="A list of decks with their IDs and names.",
    responses={
        200: {
            "description": "Successful response with a list of decks.",
            "content": {
                "application/json": {
                    "example": {
                        "decks": [
                            {"id": 1, "name": "Deck 1"},
                            {"id": 2, "name": "Deck 2"}
                        ]
                    }
                }
            },
        },
        500: {
            "description": "Internal server error.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while fetching decks."}
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
