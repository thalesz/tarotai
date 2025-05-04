# Tarot Project

Este é um projeto de API que realiza leituras de tarot utilizando inteligência artificial, implementado com os serviços da Azure.

## Pré-requisitos

Certifique-se de ter os seguintes itens instalados em sua máquina:
- Python 3.8 ou superior
- Pip (gerenciador de pacotes do Python)

## Como usar

1. Clone o repositório:
    ```bash
    git clone https://github.com/thalesz/tarotai.git
    cd tarot-project
    ```

2. Crie e ative o ambiente virtual (venv):
    ```bash
    python -m venv venv
    venv\Scripts\activate  # No Windows
    source venv/bin/activate  # No Linux/Mac
    ```

3. Instale as dependências do projeto:
    ```bash
    pip install -r requirements.txt
    ```

4. Inicie o servidor utilizando o Uvicorn:
    ```bash
    uvicorn app.main:app --reload
    ```

5. Acesse a aplicação no navegador:
    ```
    http://localhost:8000/
    ```

## Estrutura do Projeto

- `app/`: Contém o código principal da aplicação.
- `requirements.txt`: Lista de dependências do projeto.

