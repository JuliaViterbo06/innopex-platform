# Integração futura — o que muda e onde

Tudo foi separado para que cada integração seja **uma peça trocada**, sem mexer nas telas.

## 1. Dados oficiais (Databricks, catálogo `innopex`)
1. Pipeline já aprovado: SharePoint (OpEx Global `Projects` + GMSA `Growth Project`) → Microsoft Graph → `innopex.bronze` → `silver` → `gold`.
2. Implementar `app/repositories/databricks_repo.py`, devolvendo os **mesmos modelos** de `app/models.py`.
3. `pip install databricks-sql-connector databricks-sdk` e adicionar em `requirements.txt`.
4. No `.env` (ou `app.yaml`): `DATA_MODE=databricks`, `DATABRICKS_HOST`, `DATABRICKS_WAREHOUSE_ID`.

Mapeamento aprovado (para a camada gold):
| Campo da plataforma | Origem |
|---|---|
| `type` | inferido da lista: Projects = Opex · Growth Project = Inovação |
| `master` | OpEx Master (global) / InnOpEx Master (local) — responsável único |
| `value_musd` | Blue Value + Project 3 Year Value |
| `green_musd` | Green Value (campo separado) |
| `phase` | datas ECD por fase (global) / Current Phase traduzido (local) |

## 2. Login corporativo (Microsoft Entra ID)
- No Databricks Apps o SSO já vem pronto: o app recebe o cabeçalho `X-Forwarded-Email`.
- Basta `AUTH_MODE=databricks` (já configurado no `app.yaml`). O código está em `app/auth.py`.
- O perfil (Admin/Master/Leader/Viewer) vem de `repo.find_user(email)`; quem não estiver cadastrado entra como Viewer.

## 3. E-mails das notificações
- Ponto único: `services.notify()`. Acrescentar ali o envio (ex.: Power Automate / Microsoft Graph), mantendo a central de notificações.

## 4. Escrita de volta no SharePoint
- Ponto único: `DatabricksRepository.save_project()` (ou um serviço de sincronização).
- **Depende de autorização** — decisão pendente.

## 5. Automações agendadas
- `services.run_stale_check()` hoje roda quando o servidor sobe. Em produção vira um job diário no Databricks.
- Fila de terça e destaque de decks já são calculados pela API.

## Decisões pendentes (bloqueiam a versão final)
- Autorização de escrita no OpEx Global
- Máximo de projetos por terça
- Critério oficial de filtro GMSA na lista global
- Quem aprova reclassificação Opex ↔ Inovação
- Quem administra prazos e perfis
