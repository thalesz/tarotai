from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase
from app.schemas.planet import PlanetSchemaBase # Import PlanetsSchemaBase

router = APIRouter()

@router.get(
    "/all",
    response_class=JSONResponse,
    summary="Recuperar todos os planetas",
    description="Busca todos os planetas disponíveis no sistema. A resposta inclui o ID e o nome do planeta.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de planetas.",
            "content": {
                "application/json": {
                    "example": {
                        "planets": [
                            {"id": 1, "name": "Planeta 1"},
                            {"id": 2, "name": "Planeta 2"}
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida. Ocorreu um erro ao buscar os planetas.",
            "content": {
                "application/json": {
                    "example": {"error": "Ocorreu um erro"}
                }
            },
        },
    },
)
async def get_all_planets(
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve all planets.

    - **db**: Database session dependency.

    Returns a JSON response containing a list of planets with their IDs and names.
    """
    try:
        planets = await PlanetSchemaBase.get_all_planets(session=db)
        print("Planets retrieved:", planets)  # Debugging line to check retrieved planets
        #convert to a list of dictionaries
        return {"planets": planets}
    except HTTPException as e:
        return {"error": e.detail}
