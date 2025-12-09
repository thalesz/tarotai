prompt_analise_contexto_template = (
    "O contexto fornecido é '{context}'.\n"
    "Os tópicos disponíveis são: {topic_name}.\n"
    "Analise o contexto e retorne todos os tópicos que se encaixam, no formato ['topic1', 'topic2', ...].\n"
    "O formato deve ser exatamente o seguinte: ['topic1', 'topic2', ...].\n"
    "Se não houver tópicos correspondentes, retorne uma lista vazia []. Mande no máximo tres topicos, não ultrapasse.\n"
    "O formato deve ser respeitado, pois o restante da API depende disso.\n"
)

role_analise_contexto = (
    "Você é um especialista em análise de contexto e categorização. Sua tarefa é identificar os tópicos mais relevantes com base no contexto fornecido."
)
