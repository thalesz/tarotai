from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy import select  # Import the select function
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.exc import IntegrityError  # Import IntegrityError
from app.models.mission import MissionModel  # Import MissionModel to fix NameError
from app.schemas.status import StatusSchemaBase  # Import StatusSchemaBase to fix NameError
from datetime import datetime  # Import datetime to fix NameError

class MissionSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True

    @staticmethod
    async def mission_exists(session: AsyncSession, mission_id: int, user_id: int = None) -> bool:
        """
        Verifica se uma missão existe pelo ID. Se user_id for fornecido, verifica se a missão pertence ao usuário.
        """
        try:
            query = select(MissionModel).where(MissionModel.id == mission_id)
            if user_id is not None:
                query = query.where(MissionModel.user == user_id)
            result = await session.execute(query)
            mission = result.scalars().first()
            return mission is not None
        except Exception as e:
            await session.rollback()
            print(f'Erro ao verificar existência da missão: {e}')
            return False
        

    @staticmethod
    async def get_used_at_by_id(
        session: AsyncSession, mission_id: int
    ) -> datetime | None:
        """
        Retorna a data de uso de uma missão pelo ID.
        """
        try:
            print(f"Buscando data de uso da missão ID {mission_id}.")
            result = await session.execute(
                select(MissionModel.used_at).where(MissionModel.id == mission_id)
            )
            used_at = result.scalar_one_or_none()
            return used_at if used_at is not None else None

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar data de uso da missão ID {mission_id}. Conflito de integridade: {e.orig}')
            return None
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar data de uso da missão ID {mission_id}: {e}')
            return None
    
    @staticmethod
    async def get_created_at_by_id(
        session: AsyncSession, mission_id: int
    ) -> datetime | None:
        """
        Retorna a data de criação de uma missão pelo ID.
        """
        try:
            # print(f"Buscando data de criação da missão ID {mission_id}.")
            result = await session.execute(
                select(MissionModel.created_at).where(MissionModel.id == mission_id)
            )
            created_at = result.scalar_one_or_none()
            return created_at if created_at is not None else None

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar data de criação da missão ID {mission_id}. Conflito de integridade: {e.orig}')
            return None
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar data de criação da missão ID {mission_id}: {e}')
            return None
        
    @staticmethod
    async def update_mission_status(
        session: AsyncSession, mission_id: int, new_status: int
    ) -> MissionModel | None:
        """
        Atualiza o status de uma missão pelo ID.
        """
        try:
            print(f"Atualizando status da missão ID {mission_id} para {new_status}.")
            result = await session.execute(
                select(MissionModel).where(MissionModel.id == mission_id)
            )
            existing_mission = result.scalars().first()

            if existing_mission:
                existing_mission.status = new_status
                existing_mission.used_at = datetime.now() if new_status == 7 else None  # Define used_at se o status for 'completed'
                await session.commit()
                print(f'Status da missão ID {mission_id} atualizado para {new_status}.')
                return existing_mission
            else:
                print(f'Missão ID {mission_id} não encontrada.')
                return None

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao atualizar status da missão ID {mission_id}. Conflito de integridade: {e.orig}')
            return None
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao atualizar status da missão ID {mission_id}: {e}')
            return None
    @staticmethod
    async def get_list_id_by_user_and_types_and_period_and_status(
        session: AsyncSession,
        user_id: int,
        mission_type_id: int,
        status_ids: list[int],
        start_date: datetime = None,
        end_date: datetime = None
    ) -> list[int]:
        """
        Retorna uma lista de IDs de missões de um usuário para um tipo de missão,
        podendo filtrar por período (start_date, end_date) e por uma lista de status.
        As datas são opcionais e podem ser usadas individualmente ou juntas.
        """
        try:
            # print(f"Buscando missões para usuário {user_id}, tipo {mission_type_id} com status {status_ids}, start_date={start_date}, end_date={end_date}.")
            query = select(MissionModel.id).where(
                MissionModel.user == user_id,
                MissionModel.mission_type == mission_type_id,
                MissionModel.status.in_(status_ids)
            )
            if start_date is not None:
                query = query.where(MissionModel.created_at >= start_date)
            if end_date is not None:
                query = query.where(MissionModel.created_at <= end_date)

            result = await session.execute(query)
            mission_ids = result.scalars().all()
            # if mission_ids:
            #     print(f'Missões encontradas: {mission_ids}')
            # else:
            #     print('Nenhuma missão encontrada.')
            return mission_ids

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar missões. Conflito de integridade: {e.orig}')
            return []
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar missões: {e}')
            return []
    @staticmethod
    async def get_id_by_user_and_types_and_period_and_status(
        session: AsyncSession,
        user_id: int,
        mission_type_id: int,
        start_date: datetime,
        end_date: datetime,
        status_ids: list[int]
    ) -> int | None:
        """
        Retorna o ID da missão de um usuário para um tipo de missão,
        dentro de um período e para uma lista de status.
        """
        try:
            print(f"Buscando missão para usuário {user_id}, tipo {mission_type_id} entre {start_date} e {end_date} com status {status_ids}.")
            result = await session.execute(
                select(MissionModel.id).where(
                    MissionModel.user == user_id,
                    MissionModel.mission_type == mission_type_id,
                    MissionModel.status.in_(status_ids),
                    MissionModel.created_at >= start_date,
                    MissionModel.created_at <= end_date
                )
            )
            mission_id = result.scalars().first()
            if mission_id:
                print(f'Missão encontrada: {mission_id}')
            else:
                print('Nenhuma missão encontrada.')
            return mission_id

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar missão. Conflito de integridade: {e.orig}')
            return None
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar missão: {e}')
            return None
    @staticmethod
    async def get_mission_by_user_and_type(
        session: AsyncSession, user_id: int, mission_type_id: int, status_id: int
    ) -> MissionModel | None:
        """
        Retorna uma missão específica de um usuário pelo ID do tipo de missão.
        """
        try:
            print(f"Buscando missão para usuário {user_id} e tipo {mission_type_id} com status {status_id}.")
            result = await session.execute(
                select(MissionModel).where(
                    MissionModel.user == user_id,
                    MissionModel.mission_type == mission_type_id,
                    MissionModel.status == status_id
                )
            )
            existing_mission = result.scalars().first()
            if existing_mission:
                print(f'Missão encontrada: ID {existing_mission.id}')
            else:
                print('Nenhuma missão encontrada.')
            return existing_mission
            

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar missão. Conflito de integridade: {e.orig}')
            return None
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar missão: {e}')
            return None
        
        
    @staticmethod
    async def verify_mission_exists(
        session: AsyncSession, user_id: int, mission_type_id: int, status_id: int
    ) -> bool:
        """
        Verifica se uma missão já existe para um usuário específico e tipo de missão e status.
        """
        try:
            result = await session.execute(
                select(MissionModel).where(
                    MissionModel.user == user_id,
                    MissionModel.mission_type == mission_type_id,
                    MissionModel.status == status_id
                )
            )
            existing_mission = result.scalars().first()
            return existing_mission is not None

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao verificar missão. Conflito de integridade: {e.orig}')
            return False
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao verificar missão: {e}')
            return False
    
    @staticmethod
    async def get_all_missions_by_user_id_and_created_at(
        session: AsyncSession, user_id: int, created_at: datetime
    ):
        """
        Retorna todas as missões de um usuário específico criadas no mesmo dia de 'created_at'.
        """
        try:
            print(f"Buscando missões para o usuário {user_id} criadas em {created_at}.")
            # Compara apenas o ano, mês e dia
            result = await session.execute(
                select(MissionModel).where(
                    MissionModel.user == user_id,
                    func.date(MissionModel.created_at) == created_at.date()
                )
            )
            missions = result.scalars().all()
            return missions

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar missões para o usuário {user_id}. Conflito de integridade: {e.orig}')
            return []
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar missões para o usuário {user_id}: {e}')
            return []
    
    @staticmethod
    async def create_mission_by_type_and_user_id(
        session: AsyncSession, mission_type_id_list: list[int], user_id_list: list[int]
    ):
        """
        Para cada tipo de missão e usuário, verifica se já existe uma missão pendente.
        Se existir, apenas atualiza o created_at.
        Se não existir, cria uma nova missão.
        """
        print(f"MissionType ID list: {mission_type_id_list}")
        print(f"User ID list: {user_id_list}")

        pending_status = await StatusSchemaBase.get_id_by_name(session, "pending_confirmation")

        for mission_type_id in mission_type_id_list:
            for user_id in user_id_list:
                try:
                    # Verifica se já existe missão pendente
                    result = await session.execute(
                        select(MissionModel).where(
                            MissionModel.mission_type == mission_type_id,
                            MissionModel.user == user_id,
                            MissionModel.status == pending_status
                        )
                    )
                    existing_mission = result.scalars().first()

                    if existing_mission:
                        print(f'Missão ID {existing_mission.id} já existe com status pendente. Atualizando created_at.')
                        await MissionSchemaBase.modified_created_at(session, existing_mission.id)
                    else:
                        print(f'Criando nova missão para usuário {user_id} e tipo {mission_type_id}.')
                        await MissionSchemaBase.create_mission(session, mission_type_id, user_id)

                except IntegrityError as e:
                    await session.rollback()
                    print(f'Erro de integridade ao processar missão para usuário {user_id} e tipo {mission_type_id}: {e.orig}')
                except Exception as e:
                    await session.rollback()
                    print(f'Erro inesperado ao processar missão para usuário {user_id} e tipo {mission_type_id}: {e}')
                    
    @staticmethod
    async def modified_created_at(
        session: AsyncSession, mission_id: int, period_start: datetime
    ):
        """
        Modifica a data de criação de uma missão para o valor de period_start.
        """
        try:
            result = await session.execute(
                select(MissionModel).where(MissionModel.id == mission_id)
            )
            existing_mission = result.scalars().first()

            if existing_mission:
                existing_mission.created_at = period_start
                await session.commit()
                print(f'Data de criação da missão ID {mission_id} atualizada para {period_start}.')
            else:
                print(f'Missão ID {mission_id} não encontrada.')

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao atualizar data de criação da missão ID {mission_id}. Conflito de integridade: {e.orig}')
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao atualizar data de criação da missão ID {mission_id}: {e}')

    @staticmethod
    async def create_mission(
        session: AsyncSession, mission_type_id: int, user_id: int
    ):
        """
        Cria uma nova missão para o usuário com o tipo especificado e status 'pending_confirmation'.
        """
        try:
            status = await StatusSchemaBase.get_id_by_name(session, "pending_confirmation")
            # print(f"Creating mission: user={user_id}, mission_type={mission_type_id}, status={status}")

            new_mission = MissionModel(
                mission_type=mission_type_id,
                user=user_id,
                status=status,
                created_at=datetime.now(),
                used_at=None,
            )

            session.add(new_mission)
            await session.flush()  # Popula new_mission.id antes de commit

            # print(f'Missão criada com ID {new_mission.id}.')
            await session.commit()

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao criar missão. Conflito de integridade: {e.orig}')
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao criar missão: {e}')
    
    @staticmethod
    async def get_status_by_mission_id(
        session: AsyncSession, mission_id: int
    ) -> int | None:
        """
        Retorna o status de uma missão pelo ID.
        """
        try:
            # print(f"Buscando status da missão ID {mission_id}.")
            result = await session.execute(
                select(MissionModel.status).where(MissionModel.id == mission_id)
            )
            status = result.scalar_one_or_none()
            return status if status is not None else None

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao buscar status da missão ID {mission_id}. Conflito de integridade: {e.orig}')
            return None
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao buscar status da missão ID {mission_id}: {e}')
            return None

    @staticmethod
    async def modify_mission_status(
        session: AsyncSession, mission_id: int, new_status: int, user_id: int
    ):
        """
        Modifica o status de uma missão.
        """
        try:
            result = await session.execute(
                select(MissionModel).where(
                    MissionModel.id == mission_id,
                    MissionModel.user == user_id
                )
            )
            existing_mission = result.scalars().first()

            if existing_mission:
                existing_mission.status = new_status
                await session.commit()
                print(f'Status da missão ID {mission_id} atualizado para {new_status}.')
            else:
                print(f'Missão ID {mission_id} não encontrada para o usuário {user_id}.')

        except IntegrityError as e:
            await session.rollback()
            print(f'Erro ao atualizar missão ID {mission_id}. Conflito de integridade: {e.orig}')
        except Exception as e:
            await session.rollback()
            print(f'Erro inesperado ao atualizar missão ID {mission_id}: {e}')

class MissionSchema(MissionSchemaBase):
    """
    Schema for SpreadType.
    """
    id: int
    name: str
    description: str | None = None
