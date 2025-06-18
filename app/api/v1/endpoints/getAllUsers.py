from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase
from app.schemas.planet import PlanetSchemaBase
from app.schemas.user import UserSchemaBase # Import PlanetsSchemaBase
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase
from app.schemas.user_type import UserTypeSchemaBase  # Import UserTypeSchemaBase

router = APIRouter()

@router.get(
    "/all",
    response_class=JSONResponse,
    summary="Retorna todos os usuarios cadastrados: nome, email, id, status, tipo de usuario",
    description="Busca todos os usuarios disponíveis no sistema. A resposta inclui o ID, nome, email, status e tipo de usuario.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de usuarios.",
            "content": {
                "application/json": {
                    "example": {
                        "users": [
                            {"id": 1, "name": "Usuario 1", "email": "usuario1@example.com", "status": "ativo", "tipo": "admin"},
                            {"id": 2, "name": "Usuario 2", "email": "usuario2@example.com", "status": "inativo", "tipo": "user"}
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
async def get_all_users(
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve all users.

    - **db**: Database session dependency.

    Returns a JSON response containing a list of users with their IDs, names, emails, statuses, and user types.
    """
    try:
        users = await UserSchemaBase.get_all_users(db=db)
        
        # {
        #         "id": user.id,
        #         "username": user.username,
        #         "email": user.email,
        #         "status": user.status,
        #         "user_type": user.user_type,
        #         "full_name": user.full_name,
        #     }
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        
        #pegar o nome do status
        for user in users:
            # Assuming user['status'] is an ID, we fetch the name using StatusSchemaBase
            status_name = await StatusSchemaBase.get_name_by_id(db, user['status'])
            user['status'] = status_name

            # pegar o nome do tipo de usuario
            user_type_name = await UserTypeSchemaBase.get_name_by_id(db, user['user_type'])
            user['user_type'] = user_type_name

        print("Users retrieved:", users)  # Debugging line to check retrieved users
        # users is already a list of dicts, so just return it
        return {"users": users}
    except HTTPException as e:
        return {"error": e.detail}
