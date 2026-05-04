# Workflows de GitHub Actions — `feruap/odoo-iso`

Este directorio contiene los workflows que automatizan el deploy de Odoo en el
servidor `149.102.142.110` (FC). Lo que sigue describe **cómo deben usarse** y
**qué garantías ofrecen**. Los workflows están diseñados alrededor de una
**convención estricta de branches**: si la rompes, no se deploya nada.

## Convención de branches → entornos

| Branch                                    | Push dispara                | URL pública                   | Path en server          |
|-------------------------------------------|-----------------------------|-------------------------------|--------------------------|
| `main`                                    | Deploy a **producción**     | https://fc.amunet.com.mx      | `/opt/odoo/production`   |
| `staging`                                 | Deploy a **staging**        | https://staging.fc.amunet.com.mx | `/opt/odoo/staging`   |
| Cualquier otra (`feature/*`, `fix-*`, etc.) | **Nada** (no se deploya)  | —                             | —                        |

Esto está enforced en `deploy.yml`:

```yaml
on:
  push:
    branches:
      - main
      - staging
```

y en cada job:

```yaml
if: github.ref == 'refs/heads/main'      # job deploy-production
if: github.ref == 'refs/heads/staging'   # job deploy-staging
```

**No agregues otras branches a este trigger.** El modelo es de un solo carril
(1 staging compartido); si se necesita testing paralelo en el futuro, eso
implica cambiar de modelo (ver sección "Limitaciones" abajo) — no agregar
branches al workflow.

## Flujo del día a día (para devs)

### 1. "Quiero probar un cambio antes de prod"

```bash
git checkout staging
git pull origin staging
git checkout -b feature/mi-cambio          # opcional pero recomendado
# ... hacer cambios, commits ...
git checkout staging
git merge feature/mi-cambio
git push origin staging                    # ⚡ esto dispara el deploy a staging
```

A los ~3-8 min `https://staging.fc.amunet.com.mx` tendrá el código nuevo.

### 2. "El cambio funciona en staging, lo paso a prod"

Abrí un Pull Request `staging → main` desde GitHub UI. Cuando se mergea (squash
o merge commit, da igual), el push a `main` dispara `deploy-production`.

```
staging  ─────PR─────►  main  ─────GH Actions─────►  fc.amunet.com.mx
```

### 3. "Necesito staging con datos frescos de prod"

No es un git push — es un click en el panel admin-tools:

- URL: `https://portainer.fc.amunet.com.mx/tools?token=<ADMIN_TOKEN>`
- Botón "🔄 Clonar Producción → Staging"
- O alternativamente: `Actions → Clone Production DB to Staging → Run workflow`

Ese script:
1. Detiene `odoo-staging`.
2. `pg_dump` de `odoo_production` y restaura como `odoo_staging`.
3. Copia el filestore de prod al volumen de staging.
4. Levanta `odoo-staging`.

Tiempo: ~30s a 2 min según tamaño.

### 4. "Necesito un backup de prod"

- Auto: cron diario 02:00 UTC en `/opt/odoo/backups/db_<ts>.sql.gz` y
  `filestore_<ts>.tar.gz`. Retención 7 días.
- Manual: botón "💾 Backup Manual" en el mismo panel.

### 5. "El deploy falló"

- `https://github.com/feruap/odoo-iso/actions` → ver logs del run.
- Alternativa: `Actions → Ver Logs de Odoo → Run workflow` trae los últimos
  300 renglones del log de Odoo staging y lista las DBs.
- Tail directo desde el server (si tenés acceso SSH):
  `ssh agentia-odoo@149.102.142.110 'docker logs odoo-staging --tail 300'`

## Reglas estrictas

1. **No editar prod a mano.** Todo cambio de código a prod debe pasar por
   `main`. Si algo se edita manual en `/opt/odoo/production`, el próximo deploy
   lo sobrescribe (el script hace `git reset --hard origin/main`).
2. **No push directo a `main`.** Siempre vía PR desde `staging`.
3. **`main` es sagrado.** Nada va a `main` sin haber pasado por staging
   primero (probado con datos clonados de prod, idealmente).
4. **`staging` puede romperse.** Es disposable: se puede clonar de prod cuando
   sea necesario para volver a un estado limpio.
5. **Dos devs no deben pushear a `staging` simultáneamente** sin coordinarse.
   Solo hay 1 staging compartido — el último push gana.
6. **Cualquier cambio de schema** (migrations Odoo, módulos nuevos, cambios de
   dependencias) **debe probarse en staging con clone fresco de prod**, no con
   los datos viejos que arrastra staging.

## Workflows existentes

### `deploy.yml` — Deploy Odoo

Trigger: `push` a `main` o `staging`. Hace `git reset --hard`, rebuilda imagen
Docker (con `--no-cache`), recrea contenedor, espera healthcheck, y corre
`odoo -u all` (prod) o `odoo -i amunet_production` (staging).

⚠️ **Importante**: el workflow contiene retry loops con `sleep` para evitar
errores `SerializationFailure` de Postgres durante el startup. **No los
quites.** Hay un comentario explícito al inicio del archivo.

⚠️ **Auth git**: usa `GITHUB_TOKEN` desde `/opt/odoo/.env` en el server (no
llaves SSH). Si cambias el repo o rotás el token, actualizá ese archivo.

### `clone-db.yml` — Clone Production DB to Staging

Trigger: `workflow_dispatch` (manual). Equivalente al botón del panel
admin-tools, pero desde GitHub.

### `get-logs.yml` — Ver Logs de Odoo

Trigger: `workflow_dispatch` (manual). Trae 300 renglones de log y lista las
DBs de prod y staging.

## Secrets requeridos en GitHub

Configurados en `Settings → Secrets and variables → Actions → Repository
secrets`:

- `SSH_HOST` — IP/hostname del server (`149.102.142.110`).
- `SSH_USER` — usuario SSH (`root` actualmente).
- `SSH_PRIVATE_KEY` — llave privada del usuario SSH.

No commitear estos valores ni en este README ni en archivos del repo.

## Limitaciones del modelo actual ("Camino A")

Este sistema es **un solo carril**: una sola staging compartida.

- No se puede probar 2+ features en aislamiento al mismo tiempo. Si dos devs
  pushean a `staging` cerca en el tiempo, gana el último.
- No hay entornos efímeros por PR (no es Odoo.sh real).
- Si el equipo Odoo crece a 3+ devs y necesitás testing paralelo, hay que
  evaluar migrar a "staging-per-branch" (Camino B) — ver
  `ODOO_STAGING_FLOW_2026-05-04.md` en la documentación interna.

## Problema TLS conocido

`staging.fc.amunet.com.mx` y `portainer.fc.amunet.com.mx` actualmente fallan
en handshake TLS desde el edge de Cloudflare (depth-2 certs no cubiertos por
el universal CF cert). Workarounds documentados en `ODOO_RUNBOOK_*.md`.

Mientras tanto, para acceder a esos hosts en el browser:
- O conectarse al server por SSH (`ssh agentia-odoo@149.102.142.110`) y usar
  `curl` localmente.
- O cambiar esos subdominios a "DNS only" (gris) en Cloudflare.
