# Agenda SGA

Monolito Django inicial para o sistema Agenda SGA.

## Estrutura

- `config/`: configuracao do projeto Django
- `apps/core/`: aplicacao principal com a pagina inicial

## Como executar

1. Crie e ative um ambiente virtual.
2. Instale as dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode as migracoes:
   ```bash
   python manage.py migrate
   ```
4. Inicie o servidor:
   ```bash
   python manage.py runserver
   ```
