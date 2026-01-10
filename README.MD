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

.\script-build-push.ps1 -EnvFile .\.env -PostgresUrl "postgresql+asyncpg://citus:postgres1!@c-tarot.oxdkcydnlxxclq.postgres.cosmos.azure.com:5432/citus"

### Configuração de CORS

Defina as origens permitidas via variável de ambiente para uso em desenvolvimento e produção.

- Exemplo (PowerShell - múltiplas origens):
        ```powershell
        $env:CORS_ORIGINS="http://localhost:5173,https://purple-island-07cb6510f.6.azurestaticapps.net"
        uvicorn app.main:app --reload
        ```

- Exemplo (Azure App Service - App Settings):
    - `CORS_ORIGINS` = `https://purple-island-07cb6510f.6.azurestaticapps.net`
    - Opcional: `FRONTEND_URL` = `https://purple-island-07cb6510f.6.azurestaticapps.net`

## Estrutura do Projeto

- `app/`: Contém o código principal da aplicação.
- `requirements.txt`: Lista de dependências do projeto.

