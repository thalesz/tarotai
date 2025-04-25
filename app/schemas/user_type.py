from pydantic import BaseModel, Field
from sqlmodel import SQLModel
from sqlalchemy import Column, String, Integer, ARRAY
from sqlalchemy.exc import IntegrityError
from typing import List, Optional
from app.core.base import Base  # Importando o Base correto
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user_type import UserTypeModel  # Importando o UserTypeModel
from app.basic.user_type import user_types


class UserTypeSchemaBase(BaseModel):
    
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
    
    
    @staticmethod
    async def get_name_by_id(session: AsyncSession, id: int) -> str:
        """
        Retorna o nome do tipo de usuário pelo ID.
        """
        result = await session.execute(
            select(UserTypeModel.name).where(UserTypeModel.id == id)
        )
        return result.scalar() if result else None

    @staticmethod 
    async def verify_user_type_exists(session: AsyncSession, user_type_id: int) -> bool:
        """
        Verifica se um tipo de usuário existe no banco de dados.
        """
        result = await session.execute(
            select(UserTypeModel.id).where(UserTypeModel.id == user_type_id)
        )
        return result.scalar() is not None
        
    @staticmethod
    async def sync_user_types(session: AsyncSession):
        if not isinstance(session, AsyncSession):
            raise TypeError("The session must be an instance of AsyncSession.")
        for user_type in user_types:
            # Verifica se já existe no banco pelo ID
            result = await session.execute(
                select(UserTypeModel).where(UserTypeModel.id == user_type["id"])
            )
            existing = result.scalars().first()

            if not existing:
                new_user_type = UserTypeModel(
                    id=user_type["id"],
                    name=user_type["name"],
                    accessible_card_type_ids=user_type["accessible_card_type_ids"]
                )
                session.add(new_user_type)
                try:
                    await session.commit()
                    print(f'UserType ID {user_type["id"]} adicionado.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Erro ao adicionar ID {user_type["id"]}. Conflito ou erro de integridade.')
            else:
                print(f'UserType ID {user_type["id"]} já existe no banco.')

    @staticmethod
    async def get_all_user_types(session: AsyncSession) -> list:
        """
        Retorna somente id e name de todos os tipos de usuário.
        """
        user_types = await session.execute(select(UserTypeModel.id, UserTypeModel.name))
        return user_types.all()
    
    


class UserTypeSchema(UserTypeSchemaBase):
    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(
        sa_column=Column(String(50), nullable=False)
    )  # Nome do tipo de usuário
    accessible_card_type_ids: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(Integer), nullable=True)
    )  # IDs dos tipos de cards acessíveis
