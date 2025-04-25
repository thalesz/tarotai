from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.deck import DeckSchemaBase
from app.schemas.card import CardSchemaBase  # Import CardSchemaBase

router = APIRouter()

@router.get(
    "/{deck_id}",
    response_class=JSONResponse,
    summary="Retrieve all cards by deck ID",
    description="Fetches all cards associated with a specific deck ID. The response includes the card ID and name.",
    responses={
        200: {
            "description": "Successful response with a list of cards.",
            "content": {
                "application/json": {
                    "example": {
                        "cards": [
                            {"id": 1, "name": "Card 1"},
                            {"id": 2, "name": "Card 2"}
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Bad Request. Deck ID is missing or invalid.",
            "content": {
                "application/json": {
                    "example": {"error": "Deck ID is required"}
                }
            },
        },
    },
)
async def get_all_cards_by_deck_id(
    db: AsyncSession = Depends(get_session),
    deck_id: int = None,
):
    """
    Retrieve all cards by deck ID.

    - **deck_id**: The ID of the deck to fetch cards for.
    - **db**: Database session dependency.

    Returns a JSON response containing a list of cards with their IDs and names.
    """
    try:
        if not deck_id:
            raise HTTPException(status_code=400, detail="Deck ID is required")
        
        cards = await CardSchemaBase.get_card_by_deck_id(session=db, deck_id=deck_id)
        return JSONResponse(content={"cards": [{"id": card.id, "name": card.name} for card in cards]})
    except HTTPException as e:
        return {"error": e.detail}
