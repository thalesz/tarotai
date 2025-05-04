from openai import AzureOpenAI
import os
from dotenv import load_dotenv

class OpenAIService:
    def __init__(self):
        load_dotenv()
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_API_KEY"),
            api_version="2023-03-15-preview",
            azure_endpoint=os.getenv("AZURE_ENDPOINT")
        )

    async def gerar_texto(self, prompt_ajustado: str, role: str, max_tokens, temperature) -> str:
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Ou o nome do deployment no Azure, como "gpt-35-turbo"
                messages=[
                    {"role": "system", "content": role},
                    {"role": "user", "content": prompt_ajustado}
                ],
                max_tokens=max_tokens,  # Define o limite máximo de tokens (ou palavras/frases curtas) que o modelo pode gerar.
                                 # Neste caso, está configurado para 140 tokens, que é aproximadamente metade do limite de caracteres de um tweet (280 caracteres).
                                 # Isso ajuda a garantir que o texto gerado seja curto e conciso, adequado para tweets.

                temperature=temperature  # Controla a aleatoriedade do modelo na geração de texto.
                                 # Valores mais baixos (ex.: 0.2) tornam o texto mais determinístico e previsível.
                                 # Valores mais altos (ex.: 0.9) tornam o texto mais criativo e imprevisível.
                                 # Aqui, foi configurado para 0.9, incentivando respostas mais criativas.
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Erro ao gerar texto: {str(e)}"
