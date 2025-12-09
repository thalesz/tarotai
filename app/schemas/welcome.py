from pydantic import BaseModel


class WelcomeResponse(BaseModel):
    message: str
    category: str
    source: str

    class Config:
        schema_extra = {
            "example": {
                "message": "Olá, Thales! Bem-vindo ao TarotAI — hoje é um ótimo dia para uma leitura rápida.",
                "category": "general",
                "source": "template",
            }
        }
