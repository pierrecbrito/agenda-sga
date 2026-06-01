# Agenda SGA

O Agenda SGA é um projeto voltado para a marcação de consultas em UBSs.

A proposta é organizar o fluxo de atendimento para reduzir superlotação nas unidades e permitir que o usuário acompanhe, de forma digital e ao vivo, a fila de espera e o andamento do atendimento.

O sistema centraliza o cadastro de cidadãos, UBSs, especialidades e agendamentos em um único monolito Django, facilitando a gestão da rede municipal de saúde.

## Estrutura

- `config/`: configuracao do projeto Django
- `apps/core/`: aplicacao principal com a pagina inicial

## Modelo de usuarios

- `Cidadao` concentra os dados cadastrais.
- `Endereco` fica separado para simplificar manutencao e evolucao.
- Administradores do sistema continuam sendo usuarios do Django com `is_staff` ou `is_superuser`, ligados a um `Cidadao` quando necessario.

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
