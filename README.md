# odoo-iso

Repositorio del despliegue Odoo de Amunet sobre el servidor FC
(`149.102.142.110`).

Contiene addons custom (`addons/`), parches puntuales (`corrections/`),
los Dockerfiles y compose files para prod y staging
(`docker-compose.production.yml`, `docker-compose.staging.yml`), y los
workflows de GitHub Actions que hacen deploy automático.

## Mapa branches → entornos

| Branch     | URL                              | Path en server          |
|------------|----------------------------------|--------------------------|
| `main`     | https://fc.amunet.com.mx         | `/opt/odoo/production`   |
| `staging`  | https://staging.fc.amunet.com.mx | `/opt/odoo/staging`      |

Otras branches no se deployan automáticamente.

## Deploy

`git push origin staging` deploya a staging. `git push origin main`
deploya a prod (pero el flujo recomendado es PR `staging → main`, no push
directo). Ver [`CONTRIBUTING.md`](CONTRIBUTING.md) y
[`.github/workflows/README.md`](.github/workflows/README.md).

## Operaciones comunes

- **Clonar prod → staging**: panel `https://portainer.fc.amunet.com.mx/tools`
  o GitHub Actions → "Clone Production DB to Staging".
- **Backup manual de prod**: mismo panel. Backup automático corre por cron
  diario a las 02:00 UTC, retención 7 días.
- **Ver logs de Odoo staging**: GitHub Actions → "Ver Logs de Odoo".

## Documentación operativa

- `CONTRIBUTING.md` — flujo para devs.
- `.github/workflows/README.md` — convención de branches y descripción de
  cada workflow.
- Documentación interna (no en repo): `ODOO_RUNBOOK_2026-05-04.md`.
