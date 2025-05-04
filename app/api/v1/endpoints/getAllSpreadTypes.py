from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase

router = APIRouter()

@router.get(
    "/",
    response_class=JSONResponse,
    summary="Retrieve all spread types",
    description="Fetches all spread types available in the system. The response includes the spread type ID and name.",
    responses={
        200: {
            "description": "Successful response with a list of spread types.",
            "content": {
                "application/json": {
                    "example": {
                        "spread_types": [
                            {"id": 1, "name": "Spread Type 1"},
                            {"id": 2, "name": "Spread Type 2"}
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Bad Request. An error occurred while fetching spread types.",
            "content": {
                "application/json": {
                    "example": {"error": "An error occurred"}
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
