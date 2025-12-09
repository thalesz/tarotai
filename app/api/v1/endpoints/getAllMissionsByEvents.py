from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.services.token import TokenInfoSchema  # Import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from datetime import datetime, timezone
from app.schemas.spread_type import SpreadTypeSchemaBase
from app.schemas.draw import DrawSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase, RecurrenceMode
from app.schemas.event import EventSchemaBase
from app.services.calendar import Calendar
from app.services.user_based import UserBased
import asyncio

router = APIRouter()

@router.get(
    "/all/{event_id}",
    summary="Obter todas as missões disponíveis por evento",
    description="""
Retorna uma lista de todas as missões disponíveis para um determinado evento.

- **event_id**: ID do evento para o qual as missões serão buscadas.
- Retorna informações detalhadas de cada missão, incluindo:
    - id: ID da missão
    - name: Nome da missão
    - description: Descrição da missão
    - status: Status atual da missão (pendente ou completada)
    - used_at: Data/hora em que a missão foi utilizada (se aplicável)
    - start: Data/hora de início do período da missão
    - end: Data/hora de término do período da missão
""",
    response_description="Uma lista contendo os IDs, nomes, status e descrições dos tipos de missões.",
    responses={
        200: {
            "description": "Lista de missões disponíveis retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Missão Diária",
                                "description": "Complete uma tiragem diária.",
                                "status": "pendente",
                                "used_at": "2024-06-10T12:00:00Z",
                                "start": "2024-06-10T00:00:00Z",
                                "end": "2024-06-10T23:59:59Z"
                            }
                        ]
                    }
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
        400: {
            "description": "Erro de validação ou usuário não encontrado.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not exist."}
                }
            },
        },
        403: {
            "description": "Usuário não tem permissão para acessar este evento.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not have permission to access this event."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao buscar as tiragens disponíveis."}
                }
            },
        },
    },
)
async def get_all_mission_by_event_id(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_session)
):
    try:
        print(f"Fetching missions for event_id: {event_id}")
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="token information is missing")

        user_id = getattr(token_info, "id", None)
        if user_id is None:
            raise HTTPException(status_code=400, detail="User id not found in token")

        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="User does not exist.")

        user_type = await UserSchemaBase.get_user_type_by_id(db, user_id)
        
        
        print(f"User ID: {user_id}, User Type: {user_type}")

        if not await EventSchemaBase.user_type_has_permission_for_event(db, user_type, event_id):
            raise HTTPException(status_code=403, detail="User does not have permission to access this event.")
        print(f"User {user_id} has permission for event {event_id}")

        missions = await EventSchemaBase.get_all_missions_by_event_id(db, event_id)
        print("missions___:", missions)

        id_pending, id_completed = await asyncio.gather(
            StatusSchemaBase.get_id_by_name(db, "pending_confirmation"),
            StatusSchemaBase.get_id_by_name(db, "completed")
        )

        async def get_mission_detail(mission_id: int):
            (
                name, description, recurrence_mode, recurrence_type, 
                reset_time, auto_renew, start_date
            ) = await asyncio.gather(
                MissionTypeSchemaBase.get_name_by_id(db, mission_id),
                MissionTypeSchemaBase.get_description_by_id(db, mission_id),
                MissionTypeSchemaBase.get_recurrence_mode_by_id(db, mission_id),
                MissionTypeSchemaBase.get_recurrence_type_by_id(db, mission_id),
                MissionTypeSchemaBase.get_reset_time_by_id(db, mission_id),
                MissionTypeSchemaBase.get_auto_renew_by_id(db, mission_id),
                MissionTypeSchemaBase.get_start_date_by_id(db, mission_id)
            )

            if recurrence_mode == RecurrenceMode.CALENDAR.value:
                calendar = Calendar()
                period_start, period_end = calendar.get_current_period(
                    recurrence_type, start_date, reset_time, auto_renew
                )
            else:
                period_start = start_date
                if recurrence_mode == RecurrenceMode.EXPIRED_DATE.value:
                    period_end = await MissionTypeSchemaBase.get_expired_date_by_id(db, mission_id)
                else:
                    period_end = datetime.now(timezone.utc)

            id_missions = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                session=db,
                user_id=user_id,
                mission_type_id=mission_id,
                start_date=period_start,
                end_date=period_end,
                status_ids=[id_pending, id_completed]
            )

            details = []
            for id in id_missions:
                if not id:
                    continue

                status_id, used_at = await asyncio.gather(
                    MissionSchemaBase.get_status_by_mission_id(db, id),
                    MissionSchemaBase.get_used_at_by_id(db, id)
                )
                status_name = await StatusSchemaBase.get_name_by_id(db, status_id)

                if recurrence_mode == RecurrenceMode.USER_BASED.value:
                    created_at = await MissionSchemaBase.get_created_at_by_id(db, id)
                    relative_days = await MissionTypeSchemaBase.get_relative_days_by_id(db, mission_id)
                    user_based = UserBased()
                    period_start = created_at
                    period_end = user_based.calculate_expired_date(start_date, relative_days, reset_time)

                status_map = {
                    "pending_confirmation": "pendente",
                    "completed": "completada"
                }

                details.append({
                    "id": id,
                    "name": name,
                    "description": description,
                    "status": status_map.get(status_name, status_name),
                    "used_at": used_at.isoformat() if used_at else None,
                    "start": period_start.isoformat() if period_start else None,
                    "end": period_end.isoformat() if period_end else None
                })
            return details

        # Executa em paralelo a busca de detalhes das missões
        mission_tasks = [get_mission_detail(m) for m in missions]
        results = await asyncio.gather(*mission_tasks)
        mission_details = [item for sublist in results for item in sublist]  # flatten list

        return {"data": mission_details}

    except HTTPException as e:
        print(f"HTTPException: {e.detail}")
        raise e
    except Exception as e:
        print(f"Exception: {e}")
        raise HTTPException(status_code=500, detail=str(e))
