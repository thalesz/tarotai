from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.event import EventSchemaBase
from app.schemas.mission import MissionSchemaBase

router = APIRouter()

@router.put(
    "/completed/{mission_id}",
    summary="Atualizar status da missão para concluída",
    description="Atualiza o status de uma missão específica para concluída, com base no ID da missão fornecido.",
    response_description="Status da missão atualizado com sucesso.",
    responses={
        200: {
            "description": "Status da missão atualizado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "detail": "Status da missão atualizado para confirmado com sucesso."
                            }
                        ]
                    }
                }
            },
        },
        400: {
            "description": "Usuário inválido ou não encontrado.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not exist."}
                }
            },
        },
        401: {
            "description": "Token de autenticação ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "token information is missing"}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao buscar os eventos."}
                }
            },
        },
    },
)
async def confirm_mission(
    request: Request,
    mission_id: int,
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

        id_completed = await StatusSchemaBase.get_id_by_name(db, "completed")
        id_pending = await StatusSchemaBase.get_id_by_name(db, "pending_confirmation")

        # Verifica se a missão existe e pertence ao usuário
        missionExists = await MissionSchemaBase.mission_exists(db, mission_id, user_id)
        if not missionExists:
            raise HTTPException(status_code=400, detail="Mission does not exist or user is not the owner.")

        mission_status = await MissionSchemaBase.get_status_by_mission_id(db, mission_id)
        if mission_status != id_pending:
            raise HTTPException(status_code=400, detail="Missão não está pendente de confirmação.")	

        # Atualiza o status da missão para "confirmado"
        await MissionSchemaBase.update_mission_status(db, mission_id, id_completed)

        print("Status da missão atualizado para confirmado com sucesso.")
        return {
            "data": [
                {
                    "detail": "Status da missão atualizado para confirmado com sucesso."
                }
            ]
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao buscar os eventos: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao buscar os eventos.")
