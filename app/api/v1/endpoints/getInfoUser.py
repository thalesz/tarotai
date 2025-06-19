from fastapi import APIRouter, Depends, HTTPException, Response, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase
from app.schemas.planet import PlanetSchemaBase
from app.schemas.user import UserSchemaBase # Import PlanetsSchemaBase
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase
from app.schemas.user_type import UserTypeSchemaBase  # Import UserTypeSchemaBase
from app.services.token import TokenInfoSchema

router = APIRouter()

@router.get(
    "/self",
    response_class=JSONResponse,
    summary="Retorna informaações de um usuario especifico utilizando o ID do usuario contido no token",
    description="Busca todos os usuarios disponíveis no sistema. A resposta inclui o ID, nome, email, status e tipo de usuario.",
    responses={
        200: {
            "description": "Resposta bem-sucedida com uma lista de usuarios.",
            "content": {
                "application/json": {
                    "example": {
                        "user": {
                            "id": 1,
                            "name": "Usuario 1",
                            "email": "usuario1@example.com",
                            "status": "ativo",
                            "tipo": "admin"
                        }
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
async def get_info_user(
    request: Request,

    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve all users.

    - **db**: Database session dependency.

    Returns a JSON response containing a list of users with their IDs, names, emails, statuses, and user types.
    """
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if not token_info or not getattr(token_info, "id", None):
            raise HTTPException(status_code=401, detail="Usuário não autenticado.")

        user_id = token_info.id

        # Verifica se o usuário existe
        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="Usuário não encontrado.")

        user = await UserSchemaBase.get_user_by_id(db=db, user_id=user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")

        # pegar o nome do status
        status_name = await StatusSchemaBase.get_name_by_id(db, user.status)
        user_type_name = await UserTypeSchemaBase.get_name_by_id(db, user.user_type)

        # Montar resposta apenas com os campos solicitados
        user_response = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "user_type": user_type_name,
            "status": status_name,
            "birth_date": user.birth_date,
            "birth_time": user.birth_time,
            "birth_place": user.birth_place,
        }

        return {"user": user_response}
    except HTTPException as e:
        return {"error": e.detail}

        return {"user": user}
    except HTTPException as e:
        return {"error": e.detail}
