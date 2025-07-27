from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.deck import DeckSchemaBase
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.user_type import UserTypeSchemaBase
from app.schemas.card_styles import CardStylesSchema  # Add this import

router = APIRouter()

@router.get(
    "/all",
    summary="Recuperar todos os estilos de cartas",
    description="Busca todos os estilos de cartas com seus respectivos IDs, nomes e disponibilidade para o usuário.",
    response_description="Uma lista de estilos de cartas com seus IDs, nomes e disponibilidade.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de estilos de cartas.",
            "content": {
                "application/json": {
                    "example": {
                        "decks": [
                            {"id": 1, "name": "Traditional", "description": "Um baralho tradicional", "available": True},
                            {"id": 2, "name": "Gatinho", "description": "Um baralho de gatinhos", "available": False}
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
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="token information is missing")

        user_id = getattr(token_info, "id", None)
        if user_id is None:
            raise HTTPException(status_code=400, detail="User id not found in token")
        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="User does not exist.")

        type_user = await UserSchemaBase.get_user_type_by_id(db, user_id)
        # accessible_card_types = await UserTypeSchemaBase.get_accessible_card_types_by_user_type(
        #     db, type_user
        # )
        
        accessible_card_styles = await UserTypeSchemaBase.get_accessible_card_styles_by_user_type(
            db, type_user
        )
        card_styles = await CardStylesSchema.get_all_card_styles(session=db)

        card_styles_response = []
        for style in card_styles:
            available = style.id in accessible_card_styles
            card_styles_response.append({
                "id": style.id,
                "name": style.name,
                "description": style.description,
                "available": available
            })

        # Ordena para mostrar os disponíveis primeiro
        card_styles_response.sort(key=lambda x: not x["available"])

        return {"card_styles": card_styles_response}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
