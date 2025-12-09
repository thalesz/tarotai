prompt_resumo_leitura_template = (
    "Resuma a leitura de tarot a seguir em uma frase curta e objetiva:\n"
    "Contexto: {context}\n"
    "Nome do Baralho: {deck_name}\n"
    "Tipo de Spread: {spread_name}\n"
    "Carta(s): {cards}\n"
    "Leitura: {reading}\n"
)

role_resumo_leitura = (
    "Você é um especialista em síntese de informações."
    "Sua tarefa é resumir a leitura de tarot fornecida, mantendo os pontos mais importantes e relevantes."
)
