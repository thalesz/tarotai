from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase

router = APIRouter()

@router.get(
    "/all",
    response_class=JSONResponse,
    summary="Recuperar todos os tipos de tiragens",
    description="Busca todos os tipos de spreads disponíveis no sistema. A resposta inclui o ID e o nome do tipo de spread.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de tipos de spreads.",
            "content": {
                "application/json": {
                    "example": {
                        "spread_types": [
                            {"id": 1, "name": "Tipo de Spread 1"},
                            {"id": 2, "name": "Tipo de Spread 2"}
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida. Ocorreu um erro ao buscar os tipos de spreads.",
            "content": {
                "application/json": {
                    "example": {"error": "Ocorreu um erro"}
                }
            },
        },
    },
)
async def get_all_spread_types(
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve all spread types.

    - **db**: Database session dependency.

    Returns a JSON response containing a list of spread types with their IDs and names.
    """
    try:
        spread_types = await SpreadTypeSchemaBase.get_all_spread_types(session=db)
        return JSONResponse(content={"spread_types": [{"id": spread_type.id, "name": spread_type.name, "description":spread_type.description, "card_count": spread_type.card_count} for spread_type in spread_types]})
    except HTTPException as e:
        return {"error": e.detail}
