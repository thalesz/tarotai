import json
import re
import ast


class JsonExtractor:
    @staticmethod
    def extract_json_from_reading(reading):
        """Tenta extrair um dicionário Python/JSON a partir de diferentes formatos que a resposta da IA pode retornar.

        Estratégia:
        - Se já for dict, retorna direto.
        - Procura um bloco ```json ... ``` e tenta json.loads.
        - Procura o primeiro objeto JSON {...} na string e tenta json.loads.
        - Tenta ast.literal_eval como fallback (aceita aspas simples).
        - Como último recurso tenta substituir aspas simples por duplas e json.loads.
        - Se nada funcionar, retorna None.
        """
        if isinstance(reading, dict):
            return reading

        if not isinstance(reading, str):
            return None

        # 1) bloco ```json ... ```
        try:
            regex = r'```json\s*([\s\S]*?)\s*```'
            match = re.search(regex, reading)
            if match and match.group(1):
                try:
                    return json.loads(match.group(1))
                except Exception:
                    pass

            # 2) primeiro objeto JSON {...}
            match2 = re.search(r'(\{[\s\S]*\})', reading)
            if match2:
                candidate = match2.group(1)
                try:
                    return json.loads(candidate)
                except Exception:
                    # tentar ast
                    try:
                        return ast.literal_eval(candidate)
                    except Exception:
                        pass

            # 3) tentar interpretar toda a string com json
            try:
                return json.loads(reading)
            except Exception:
                pass

            # 4) ast literal eval em toda a string
            try:
                return ast.literal_eval(reading)
            except Exception:
                pass

            # 5) substituir aspas simples por duplas e tentar json
            try:
                fixed = reading.replace("\"\"\"", '"')
                fixed = fixed.replace("'", '"')
                return json.loads(fixed)
            except Exception:
                pass
        except Exception as e:
            print("JsonExtractor unexpected error:", e)

        return None
