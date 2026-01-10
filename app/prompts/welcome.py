WELCOME_MESSAGES = {
    "general": "Bem-vindo ao TarotAI — seu guia de sabedoria e autoconhecimento através do tarot.",
    "zodiac": "Bem-vindo à seção Zodíaco! Descubra insights astrológicos profundos e personalizados para sua jornada.",
    "deck": "Bem-vindo à nossa coleção de Baralhos! Escolha o deck que mais ressoa com sua energia.",
    "reading": "Pronto para uma leitura? Abra-se às mensagens das cartas e encontre clareza.",
}

WELCOME_GREETINGS = {
    "general": "Bem-vindo",
    "zodiac": "Bem-vindo às estrelas",
    "deck": "Bem-vindo ao baralho",
    "reading": "Bem-vindo à leitura",
}


def build_welcome_role() -> str:
    return (
        "Você é um assistente espiritual acolhedor e intuitivo do TarotAI, especializado em criar boas-vindas "
        "significativas e personalizadas. Seu tom é leve, simpático e genuíno — como um amigo sábio recebendo alguém. "
        "As mensagens devem ter no máximo 1–2 frases, ser diretas e inspiradoras. "
        "Use um tom profundo mas acessível, evitando linguagem robótica, formalidade excessiva ou tecnicismo. "
        "Não utilize listas, markdown ou explicações — apenas uma mensagem fluida, espontânea e autêntica."
    )


def build_welcome_prompt(user_name: str | None, friendly_name: str, category: str, include_date: bool, date_context: str, weekday_pt: str) -> str:
    """
    Constrói o prompt para geração de mensagem de boas-vindas personalizada.
    
    Args:
        user_name: Nome do usuário, se disponível
        friendly_name: Nome amigável da seção (e.g., 'o aplicativo', 'a seção Zodíaco')
        category: Categoria da saudação (general, zodiac, deck, reading)
        include_date: Se deve mencionar a data
        date_context: String com data e dia da semana
        weekday_pt: Dia da semana em português
    
    Returns:
        Prompt formatado para a IA
    """
    date_instruction = (
        f" Você pode incluir um contexto temporal natural. {date_context}"
        if include_date
        else ""
    )

    if user_name:
        prompt = (
            f"Crie uma mensagem de boas-vindas em duas partes para {user_name} em {friendly_name}.\n\n"
            f"FORMATO OBRIGATÓRIO:\n"
            f"[Saudação variada], {user_name}! [Uma frase com máximo 20 palavras]\n\n"
            f"A primeira parte deve ser uma SAUDAÇÃO VARIADA E CRIATIVA (pode ser 'Bem-vindo', 'Seja bem-vindo', 'Olá', 'Bem-vindo de volta', etc.), "
            f"seguida de '{user_name}!' — terminada sempre em '!'\n"
            f"A segunda parte deve ser UMA ÚNICA frase com NO MÁXIMO 20 PALAVRAS que combine com {friendly_name}, "
            f"transmitindo acolhimento genuíno. Seja conciso e inspirador."
            + date_instruction
        )
    else:
        prompt = (
            f"Gere uma mensagem de boas-vindas em duas partes para alguém que acabou de acessar {friendly_name}.\n\n"
            f"FORMATO OBRIGATÓRIO:\n"
            f"[Saudação variada]! [Uma frase com máximo 20 palavras]\n\n"
            f"A primeira parte é uma SAUDAÇÃO VARIADA E CRIATIVA (pode ser 'Bem-vindo', 'Seja bem-vindo', 'Olá', 'Bem-vindo', etc.) — "
            f"terminada sempre em '!'\n"
            f"A segunda parte deve ser UMA ÚNICA frase com NO MÁXIMO 20 PALAVRAS profunda e autêntica sobre {friendly_name}, "
            f"transmitindo acolhimento genuíno. Seja conciso e direto."
            + date_instruction
        )
    
    return prompt
