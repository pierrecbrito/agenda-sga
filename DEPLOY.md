# Guia de Deploy Automatizado — Agenda SGA

Este guia descreve como realizar o deploy **totalmente automatizado (1-click)** da aplicação **Agenda SGA** no **Render** utilizando a infraestrutura como código (IaC) com o arquivo `render.yaml` já configurado na raiz do projeto.

A automação irá:
1. Provisionar um banco de dados **PostgreSQL** de forma automática.
2. Criar o **Web Service** Python para rodar a aplicação.
3. Vincular de forma automática as chaves e credenciais do banco ao Web Service.
4. Gerar chaves aleatórias seguras para a `SECRET_KEY` do Django.
5. Executar as migrações de banco automaticamente a cada novo commit de código (`preDeployCommand`).
6. Servir todos os ativos estáticos de forma otimizada com compressão e cache-busting (`WhiteNoise`).

---

## 📋 Pré-requisitos
1. Uma conta no [Render](https://render.com/).
2. O código do projeto hospedado em um repositório no **GitHub** ou **GitLab**.

---

## 🚀 Passo 1: Executar o Deploy Automatizado (Render Blueprints)

1. Faça login no painel do [Render](https://render.com/).
2. No menu superior, clique em **Blueprints** e depois em **New Blueprint Instance** (Nova instância Blueprint).
3. Conecte sua conta do GitHub/GitLab e selecione o repositório do **agenda-sga**.
4. O Render detectará automaticamente o arquivo `render.yaml` na raiz do seu projeto.
5. Preencha as informações solicitadas:
   - **Service Group Name:** `agenda-sga-stack` (nome do grupo de recursos).
6. Clique em **Apply** (Aplicar).

**Pronto!** O Render começará a provisionar o banco de dados PostgreSQL e compilar sua aplicação Python automaticamente.

---

## 🔑 Passo 2: Executar Comandos Iniciais (Superusuário)

Após o deploy automatizado ser concluído com sucesso e o site estar online:
1. No painel do Render, vá em **Web Services** e clique em `agenda-sga`.
2. Clique na opção **Shell** no menu lateral esquerdo.
3. Execute o comando de criação do primeiro superusuário administrativo:
   ```bash
   python manage.py createsuperuser
   ```
4. Siga as instruções inserindo CPF, E-mail e Senha.

---

## 🔄 Como funciona a Atualização Contínua?
Sempre que você realizar um `git push` de novas alterações na sua branch principal (`master`/`main`):
1. O Render puxará o novo código automaticamente.
2. Instalará as novas dependências e compilará os arquivos estáticos.
3. Executará automaticamente o comando `python manage.py migrate` para atualizar o banco de dados (graças à diretiva `preDeployCommand` configurada).
4. Fará a substituição do servidor antigo pelo novo com **zero tempo de inatividade** (zero-downtime).

---

## 🛠️ Detalhes da Arquitetura do Deploy
* **Gunicorn:** Servidor WSGI robusto de nível de produção que gerencia as requisições em paralelo.
* **WhiteNoise:** Habilitado em `settings.py` para servir arquivos CSS, JS e imagens compactados e cacheados diretamente pelo processo do Django, sem precisar de um servidor Nginx separado.
* **Logging:** Todos os erros críticos (`ERROR`) gerados na aplicação são salvos automaticamente no arquivo `django_errors.log` e exibidos nas abas de console/logs do painel do Render em tempo real.

