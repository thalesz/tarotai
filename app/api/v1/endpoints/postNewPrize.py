from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import asyncio
from typing import List, Dict, Any

from app.core.deps import get_session
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.status import StatusSchemaBase
from app.schemas.event import EventSchemaBase
from app.schemas.mission_type import MissionTypeSchemaBase, RecurrenceMode
from app.schemas.spread_type import SpreadTypeSchemaBase
from app.schemas.mission import MissionSchemaBase
from app.services.calendar import Calendar
from app.schemas.draw import DrawCreate
from app.schemas.transaction import TransactionSchemaBase
from app.models.transaction import TransactionType

router = APIRouter()

@router.post(
    "/prizes/{event_id}",
    summary="Requisita os prêmios de um evento específico",
    description="""
Disponibiliza os prêmios associados a um evento específico, **filtrando por status ativo**, diretamente na conta do **usuário autenticado**.

- O evento deve estar ativo.
- O usuário deve ter completado todas as missões associadas ao evento.
- A recompensa só pode ser requisitada uma única vez por período.
""",
    response_description="Lista de prêmios concedidos ao usuário",
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Recompensas entregues com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Recompensas recebidas com sucesso.",
                        "rewards": ["Cruz Celta", "Estrela do Norte"]
                    }
                }
            }
        },
        400: {"description": "Erro de validação ou recompensa já recebida"},
        401: {"description": "Token inválido ou ausente"},
        500: {"description": "Erro interno do servidor"}
    }
)
async def put_new_prize(
    request: Request,
    event_id: int,
    db: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="Token de autenticação ausente.")

        user_id = getattr(token_info, "id", None)
        if user_id is None:
            raise HTTPException(status_code=400, detail="ID do usuário ausente no token.")

        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="Usuário não encontrado.")

        id_active, id_completed, user_type = await asyncio.gather(
            StatusSchemaBase.get_id_by_name(db, "active"),
            StatusSchemaBase.get_id_by_name(db, "completed"),
            UserSchemaBase.get_user_type_by_id(db, user_id)
        )

        missions = await EventSchemaBase.get_all_missions_by_event_id(db, event_id)

        all_completed = True
        for mission in missions:
            if mission is None:
                continue

            (
                recurrence_mode,
                recurrence_type,
                reset_time,
                auto_renew,
                start_date
            ) = await asyncio.gather(
                MissionTypeSchemaBase.get_recurrence_mode_by_id(db, mission),
                MissionTypeSchemaBase.get_recurrence_type_by_id(db, mission),
                MissionTypeSchemaBase.get_reset_time_by_id(db, mission),
                MissionTypeSchemaBase.get_auto_renew_by_id(db, mission),
                MissionTypeSchemaBase.get_start_date_by_id(db, mission)
            )

            if recurrence_mode == RecurrenceMode.CALENDAR.value:
                calendar = Calendar()
                period_start, period_end = calendar.get_current_period(
                    recurrence_type, start_date, reset_time, auto_renew
                )
            else:
                period_start = start_date
                period_end = (
                    await MissionTypeSchemaBase.get_expired_date_by_id(db, mission)
                    if recurrence_mode == RecurrenceMode.EXPIRED_DATE.value
                    else datetime.now(timezone.utc)
                )

            completed_missions = await MissionSchemaBase.get_list_id_by_user_and_types_and_period_and_status(
                session=db,
                user_id=user_id,
                mission_type_id=mission,
                start_date=period_start,
                end_date=period_end,
                status_ids=[id_completed]
            )

            if not completed_missions:
                raise HTTPException(
                    status_code=400,
                    detail=f"Complete todas as missões do evento {event_id} antes de requisitar os prêmios."
                )

        if recurrence_mode != RecurrenceMode.CALENDAR.value:
            period_start = await EventSchemaBase.get_start_date_by_id(db, event_id)
            period_end = await EventSchemaBase.get_expired_date_by_id(db, event_id)

        reward_transaction_exists = await TransactionSchemaBase.check_reward_transaction_exists(
            session=db,
            user_id=user_id,
            event_id=event_id,
            status_id=id_completed,
            start_date=period_start,
            end_date=period_end,
            transaction_type=TransactionType.REWARD.value
        )

        if reward_transaction_exists:
            raise HTTPException(
                status_code=400,
                detail="Recompensa já recebida anteriormente para este evento."
            )

        given_draws = []
        draw_ids = []

        if all_completed and not reward_transaction_exists:
            gifts = await EventSchemaBase.get_all_gifts_by_event_id(db, event_id)

            for gift in gifts:
                if isinstance(gift, list):
                    for spread_type_id in gift:
                        new_draw = await DrawCreate.create_draw(db, user_id=user_id, spread_type_id=spread_type_id)
                        draw_ids.append(new_draw.id)
                        draw_name = await SpreadTypeSchemaBase.get_spread_type_name_by_id(db, spread_type_id)
                        given_draws.append(draw_name)
                else:
                    new_draw = await DrawCreate.create_draw(db, user_id=user_id, spread_type_id=gift)
                    draw_ids.append(new_draw.id)
                    draw_name = await SpreadTypeSchemaBase.get_spread_type_name_by_id(db, gift)
                    given_draws.append(draw_name)

            if draw_ids:
                await TransactionSchemaBase.create_transaction(
                    session=db,
                    user_id=user_id,
                    draws=draw_ids,
                    transaction_type=TransactionType.REWARD.value,
                    status_id=id_completed,
                    event_id=event_id
                )

        return {
            "message": "Recompensas recebidas com sucesso.",
            "rewards": given_draws
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro ao requisitar prêmios: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar as recompensas.")
