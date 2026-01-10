def build_daily_tips_role():
    """
    Build the role for the daily tips generation.
    """
    return """Você é um especialista em desenvolvimento pessoal e bem-estar, 
    com profundo conhecimento em psicologia positiva, mindfulness e crescimento pessoal. 
    Sua função é gerar dicas diárias práticas e inspiradoras que ajudem as pessoas a 
    melhorar sua qualidade de vida, tomar melhores decisões e manter o equilíbrio emocional."""


def build_daily_tips_prompt():
    """
    Build the prompt for generating daily tips with fixed titles.
    """
    prompt = f"""
Gere 6 dicas diárias de desenvolvimento pessoal e bem-estar para hoje.

IMPORTANTE: Os títulos são fixos e já estão definidos. Você deve gerar APENAS o texto que COMPLETA cada título (na ordem):

1. "Mantenha" + [seu texto - será lido como "Mantenha [seu texto]"]
2. "É uma boa ideia" + [seu texto - será lido como "É uma boa ideia [seu texto]"]
3. "Evite" + [seu texto - será lido como "Evite [seu texto]"]
4. "Fique de olho" + [seu texto - será lido como "Fique de olho em [seu texto]"]
5. "Fuja de" + [seu texto - será lido como "Fuja de [seu texto]"]
6. "Reavalie" + [seu texto - será lido como "Reavalie [seu texto]"]

REGRAS CRÍTICAS:
- O texto DEVE SER UMA CONTINUAÇÃO NATURAL E DIRETA DO TÍTULO
- Quando o título e o texto forem concatenados, a frase DEVE FAZER SENTIDO GRAMATICAL PERFEITO
- Cada complemento deve ter entre 5 a 12 palavras
- NÃO adicione artigos ou palavras extras que já estão no título
- Use linguagem natural, coloquial e acessível
- Inclua elementos do COTIDIANO: trabalho, casa, relações pessoais, alimentação, sono, redes sociais, exercícios, etc.
- As dicas devem ser variadas e abordar diferentes aspectos da vida diária
- Não repita ideias entre as dicas
- Foque em ações tangíveis que qualquer pessoa pode fazer hoje

EXEMPLOS DE COMPLEMENTOS CORRETOS (que soam naturais quando concatenados):
- Mantenha + "contato com pessoas que te fazem rir" = "Mantenha contato com pessoas que te fazem rir" ✓
- É uma boa ideia + "alongar o corpo ao acordar" = "É uma boa ideia alongar o corpo ao acordar" ✓
- Evite + "pular refeições ou comer com pressa" = "Evite pular refeições ou comer com pressa" ✓
- Fique de olho em + "sinais de cansaço mental no meio do dia" = "Fique de olho em sinais de cansaço mental no meio do dia" ✓
- Fuja de + "comparações com outras pessoas nas redes sociais" = "Fuja de comparações com outras pessoas nas redes sociais" ✓
- Reavalie + "quanto tempo você passa no celular antes de dormir" = "Reavalie quanto tempo você passa no celular antes de dormir" ✓

FORMATO DE SAÍDA (JSON):
{{
    "tips": [
        "contato com pessoas que te fazem rir",
        "alongar o corpo ao acordar pela manhã",
        "pular refeições ou comer com pressa",
        "sinais de cansaço mental no meio do dia",
        "compromissos que não agregam valor real",
        "quanto tempo passa no celular antes de dormir"
    ]
}}

Gere as 6 complementos agora, garantindo que cada um seja uma continuação NATURAL E GRAMATICAL do seu respectivo título.
"""
    return prompt
