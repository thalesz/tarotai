from datetime import datetime
from pydantic import BaseModel
from sqlalchemy.sql import text  # Import text from sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession  # Import AsyncSession
from sqlalchemy.future import select  # Import select for async queries
from app.models.personalSign import PersonalSign# Importando o PersonalSignModel

class PersonalSignSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
        validate_assignment = True
        
    @staticmethod
    async def get_sign_by_planet_id(
        session: AsyncSession,
        planet_id: int, 
        user_id: int
    ) -> list[dict]:
        """
        Busca todos os PersonalSign para um planeta específico e usuário obrigatório.
        Retorna uma lista de dicionários com as chaves: zodiac_sign, description, degree.
        Se não houver resultados, retorna uma lista vazia.
        """
        stmt = select(
            PersonalSign.zodiac_sign,
            PersonalSign.description,
            PersonalSign.degree
        ).where(
            (PersonalSign.planet == planet_id) & (PersonalSign.user == user_id)
        )
        result = await session.execute(stmt)
        rows = result.all()
        if not rows:
            return []
        return [
            {
                "zodiac_sign": zodiac_sign,
                "description": description,
                "degree": degree
            }
            for zodiac_sign, description, degree in rows
        ]
    @staticmethod
    async def get_sign_and_degree_by_user_and_planet(
        session: AsyncSession,
        user_id: int,
        planet_id: int
    ) -> tuple[int, float] | None:
        """
        Busca o signo e grau do PersonalSign para (user_id, planet_id).
        Retorna uma tupla (signo, grau) ou None se não encontrado.
        """
        stmt = select(PersonalSign.zodiac_sign, PersonalSign.degree).where(
            PersonalSign.user == user_id,
            PersonalSign.planet == planet_id
        )
        result = await session.execute(stmt)
        personal_sign: tuple[int, float] | None = result.one_or_none()

        if personal_sign:
            return personal_sign
        return None
        
    @staticmethod
    async def create_or_update(
        session: AsyncSession,
        user_id: int,
        planet_id: int,
        zodiac_sign_id: int,
        description: str,
        degree: float
    ) -> PersonalSign:
        """
        Cria um PersonalSign novo ou atualiza o existente para (user_id, planet_id, zodiac_sign_id).
        """

        # 1) Tenta buscar existente
        stmt = select(PersonalSign).where(
            PersonalSign.user == user_id,
            PersonalSign.planet == planet_id
        )
        result = await session.execute(stmt)
        existing: PersonalSign | None = result.scalars().one_or_none()

        if existing:
            # 2) Atualiza campos
            existing.zodiac_sign = zodiac_sign_id
            existing.description = description
            existing.degree = degree
            session.add(existing)  # marca para update
            await session.commit()
            await session.refresh(existing)
            return existing

        # 3) Se não existe, cria
        new_sign = PersonalSign(
            user=user_id,
            planet=planet_id,
            zodiac_sign=zodiac_sign_id,
            description=description,
            degree=degree
        )
        session.add(new_sign)
        await session.commit()
        await session.refresh(new_sign)
        return new_sign

class PersonalSignSchema(PersonalSignSchemaBase):
    id: int
    user: int
    planet: int
    zodiac_sign: int
    description: str
    degree: float