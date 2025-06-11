import asyncio
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
        tentativas = 0
        max_tentativas = 5

        while tentativas < max_tentativas:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": role},
                        {"role": "user", "content": prompt_ajustado}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                tentativas += 1
                print(f"[Tentativa {tentativas}] Erro ao gerar texto: {e}")
                if tentativas < max_tentativas:
                    await asyncio.sleep(2 ** (tentativas - 1))  # 1s, 2s, 4s, 8s...
                else:
                    return f"Erro após {max_tentativas} tentativas: {str(e)}"
