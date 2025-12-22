from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete as sqldelete

from app.core.deps import get_session
from app.schemas.user import UserSchemaBase

from app.models.token_blacklist import TokenBlacklistModel
from app.models.transaction import TransactionModel
from app.models.subscription import SubscriptionModel
from app.models.wallet import WalletModel
from app.models.personalSign import PersonalSign
from app.models.review import ReviewModel
from app.models.notification import Notification
from app.models.mission import MissionModel
from app.models.daily_lucky import DailyLuckyModel
from app.models.daily_zodiac import DailyZodiacModel
from app.models.daily_path import DailyPathModel
from app.models.draw import DrawModel
from app.models.user import UserModel

router = APIRouter()


@router.delete(
    "/{user_id}",
    summary="Deleta usuário e dados dependentes (ADM apenas)",
    description=(
        "Deleta um usuário identificado por `user_id` e todas as entidades dependentes "
        "(transações, assinaturas, carteira, notificações, etc.). Requer permissões de "
        "administrador. Retorna uma mensagem de sucesso ou um erro apropriado."
    ),
    status_code=200,
    tags=["users"],
    responses={
        200: {"description": "Usuário e dependências removidos com sucesso."},
        404: {"description": "Usuário não encontrado."},
        500: {"description": "Erro interno do servidor."},
    },
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_session),
):
    try:
        # verifica se usuário existe
        exists = await UserSchemaBase.user_exists(db, user_id)
        if not exists:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # ordem: remover dependências que possuem FK para users
        await db.execute(sqldelete(TokenBlacklistModel).where(TokenBlacklistModel.user_id == user_id))
        await db.execute(sqldelete(TransactionModel).where(TransactionModel.user_id == user_id))
        await db.execute(sqldelete(SubscriptionModel).where(SubscriptionModel.user_id == user_id))
        await db.execute(sqldelete(WalletModel).where(WalletModel.user_id == user_id))
        await db.execute(sqldelete(PersonalSign).where(PersonalSign.user == user_id))
        await db.execute(sqldelete(ReviewModel).where(ReviewModel.user == user_id))
        await db.execute(sqldelete(Notification).where(Notification.user == user_id))
        await db.execute(sqldelete(MissionModel).where(MissionModel.user == user_id))
        await db.execute(sqldelete(DailyLuckyModel).where(DailyLuckyModel.user_id == user_id))
        await db.execute(sqldelete(DailyZodiacModel).where(DailyZodiacModel.user == user_id))
        await db.execute(sqldelete(DailyPathModel).where(DailyPathModel.user == user_id))
        await db.execute(sqldelete(DrawModel).where(DrawModel.user_id == user_id))

        # por fim, remove o usuário
        await db.execute(sqldelete(UserModel).where(UserModel.id == user_id))

        await db.commit()

        return {"message": "Usuário e dependências removidos com sucesso."}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")
