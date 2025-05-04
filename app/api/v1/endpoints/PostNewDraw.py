from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_session
from app.schemas.draw import DrawCreate
from app.schemas.user import UserSchemaBase  # Import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchema  # Import SpreadTypeSchema
from app.services.token import TokenInfoSchema # Import TokenInfoSchema

router = APIRouter()

@router.post(
    "/new",
    summary="Create a new draw",
    description="Creates a new tarot draw with the provided details.",
    response_description="Details of the created draw.",
    responses={
        201: {
            "description": "Successful creation of a new draw.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "cards": ["The Fool", "The Magician", "The High Priestess"],
                        "created_at": "2023-10-01T12:00:00Z"
                    }
                }
            },
        },
        400: {
            "description": "Bad request due to invalid input.",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid input data."}
                }
            },
        },
        500: {
            "description": "Internal server error.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while creating the draw."}
                }
            },
        },
    },
)
async def post_new_draw(
    request: Request,
    draw_data: DrawCreate,
    db: AsyncSession = Depends(get_session)
):
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(
                status_code=401, detail="token information is missing"
            )
        
        try:
            user_id = token_info.id
        except AttributeError:
            raise HTTPException(status_code=400, detail="User id not found in token")
        
        # verifica se o usuario existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
        # verifica se o tipo de spread existe
        spreadexists = await SpreadTypeSchema.spread_type_exists(db, draw_data.spread_type_id)
        
        # spread_type_exists(db, draw_data.spread_type_id)
        if not spreadexists:
            raise HTTPException(
                status_code=400, 
                detail="Spread type does not exist."
            )
        
        
        new_draw = await DrawCreate.create_draw(
            db, 
            user_id=user_id, 
            spread_type_id=draw_data.spread_type_id
        )
        return {
            "message": "Draw created successfully.",
            "draw": {
                "id": new_draw.id,
                "user_id": user_id,
                "spread_type_id": new_draw.spread_type_id,
                "status": new_draw.status_id,
                "created_at": new_draw.created_at
            }
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while creating the draw: {str(e)}"
        )