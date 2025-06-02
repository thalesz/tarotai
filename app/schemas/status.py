from fastapi import HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import Integer, Column, String, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.status import StatusModel

from app.basic.status import statuses

class StatusSchemaBase(BaseModel):

    class Config:
        orm_mode = True
        arbitrary_types_allowed = (
            True  # Allows arbitrary types like SQLAlchemy's DateTime
        )
        validate_assignment = True
    @staticmethod
    async def sync_statuses(session: AsyncSession):
        for status in statuses:
            result = await session.execute(
                select(StatusModel).where(StatusModel.id == status["id"])
            )
            existing = result.scalars().first()

            if not existing:
                new_status = StatusModel(
                    id=status["id"],
                    name=status["name"],
                    label=status["label"]
                )
                session.add(new_status)
                try:
                    await session.commit()
                    print(f'Status com ID "{status["id"]}" adicionado.')
                except IntegrityError:
                    await session.rollback()
                    print(f'Erro ao adicionar ID "{status["id"]}". Conflito de integridade.')
            else:
                print(f'Status com ID "{status["id"]}" já existe no banco.')
                
    @staticmethod
    async def get_name_by_id(db: AsyncSession, id: int) -> str:
        """
        Retrieves the name of a status by its ID.
        """
        query = select(StatusModel).where(StatusModel.id == id)
        result = await db.execute(query)
        status = result.scalar_one_or_none()

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Status with ID {id} not found.",
            )

        return status.name
        
    @staticmethod
    async def get_id_by_name(db: AsyncSession, name):
        """
        Retrieves the ID(s) of a status by its name or list of names.
        Returns an int if a single name is provided, or a list of ints if a list is provided.
        """
        if isinstance(name, str):
            query = select(StatusModel).where(StatusModel.name == name)
            result = await db.execute(query)
            status = result.scalar_one_or_none()
            if not status:
                raise HTTPException(
                    status_code=404,
                    detail=f"Status '{name}' not found.",
                )
            return status.id
        elif isinstance(name, list):
            query = select(StatusModel).where(StatusModel.name.in_(name))
            result = await db.execute(query)
            statuses = result.scalars().all()
            found_names = {s.name for s in statuses}
            missing = set(name) - found_names
            if missing:
                raise HTTPException(
                    status_code=404,
                    detail=f"Status(es) '{', '.join(missing)}' not found.",
                )
            return [s.id for s in statuses]
        else:
            raise HTTPException(
                status_code=400,
                detail="Input must be a string or a list of strings.",
            )
class StatusSchema(StatusSchemaBase):
    id: Optional[int] = Field(
        sa_column=Column(Integer, primary_key=True, autoincrement=True)
    )
    name: str = Field(
        sa_column=Column(String(50), nullable=False, unique=True)
    )  # Nome do deck
    description: str = Field(
        sa_column=Column(String(255), nullable=True)
    )  # Descrição do deck

    