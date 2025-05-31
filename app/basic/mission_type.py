from datetime import datetime

mission_types = [
    {
        "id": 1,
        "name": "Compartilhar tiragem em uma rede social",
        "description": "Compartilhar uma tiragem em uma rede social para ganhar recompensas.",
        "status": 2,
        "recurrence_type": 1,  # DAILY
        "recurrence_mode": 1,  # CALENDAR
        "reset_time": "00:00:00",
        "expiration_date": None,
        "relative_days": None,
        "auto_renew": True,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
     {
        "id": 7,
        "name": "Abrir um biscoito da sorte",   
        "description": "Abrir um biscoito da sorte para receber uma mensagem especial.",
        "status": 2,
        "recurrence_type": 1,  # DAILY
        "recurrence_mode": 1,  # CALENDAR
        "reset_time": "00:00:00", 
        "expiration_date": None,
        "relative_days": None,
        "auto_renew": True,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 2,
        "name": "Avaliar uma tiragem gerada pela IA",
        "description": "Avaliar a precisão e utilidade de uma tiragem feita pela IA.",
        "status": 2,
        "recurrence_type": 2,  # WEEKLY
        "recurrence_mode": 1,  # CALENDAR
        "reset_time": "00:00:00", 
        "expiration_date": None,
        "relative_days": None,
        "auto_renew": True,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 8,
        "name": "Fazer uma leitura no oraculo semanal",
        "description": "Realizar uma leitura semanal no oráculo para obter orientações.",
        "status": 2,
        "recurrence_type": 2,  # WEEKLY
        "recurrence_mode": 1,  # CALENDAR
        "reset_time": "00:00:00",
        "expiration_date": None,
        "relative_days": None,
        "auto_renew": True,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 3,
        "name": "Enviar feedback detalhado",
        "description": "Escrever e enviar um feedback detalhado sobre sua experiência.",
        "status": 2,
        "recurrence_type": 3,  # MONTHLY
        "recurrence_mode": 1,  # CALENDAR
        "reset_time": "00:00:00",
        "expiration_date": None,
        "relative_days": None,
        "auto_renew": True,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 4,
        "name": "Evento especial anual",
        "description": "Participar de um evento comemorativo que ocorre uma vez por ano.",
        "status": 2,
        "recurrence_type": 4,  # YEARLY
        "recurrence_mode": 1,  # CALENDAR
        "reset_time": "00:00:00" ,
        "expiration_date": "2026-05-25T00:00:00",
        "relative_days": None,
        "auto_renew": False,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 5,
        "name": "Criar uma nova pergunta para a IA responder",
        "description": "Escrever uma pergunta original e solicitar uma tiragem da IA com base nela.",
        "status": 2,
        "recurrence_type": 5,  # ONCE
        "recurrence_mode": 2,  # USER_BASED
        "reset_time": "00:00:00",
        "expiration_date": "2025-05-30T00:00:00",
        "relative_days": 10,
        "auto_renew": False,
        "start_date": "2026-05-27T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    },
    {
        "id": 6,
        "name": "Evento de boas vindas",
        "description": "Entrar em um sorteio para ganhar prêmios.",
        "status": 2,
        "recurrence_type": 5,  # ONCE
        "recurrence_mode": 3,  # BY_EXPIRATION_DATE
        "reset_time": "00:00:00",
        "expiration_date": "2025-05-30T23:59:59",
        "relative_days": None,
        "auto_renew": False,
        "start_date": "2025-05-25T00:00:00",
        "created_at": "2024-01-01T00:00:00"
    }
]
