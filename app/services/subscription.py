from app.schemas.status import StatusSchemaBase  # Adjust the import path as needed
from app.schemas.user_type import UserTypeSchemaBase  # Adjust the import path as needed
from app.schemas.user import UserSchemaBase  # Adjust the import path as needed
from app.schemas.subscription import SubscriptionSchemaBase  # Adjust the import path as needed
from datetime import datetime
from app.core.postgresdatabase import Session
from sqlalchemy.ext.asyncio import AsyncSession
from collections import Counter
from app.schemas.draw import DrawCreate  # Adjust the import path as needed
from app.schemas.transaction import TransactionSchemaBase  # Adjust the import path as needed


class Subscription:
    
    # Esta função será chamada uma vez por dia
    async def create_daily_gift_for_all_users(self):
        """
        Create a daily gift for all active users.
        """
        async with Session() as session:
            db: AsyncSession = session

            print("Creating daily gifts for all users...")

            id_active = await StatusSchemaBase.get_id_by_name(db=session, name="active")
            id_standard = await UserTypeSchemaBase.get_id_by_name(session=session, name="STANDARD")
            id_premium = await UserTypeSchemaBase.get_id_by_name(session=session, name="PREMIUM")
            id_admin = await UserTypeSchemaBase.get_id_by_name(session=session, name="ADM")

            active_users = await UserSchemaBase.get_all_id_by_status(
                db=db, status_id=id_active, user_type=[id_standard, id_premium, id_admin]
            )

            if not active_users:
                print("No active users found.")
                return

            print(f"Active users: {active_users}")
            for user in active_users:
                await self.create_daily_gift_for_user(db=db, user_id=user)

    @staticmethod
    # Esta função pode ser reutilizada em outras partes do sistema
    async def create_daily_gift_for_user(db: AsyncSession, user_id: int):
        """
        Create a daily gift for a single user.
        """
        print(f"Creating daily gift for user {user_id}.")

        id_pending_confirmation = await StatusSchemaBase.get_id_by_name(
            db=db, name="pending_confirmation"
        )

        user_type = await UserSchemaBase.get_user_type_by_id(db=db, id=user_id)
        gifts = await UserTypeSchemaBase.get_daily_gift_by_user_type(
            session=db, user_type_id=user_type
        )

        last_transaction_id = await TransactionSchemaBase.get_last_transaction_by_user_id(
            session=db, user_id=user_id, transaction_type="DAILY_LOGIN"
        )

        last_transaction_draws = await TransactionSchemaBase.get_draws_by_transaction_id(
            session=db, transaction_id=last_transaction_id
        )

        pending_gift_counts = {}
        new_draws = []

        if last_transaction_draws:
            for draw in last_transaction_draws:
                draw_status = await DrawCreate.get_draw_status_by_id(session=db, draw_id=draw)
                spread_type_id = await DrawCreate.get_spread_type_id_by_draw_id(session=db, draw_id=draw)
                if draw_status == id_pending_confirmation:
                    pending_gift_counts[spread_type_id] = pending_gift_counts.get(spread_type_id, 0) + 1
                    await DrawCreate.update_created_at(session=db, draw_id=draw)
                    new_draws.append(draw)
                else:
                    print(f"Draw {draw} for user {user_id} is not pending confirmation, skipping.")

        gifts_counter = Counter(gifts)
        for gift, required_count in gifts_counter.items():
            already_pending = pending_gift_counts.get(gift, 0)
            to_create = required_count - already_pending
            for _ in range(to_create):
                # print(f"Adding gift {gift} for user {user_id}.")
                created_draw = await DrawCreate.create_draw(
                    db,
                    user_id=user_id,
                    spread_type_id=gift
                )
                new_draws.append(created_draw.id)
                # print(f"Gift {gift} added as draw for user {user_id}. Draw ID: {created_draw.id}")

        if new_draws:
            await TransactionSchemaBase.create_transaction(
                session=db,
                user_id=user_id,
                transaction_type="DAILY_LOGIN",
                draws=new_draws
            )
            print(f"Created DAILY_LOGIN transaction for user {user_id} with draws {new_draws}")

        await TransactionSchemaBase.delete_old_daily_transactions(
            session=db,
            user_id=user_id
        )

    async def verify_subscription(self):
        """
        Verify the subscription status of a user.
        """
        async with Session() as session:
            # pega todos os usuarios ativos e premium
            db: AsyncSession = session
            id_active = await StatusSchemaBase.get_id_by_name(db=session, name="active")
            id_premium = await UserTypeSchemaBase.get_id_by_name(session=session, name="PREMIUM")
            id_standard = await UserTypeSchemaBase.get_id_by_name(session=session, name="STANDARD")

            # print("id active:", id_active)
            # print("id premium:", id_premium)
            active_premium_users = await UserSchemaBase.get_all_id_by_status(
                db=db, status_id=id_active, user_type=id_premium
            )
            if not active_premium_users:
                print("No active premium users found.")
                return            
            #pegamos todos os usuarios ativos e premium
            print(f"Active premium users: {active_premium_users}")
            
            #agora temos que pegar a assinatura e ver se ta expirada ou não
            for user in active_premium_users:
                # tem que pegar a assinatura ativa e sua data de expiração
                subscription_id = await SubscriptionSchemaBase.get_id_by_user_id(session=db, user_id=user, status_id=id_active)

                subscription_expiration = await SubscriptionSchemaBase.get_expiration_by_id(session=db, subscription_id=subscription_id)

                # print(f"User {user} has subscription ID {subscription_id} with expiration date {subscription_expiration}. now {datetime.now()}")
                if subscription_expiration is None:
                    continue

                if subscription_expiration < datetime.now():
                    # Se a assinatura estiver expirada, atualizamos o status do usuário
                    await UserSchemaBase.update_user_type(
                        db=db,
                        user_id=user,
                        new_user_type=id_standard
                    )
                    await SubscriptionSchemaBase.update_status(
                        session=db,
                        subscription_id=subscription_id,
                        new_status=id_standard
                    )
                    print(f"User {user} has expired subscription and is now set to standard.")
                else:
                    print(f"User {user} has an active subscription.")
    