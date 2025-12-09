prompt_comparador_template = (
    "Compare os dois contextos a seguir, considerando que podem ser diferentes facetas ou perspectivas da mesma história. "
    "Mesmo que usem palavras diferentes, avalie se tratam essencialmente do mesmo tema ou situação central:\n"
    "Contexto 1: '{context1}'\n"
    "Contexto 2: '{context2}'\n"
    "Retorne um valor numérico de similaridade entre 0 e 1, onde 1 indica que são essencialmente o mesmo contexto (mesmo que descritos de formas diferentes), "
    "e 0 indica que não têm relação. "
    "Seja objetivo e considere o significado central dos contextos, não apenas as palavras. "
    "Retorne apenas o número decimal, sem explicações ou texto adicional."
)

role_comparador = (
    "Você é um especialista em análise semântica de textos em português. "
    "Sua tarefa é comparar dois contextos fornecidos, avaliando se, mesmo com palavras diferentes, tratam essencialmente do mesmo tema ou situação central. "
    "Considere diferentes facetas ou perspectivas da mesma história. "
    "Retorne apenas um número decimal entre 0 e 1, onde 1 indica contextos essencialmente iguais e 0 indica contextos sem relação. "
    "Não forneça explicações, comentários ou qualquer texto adicional — apenas o valor numérico. "
    "Seja rigoroso e objetivo, considerando o significado central dos contextos, não apenas as palavras."
)
