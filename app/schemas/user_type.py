from pydantic import BaseModel, Field
from sqlmodel import SQLModel
from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.expression import any_
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
    async def get_accessible_card_styles_by_user_type(
        session: AsyncSession, user_type_id: int
    ) -> List[int]:
        """
        Retorna os IDs dos estilos de cartas acessíveis para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.card_styles).where(UserTypeModel.id == user_type_id)
        )
        accessible_card_styles = result.scalar_one_or_none()
        return accessible_card_styles if accessible_card_styles else []
    
    @staticmethod
    async def get_planets_by_user_type_id(
        session: AsyncSession, user_type_id: int
    ) -> List[int]:
        """
        Retorna os IDs dos planetas disponíveis para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.planet).where(UserTypeModel.id == user_type_id)
        )
        planets = result.scalar_one_or_none()
        return planets if planets else []
        
    @staticmethod
    async def get_context_amount_by_id(session: AsyncSession, user_type_id: int) -> Optional[int]:
        """
        Retorna a quantidade de contexto disponível para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.context_amount).where(UserTypeModel.id == user_type_id)
        )
        return result.scalar_one_or_none()
        
    @staticmethod
    async def check_reading_style_belongs_to_user(
        session: AsyncSession, user_type_id: int, reading_style_id: int
    ) -> bool:
        """
        Verifica se o estilo de leitura pertence ao usuário especificado.
        """
        # print(f"Verificando se o estilo de leitura {reading_style_id} pertence ao usuário {user_id}")
        result = await session.execute(
            select(UserTypeModel.id).where(
                UserTypeModel.id == user_type_id,
                reading_style_id == any_(UserTypeModel.reading_style)
            )
        )
        
        return result.scalars().first() is not None
    
    
    
        
    @staticmethod
    async def get_reading_styles_by_user_type_id(
        session: AsyncSession, user_type_id: int
    ) -> List[int]:
        """
        Retorna os IDs dos estilos de leitura disponíveis para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.reading_style).where(UserTypeModel.id == user_type_id)
        )
        reading_styles = result.scalar_one_or_none()
        return reading_styles if reading_styles else []
        
    @staticmethod
    async def get_daily_gift_by_user_type(
        session: AsyncSession, user_type_id: int
    ) -> List[int]:
        """
        Retorna os IDs dos brindes diários disponíveis para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.daily_gift).where(UserTypeModel.id == user_type_id)
        )
        daily_gifts = result.scalar_one_or_none()
        return daily_gifts if daily_gifts else []
        
        
    @staticmethod
    async def get_id_by_name(session: AsyncSession, name: str) -> int:
        """
        Retorna o ID do tipo de usuário pelo nome.
        """
        result = await session.execute(
            select(UserTypeModel.id).where(UserTypeModel.name == name)
        )
        return result.scalar() if result else None
        
    @staticmethod
    async def get_token_amount_by_id(session: AsyncSession, user_type_id: int) -> int:
        """
        Retorna a quantidade de tokens disponíveis para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.token_amount).where(UserTypeModel.id == user_type_id)
        )
        return result.scalar() if result else None
        
    @staticmethod
    async def check_deck_belongs_to_user( 
        session: AsyncSession, user_id: int, deck_id: int
    ) -> bool:
        """
        Verifica se o deck pertence ao usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.id).where(
                UserTypeModel.id == user_id,
                deck_id == any_(UserTypeModel.accessible_card_type_ids)
            )
        )
        
        return result.scalars().first() is not None
    
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
    async def get_accessible_card_types_by_user_type(
        session: AsyncSession, user_type_id: int
    ) -> List[int]:
        """
        Retorna os IDs dos tipos de cards acessíveis para o tipo de usuário especificado.
        """
        result = await session.execute(
            select(UserTypeModel.accessible_card_type_ids).where(UserTypeModel.id == user_type_id)
        )
        accessible_card_types = result.scalar_one_or_none()
        return accessible_card_types if accessible_card_types else []
    
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
                    accessible_card_type_ids=user_type["accessible_card_type_ids"],
                    token_amount=user_type["token_amount"],
                    daily_gift=user_type.get("daily_gift", []),
                    reading_style=user_type.get("reading_style", []),
                    context_amount=user_type.get("context_amount", 0),
                    planet=user_type.get("planet", []),
                    card_styles=user_type.get("card_styles", [])
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
    daily_gifts: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(Integer), nullable=True, default=[])
    )  # IDs dos brindes diários disponíveis para o tipo de usuário
    #quantidade de token
    token_amount: Optional[int] = Field(
        sa_column=Column(Integer, nullable=True, default=0)
    )  # Quantidade de tokens disponíveis para o tipo de usuário
    reading_style: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(Integer), nullable=True, default=[])
    )  # IDs dos estilos de leitura disponíveis para o tipo de usuário
    context_amount: Optional[int] = Field(
        sa_column=Column(Integer, nullable=True, default=0)
    )  # Quantidade de contexto disponível para o tipo de usuário
    planet: Optional[List[int]] = Field(
        sa_column=Column(ARRAY(Integer), nullable=True, default=[])
    )