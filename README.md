# 🏥 Agenda SGA — Sistema Municipal de Gestão de Saúde e Fila de Atendimento

O **Agenda SGA** é um sistema completo e de nível profissional desenvolvido para a marcação de consultas em Unidades Básicas de Saúde (UBSs), controle de filas de atendimento em tempo real e auditoria geral de processos.

O objetivo principal do sistema é reduzir as filas presenciais e a superlotação nas unidades, permitindo que os gestores controlem a chamada de pacientes via painéis de TV de alta visibilidade e que os cidadãos acompanhem sua posição na fila e a estimativa de atendimento diretamente de seus celulares.

---

## 🎯 Objetivo do Projeto
Centralizar e organizar o fluxo de agendamento de consultas médicas em uma rede municipal de saúde, fornecendo transparência aos cidadãos e ferramentas de controle eficientes para os administradores das unidades de saúde.

---

## 🛠️ Tecnologias Utilizadas

* **Backend:** Python 3.13 e Django 5.2 (Monolito robusto com padrão MTV).
* **Banco de Dados:** PostgreSQL (Produção) e SQLite3 (Desenvolvimento local).
* **Servidor de Produção:** Gunicorn (servidor WSGI).
* **Gestão de Estáticos:** WhiteNoise (compressão e cache-busting).
* **Segurança e Variáveis:** python-dotenv (gestão de ambiente via `.env`).
* **Frontend:** HTML5 semântico, JavaScript nativo (ES6) e Vanilla CSS com padrão glassmorphism e design responsivo.
* **Autenticação:** Baseada em CPF com validador matemático (dígitos verificadores via módulo 11).

---

## 🔑 Perfis de Acesso & Permissões (RBAC)

O sistema trabalha com três perfis de acesso bem definidos, controlados dinamicamente via permissões e cache de sessão:

1. **Super Administrador (`super_admin`):**
   - Acesso irrestrito a todas as UBSs, logs de auditoria e relatórios de sistema.
   - Permissão exclusiva para cadastrar, editar e excluir UBSs.
   - Cadastro de administradores e gerenciamento geral de usuários.

2. **Administrador de UBS (`ubs_admin`):**
   - Vinculado a uma ou mais unidades específicas através da tabela `UbsAdmin`.
   - Gerencia a fila de chamadas, especialidades e agendamentos **apenas** nas unidades às quais está associado.
   - Visualiza a lista de cidadãos cadastrados no sistema.

3. **Cidadão (`cidadao`):**
   - Acesso exclusivo a agendar suas próprias consultas (apenas em UBSs com agendamento online ativo).
   - Visualização e cancelamento de seus próprios agendamentos.
   - Acompanhamento da sua posição em tempo real na fila no dia da consulta.

---

## 📋 Regras de Negócio Chave

* **Unicidade de CPF:** Cada cidadão é unicamente identificado pelo CPF, validado matematicamente no cadastro.
* **Double Booking:** Uma vaga de agendamento específica (UBS + Especialidade + Data + Horário) não pode receber múltiplos cidadãos (`UniqueConstraint` a nível de banco).
* **Agendamento no Passado:** Não é permitida a criação de agendamentos com data ou hora no passado.
* **Antecedência Máxima:** O cidadão só pode agendar consultas respeitando o limite de `antecedencia_maxima_dias` definido individualmente por cada UBS.
* **Compromisso de Presença:** O cidadão deve comparecer à unidade 20 minutos antes do horário agendado.
* **Estimativa de Fila:** A estimativa de espera para o cidadão é calculada somando a duração real (fim - início) configurada de cada vaga de consulta confirmada à sua frente na fila daquela especialidade.

---

## 📺 Recursos de Fila de Chamada em Tempo Real

1. **Painel de Controle do Admin (`/agendamentos/fila/`):**
   - Tela para chamar o próximo paciente, rechamar (repetir alerta), registrar falta (status `FALTA`) e concluir o atendimento (status `EXECUTADO`).
   - A chamada de um novo paciente conclui automaticamente o anterior da mesma especialidade.

2. **Painel de TV de Sala de Espera (`/agendamentos/fila/painel/<ubs_id>/`):**
   - Interface de alta visibilidade ideal para TVs/monitores na sala de espera.
   - Exibe a senha, nome e especialidade do chamado atual em destaque, e o histórico dos últimos 5 chamados na lateral.
   - **Som e Voz Sintetizada:** Emite um gongo sonoro (gerado via *Web Audio API*) e dita o nome do paciente via sintetizador de voz nativo do navegador (*SpeechSynthesis*).
   - Possui overlay de desbloqueio para cumprir as políticas de autoplay de áudio.

3. **Painel de Acompanhamento do Cidadão (`/agendamentos/fila/acompanhar/`):**
   - Página em tempo real que mostra a senha do cidadão, posição exata na fila, quantas pessoas estão na frente, estimativa de minutos restantes e hora limite recomendada para comparecimento.
   - Alerta interativo visual piscante caso sua senha seja chamada no painel da unidade.

---

## 📁 Organização do Projeto

```text
agenda-sga/
│
├── apps/
│   ├── core/           # Cadastro de cidadãos, endereços, perfis e autenticação por CPF.
│   ├── ubs/            # Cadastro de UBSs, especialidades médicas e endereços das unidades.
│   ├── agendamentos/   # Agendamento de vagas, geração de senhas e painéis de filas (controle, TV e cidadão).
│   └── logs/           # Middleware de auditoria e geração de relatórios de logs de sistema.
│
├── config/             # Configurações globais do Django (settings, urls, wsgi).
├── static/             # Ativos estáticos globais (CSS, JS, Imagens).
├── templates/          # Templates HTML globais e de erros (404, 500).
├── requirements.txt    # Dependências do projeto.
├── render.yaml         # Blueprint de deploy automatizado no Render.
└── DEPLOY.md           # Guia de implantação detalhado.
```

---

## ⚙️ Execução Local

### 1. Clonar o repositório e preparar o ambiente
```bash
git clone https://github.com/seu-usuario/agenda-sga.git
cd agenda-sga
python -m venv .venv
```

No Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```
No Linux/macOS:
```bash
source .venv/bin/activate
```

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis locais (Opcional)
Crie um arquivo `.env` na raiz do projeto:
```env
DEBUG=True
SECRET_KEY=sua-chave-secreta-local
```
*(Se as variáveis do banco não forem fornecidas, o sistema usará automaticamente o SQLite3 local).*

### 4. Executar Migrações e Servidor
```bash
python manage.py migrate
python manage.py runserver
```
Acesse o sistema localmente em `http://127.0.0.1:8000/`.

---

## 🧪 Testes Automatizados
Para executar a suíte de testes unitários do Django:
```bash
python manage.py test
```

---

## 🚀 Deploy Automatizado no Render (1-click)
O repositório já inclui suporte para infraestrutura como código (IaC) com o Render Blueprints.
1. No painel do Render, vá em **Blueprints**.
2. Clique em **New Blueprint Instance** e conecte este repositório.
3. Clique em **Apply** e o Render provisionará o banco PostgreSQL, o Web Service, gerará a chave secreta e aplicará as migrações automaticamente a cada deploy.
4. Para mais informações detalhadas sobre o deploy, consulte o [DEPLOY.md](file:///c:/Users/Pierre%20Brito/Documents/dev/agenda-sga/DEPLOY.md).
