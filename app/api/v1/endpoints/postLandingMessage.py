from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email import EmailConfirmationSchema
from app.core.configs import settings

router = APIRouter()


class LandingContactSchema(BaseModel):
    name: str
    email: EmailStr
    message: str


@router.post("/", summary="Receber mensagem do landing e enviar para admin")
async def post_landing_message(payload: LandingContactSchema):
    admin_email = getattr(settings, "ADMIN_EMAIL", settings.SMTP_USERNAME)
    try:
        await EmailConfirmationSchema.send_contact_email(admin_email, payload.name, payload.email, payload.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao enviar email")
    return {"detail": "Mensagem enviada com sucesso"}
