# app/services/descricao_astrologica.py

from app.services.openai import OpenAIService
from app.services.extract import JsonExtractor
from app.services.planet import PlanetSignCalculator
from app.schemas.personal_sign import PersonalSignSchema
from app.schemas.zodiac import ZodiacSchemaBase

class DescricaoAstrologicaService:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.role = (
            "Você é um astrólogo especialista em mapa astral. "
            "Seu papel é analisar data, hora e local de nascimento e retornar o signo de um planeta específico.\n\n"
            "Retorne a resposta OBRIGATORIAMENTE dentro de um bloco de código markdown com a linguagem 'json', assim:\n"
            "```json\n"
            "{\n"
            "  \"planet_sign\": {\"nome\": \"Capricórnio\", \"descricao\": \"...\"}\n"
            "}\n"
            "```\n"
            "⚠️ Não altere a estrutura. A descrição deve ser clara, concisa e curta."
        )

    async def gerar_e_salvar_descricao(
        self,
        db, user_id: int, birth_date: str, birth_time: str, birth_place: str,
        planet_id: int, planet_name: str, acesso_premium: bool, max_tokens: int, signo: str, grau: str 
    ):
        # planet_sign_calculator = PlanetSignCalculator()
        # signo, grau = await planet_sign_calculator.planet_sign(
        #     birth_date,
        #     birth_time,
        #     birth_place,
        #     planet_name.upper()
        # )

        tokens_para_usar = max_tokens if acesso_premium else 60

        prompt = (
            f"Considere os dados de nascimento abaixo:\n"
            f"- Data: {birth_date}\n"
            f"- Hora local: {birth_time}\n"
            f"- Local: {birth_place}\n\n"
            f"O planeta {planet_name} está no signo de {signo} (grau {grau}).\n"
            f"Forneça uma interpretação astrológica profissional.\n\n"
            f"⚠️ Responda apenas com um JSON válido:\n"
            f"{{\n"
            f"  \"planet_sign\": {{\n"
            f"    \"nome\": \"{signo}\",\n"
            f"    \"descricao\": \"...\"\n"
            f"  }}\n"
            f"}}"
        )

        if not acesso_premium:
            prompt += "\n⚠️ A descrição deve ser uma prévia no máximo 10 palavras com 'Assine o pacote premium para saber mais...'."

        leitura = await self.openai_service.gerar_texto(
            prompt_ajustado=prompt,
            role=self.role,
            max_tokens=tokens_para_usar,
            temperature=0.9
        )

        json_data = JsonExtractor.extract_json_from_reading(leitura)

        if not json_data or "planet_sign" not in json_data:
            raise ValueError(f"Erro ao extrair JSON da leitura para o planeta {planet_name}.")

        planet_sign = json_data["planet_sign"]
        nome = planet_sign.get("nome", "")
        descricao = planet_sign.get("descricao", "")

        id_zodiac = await ZodiacSchemaBase.get_zodiac_id_by_name(db, nome)
        await PersonalSignSchema.create_or_update(db, user_id, planet_id, id_zodiac, descricao, f"{grau}°")

        return {
            "planet": planet_name,
            "signo": nome,
            "descricao": descricao,
            "grau": grau,
        }
