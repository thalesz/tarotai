import smtplib
from email.mime.text import MIMEText
from pydantic import BaseModel
from typing import Optional
from app.core.configs import settings


class EmailSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True

    subject: str
    body: str
    recipient: str
    sender: str


class EmailSchema(EmailSchemaBase):
    pass


class EmailConfirmationSchema(EmailSchemaBase):
    confirmation_token: str

    @staticmethod
    def _send_email(subject: str, body: str, recipient: str) -> EmailSchemaBase:
        msg = MIMEText(body, "html")  # 👈 ESSENCIAL!
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = recipient

        try:
            with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_SECRET_KEY)
                server.send_message(msg)
                print(f"Email enviado para {recipient}")
        except Exception as e:
            print(f"Erro ao enviar email: {e}")
            raise

        return EmailSchemaBase(
            subject=subject,
            body=body,
            recipient=recipient,
            sender=settings.SMTP_USERNAME
        )


    @staticmethod
    async def send_confirmation_email(email: str, token: str) -> EmailSchemaBase:
        subject = "Tarot - Confirmação de Email - Ação Necessária"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                <h2 style="color: #4CAF50; text-align: center;">Confirmação de Email</h2>
                <p>Olá,</p>
                <p>Obrigado por se registrar em nossa plataforma. Para concluir o processo de cadastro, por favor, confirme seu email clicando no botão abaixo:</p>
                <div style="text-align: center; margin: 20px 0;">
                <form action="http://localhost:8000/api/v1/confirm-email/receive/{token}" style="display: inline-block;">
                    <button type="submit" style="padding: 10px 20px; font-size: 16px; color: #fff; background-color: #4CAF50; border: none; border-radius: 5px; cursor: pointer;">
                    Confirmar Email
                    </button>
                </form>
                </div>
                <p>Se você não realizou este cadastro, por favor, ignore este email.</p>
                <p>Atenciosamente,<br>Equipe de Suporte</p>
            </div>
            </body>
        </html>
        """
        return EmailConfirmationSchema._send_email(subject, body, email)

    @staticmethod
    async def send_active_email(email: str) -> EmailSchemaBase:
        subject = "Tarot - Conta Confirmada com Sucesso"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px; background-color: #f9f9f9;">
                    <h2 style="color: #4CAF50; text-align: center;">Conta Confirmada</h2>
                    <p>Olá,</p>
                    <p>Sua conta foi confirmada com sucesso. Você já pode acessar a plataforma e aproveitar todos os recursos disponíveis.</p>
                    <p>Atenciosamente,<br>Equipe de Suporte</p>
                </div>
            </body>
        </html>
        """
        return EmailConfirmationSchema._send_email(subject, body, email)
