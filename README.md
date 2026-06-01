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
- O sistema trabalha com tres perfis de acesso:
   - `Super admins`: acesso total ao sistema, sem restricoes de visualizacao ou edicao.
   - `Admins de UBS`: acesso limitado a uma ou mais UBSs vinculadas ao usuario, podendo gerenciar apenas os dados e agendamentos dessas unidades.
   - `Cidadaos`: usuarios comuns com acesso aos proprios dados e as solicitacoes de agendamento.
- Para representar admins de UBS, existe o vínculo `UbsAdmin`, que relaciona um usuario a uma ou mais UBSs.

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
