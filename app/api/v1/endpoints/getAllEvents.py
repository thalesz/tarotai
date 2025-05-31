from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import asyncio

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.event import EventSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.schemas.mission_type import RecurrenceMode, MissionTypeSchemaBase
from app.schemas.transaction import TransactionSchemaBase, TransactionType
from app.services.calendar import Calendar

router = APIRouter()

@router.get(
    "/all",
    summary="Listar eventos ativos por usuário",
    description="Retorna todos os eventos ativos disponíveis para o tipo de usuário autenticado, junto com o status de premiação de cada evento.",
    response_description="Lista de eventos ativos retornada com sucesso.",
    responses={
        200: {
            "description": "Lista de eventos ativos retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {
                                "id": 1,
                                "name": "Campanha de Verão",
                                "description": "Complete missões para ganhar recompensas.",
                                "gifts": "Prêmio disponível para retirada"
                            },
                            {
                                "id": 2,
                                "name": "Promoção de Natal",
                                "description": "Participe de eventos e ganhe prêmios.",
                                "gifts": "Prêmio já retirado"
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
    }
)
async def get_all_active_events_by_user(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    """
    Retorna todos os eventos ativos de acordo com o tipo de usuário autenticado.
    Cada evento indica se o prêmio já foi retirado, está disponível ou ainda não está disponível.
    """
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="token information is missing")

        user_id = getattr(token_info, "id", None)
        if user_id is None:
            raise HTTPException(status_code=400, detail="User id not found in token")

        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="User does not exist.")

        id_active = await StatusSchemaBase.get_id_by_name(db, "active")
        id_completed = await StatusSchemaBase.get_id_by_name(db, "completed")
        id_pending = await StatusSchemaBase.get_id_by_name(db, "pending_confirmation")

        user_type = await UserSchemaBase.get_user_type_by_id(db, user_id)
        all_active_events = await EventSchemaBase.get_all_active_events_by_user_type_and_status(
            db, [user_type], [id_active]
        )

        events_data = []
        SAFE_MAX_DATE = datetime(9999, 12, 31, 23, 59, 59)
        now_utc = datetime.now(timezone.utc)

        for event in all_active_events or []:
            recurrence_mode = await EventSchemaBase.get_recurrence_mode_by_id(db, event.id)
            start_date = await EventSchemaBase.get_start_date_by_id(db, event.id)
            period_start = start_date
            period_end = now_utc.replace(tzinfo=None)

            if recurrence_mode == RecurrenceMode.EXPIRED_DATE.value:
                expired_date = await EventSchemaBase.get_expired_date_by_id(db, event.id)
                period_end = expired_date if expired_date is not None else SAFE_MAX_DATE

            elif recurrence_mode == RecurrenceMode.CALENDAR.value:
                calendar = Calendar()
                recurrence_type, auto_renew = await asyncio.gather(
                    EventSchemaBase.get_recurrence_type_by_id(db, event.id),
                    EventSchemaBase.get_auto_renew_by_id(db, event.id)
                )
                reset_time = await EventSchemaBase.get_reset_time_by_id(db, event.id)
                period_start, period_end = calendar.get_current_period(
                    recurrence_type, start_date, reset_time, auto_renew
                )

            missions = await EventSchemaBase.get_all_missions_by_event_id(db, event.id)
            has_valid_mission = False

            for mission_id in missions:
                user_missions = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                    session=db,
                    user_id=user_id,
                    mission_type_id=mission_id,
                    start_date=period_start,
                    end_date=period_end,
                    status_ids=[id_completed, id_pending]
                )
                if user_missions:
                    has_valid_mission = True
                    break

            if recurrence_mode == RecurrenceMode.USER_BASED.value and not has_valid_mission:
                continue

            reward_transaction_exists = await TransactionSchemaBase.check_reward_transaction_exists(
                session=db,
                user_id=user_id,
                event_id=event.id,
                status_id=id_completed,
                start_date=period_start,
                end_date=period_end,
                transaction_type=TransactionType.REWARD.value
            )

            all_missions_completed = True

            for mission_id in missions:
                recurrence_mode, recurrence_type, reset_time, auto_renew, start_date = await asyncio.gather(
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
                elif recurrence_mode == RecurrenceMode.EXPIRED_DATE.value:
                    expired_date = await MissionTypeSchemaBase.get_expired_date_by_id(db, mission_id)
                    period_end = expired_date if expired_date is not None else SAFE_MAX_DATE
                else:
                    period_end = datetime.now(timezone.utc)

                if period_start and period_start.tzinfo:
                    period_start = period_start.replace(tzinfo=None)
                if period_end and period_end.tzinfo:
                    period_end = period_end.replace(tzinfo=None)

                completed_missions = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                    session=db,
                    user_id=user_id,
                    mission_type_id=mission_id,
                    start_date=period_start,
                    end_date=period_end,
                    status_ids=[id_completed]
                )
                if not completed_missions:
                    all_missions_completed = False
                    break

            if reward_transaction_exists:
                gifts = "Prêmio já retirado"
            elif all_missions_completed:
                gifts = "Prêmio disponível para retirada"
            else:
                gifts = "Prêmio ainda não retirado"

            events_data.append({
                "id": event.id,
                "name": event.name,
                "description": getattr(event, "description", None),
                "gifts": gifts
            })

        return {"data": events_data}

    except Exception as e:
        print(f"Erro ao buscar os eventos: {e}")
        raise HTTPException(status_code=500, detail="Ocorreu um erro ao buscar os eventos.")
