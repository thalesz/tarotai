from pydantic import BaseModel, Field
from typing import Optional


class ConfirmationResponse(BaseModel):
    message: str = Field(..., example="Conta confirmada com sucesso!")
    email: Optional[str] = Field(None, example="user@example.com")


class ErrorResponse(BaseModel):
    message: str = Field(..., example="Usuário não encontrado.")
    detail: Optional[str] = Field(None, example="Descrição do erro (opcional)")
