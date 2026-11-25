<<<<<<< HEAD
# InnOpEx Governance Platform · GMSA

Plataforma de governança de projetos OpEx e Inovação da GMSA.
**Back-end em Python (FastAPI)** + **front-end com a identidade visual aprovada do mockup**.

> Versão 0.1.0 — dados de exemplo (`DATA_MODE=mock`) e login de desenvolvimento (`AUTH_MODE=dev`).
> A integração com Databricks / SharePoint / Entra ID já tem lugar reservado (ver `docs/INTEGRACAO.md`).

---

## 🧸 Como rodar no VS Code (Windows)

1. **Descompacte** o `.zip` em uma pasta fácil, por exemplo `C:\Users\SEU_ID\Documents\innopex-platform`.
2. No VS Code: **File → Open Folder…** e escolha a pasta `innopex-platform`.
3. Se aparecer *"Do you want to install the recommended extensions?"*, clique em **Install**.
4. Abra o terminal: **Ctrl + `** (crase).
5. Crie o ambiente virtual (uma caixinha só para as bibliotecas do projeto):
   ```powershell
   py -m venv .venv
   ```
6. Instale as bibliotecas **sem precisar ativar** o ambiente (isso evita o erro do `Activate.ps1`):
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   ```
7. Aperte **F5** e escolha **"InnOpEx: rodar a plataforma"**.
   O navegador abre sozinho em **http://127.0.0.1:8000**. 🎉
8. Para parar o servidor: **Shift + F5**.

Sem F5? Rode no terminal:
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

### Testes automáticos
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
Ou no VS Code: ícone do frasco 🧪 (Testing) → **Run All Tests**.

### Documentação da API
Com o servidor rodando, abra **http://127.0.0.1:8000/docs** — dá para testar cada rota clicando em *Try it out*.

---

## 🧱 Como o projeto está organizado

```
innopex-platform/
├── app/                      ← back-end Python
│   ├── main.py               ← liga tudo: rotas, erros, arquivos do site
│   ├── config.py             ← lê o .env (DATA_MODE, AUTH_MODE…)
│   ├── models.py             ← formato dos dados (Projeto, Reunião, Deck…)
│   ├── rules.py              ← regras de negócio puras (lucro no Measure, Master único, terças…)
│   ├── services.py           ← casos de uso (mover fase, Meeting Notes, reagendar…) + histórico + notificações
│   ├── auth.py               ← quem está logado (dev hoje, SSO Entra ID depois)
│   ├── nopex.py              ← respostas do Nopex
│   ├── api/                  ← rotas HTTP (/api/...)
│   └── repositories/         ← 🔌 a "tomada" de dados
│       ├── base.py           ← contrato que toda fonte de dados segue
│       ├── json_repo.py      ← HOJE: data/seed.json → data/state.json
│       └── databricks_repo.py← AMANHÃ: SQL Warehouse (catálogo innopex)
├── static/                   ← front-end (HTML, CSS do mockup, JS)
│   ├── index.html
│   ├── css/styles.css        ← CSS do mockup aprovado, sem alterações + adições no final
│   ├── js/api.js             ← único arquivo que conversa com o back-end
│   ├── js/app.js             ← telas
│   └── img/                  ← Nopex
├── data/seed.json            ← dados ILUSTRATIVOS
├── tests/                    ← testes automáticos (pytest)
├── docs/INTEGRACAO.md        ← passo a passo da integração futura
├── app.yaml                  ← publicação no Databricks Apps
└── .vscode/                  ← F5, testes e extensões prontos
```

**Regra de ouro:** as telas só falam com a API, a API só fala com `services.py`,
e `services.py` só fala com o *repository*. Por isso trocar os dados de exemplo
pelo Databricks é trocar **uma peça**, sem mexer nas telas.

---

## ✅ Regras de negócio já implementadas

| Regra | Onde |
|---|---|
| Lucro estimado obrigatório a partir do Measure | `rules.check_profit` |
| Um único Master por projeto | `rules.check_single_master` |
| Toda mudança grava autor e data | `services._log` |
| Toda ação gera notificação na central | `services.notify` |
| Alerta de material parado (30 dias, configurável) | `services.run_stale_check` |
| Meeting Notes + intervalo de retorno obrigatórios; propõe a próxima terça livre | `services.register_notes` |
| Aceitar / recusar com reagendamento automático | `services.accept_meeting` / `decline_meeting` |
| Capacidade máxima por terça (provisório: 4) | `Config.max_per_tuesday` |
| Deck em destaque na semana da reunião | `api/governance.decks` |
| Perfis Admin, Master, Leader, Viewer | `rules.PERMISSIONS` |
| Acesso só para `@gm.com` | `rules.is_email_allowed` |

## 🔁 Reiniciar os dados de exemplo
- Pela tela: link **"reiniciar demonstração"** no rodapé.
- Ou apague o arquivo `data/state.json` e reinicie o servidor.

## ⚠️ Limitações desta versão
- Dados ilustrativos; nada é gravado no SharePoint e nenhum e-mail é enviado.
- O upload de deck registra só o nome e a versão (o arquivo em si vai para a biblioteca do SharePoint na integração).
- Gráficos usam a biblioteca ECharts via internet (CDN). Sem internet, aparece um aviso no lugar.
=======
# innopex-platform
>>>>>>> d0e24984992ae85d1af58ea347907f5c4d1eed79
