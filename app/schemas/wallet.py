from pydantic import BaseModel, EmailStr, Field, ValidationError
from fastapi import HTTPException, status
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, func
from app.models.user import UserModel
from app.core.security import pwd_context
from datetime import datetime
from app.models.wallet import WalletModel  # Assuming WalletModel is the ORM model for the wallet


class WalletSchemaBase(BaseModel):
    
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True  # Allows arbitrary types like SQLAlchemy's DateTime
        validate_assignment = True
        
    @staticmethod
    async def confirm_wallet_status_using_id(user_id: int, session: AsyncSession) -> dict:
        """
        Atualiza o status da carteira para "active" usando o ID da carteira.
        """
        wallet = await session.execute(
            select(WalletModel).where(WalletModel.user_id == user_id)
        )
        wallet = wallet.scalars().first()

        if not wallet:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Carteira não encontrada",
            )

        wallet.status = "active"
        await session.commit()
        await session.refresh(wallet)
        return {
            "message": "Usuário confirmado com sucesso",
            "id": wallet.id,
            "user_id": wallet.user_id,
            "status": wallet.status,
        }
        
    @staticmethod
    async def create_wallet(user_id: int, wallet_type: str, session: AsyncSession) -> "WalletSchema":

        new_wallet = WalletModel(
            user_id=user_id,
            balance=0.0,
            created_at=datetime.now(),
            currency=wallet_type,
            status="pending_confirmation"
        )
        session.add(new_wallet)
        await session.commit()
        await session.refresh(new_wallet)
        return new_wallet


class WalletSchema(WalletSchemaBase):
    __tablename__ = "wallets"
    id: Optional[int] = Field(sa_column=Column(Integer, primary_key=True, autoincrement=True))
    user_id: int = Field(sa_column=Column(Integer, ForeignKey("users.id"), unique=True, nullable=False))  # Relacionamento 1-1 com UserModel
    balance: float = Field(sa_column=Column(Float, nullable=False, default=0.0))  # Saldo da carteira
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.timezone.utc))
    currency: str = Field(sa_column=Column(String(10), nullable=False, default="BRL"))  # Moeda padrão (BRL é o padrão)
    status: str = Field(sa_column=Column(String(50), nullable=False, default="active"))  # Status da carteira



