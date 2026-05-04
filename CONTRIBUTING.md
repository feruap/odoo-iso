# CONTRIBUTING — `feruap/odoo-iso`

Guía rápida para contribuir cambios al sistema Odoo desplegado en
`fc.amunet.com.mx` (prod) y `staging.fc.amunet.com.mx` (staging).

## Branches "oficiales"

| Branch    | Significado            | Deploy automático             |
|-----------|------------------------|-------------------------------|
| `main`    | Lo que está en prod    | https://fc.amunet.com.mx       |
| `staging` | Lo que está en staging | https://staging.fc.amunet.com.mx |

Cualquier otra branch es un **espacio de trabajo personal** y no deploya en
ningún lado. Usá nombres descriptivos: `feature/<lo-que-haces>`,
`fix/<bug>`, `chore/<tarea-de-limpieza>`.

## Flujo recomendado

```
1. git checkout staging && git pull
2. git checkout -b feature/mi-cambio
3. ... commits ...
4. git push origin feature/mi-cambio
5. (opcional) abrir PR feature/mi-cambio → staging para code review
6. mergear el PR (o git merge feature/mi-cambio en local + push staging)
7. push origin staging  → dispara deploy a staging.fc.amunet.com.mx
8. probar en staging con datos frescos (botón "Clonar prod→staging" si hace falta)
9. abrir PR staging → main
10. mergear el PR  → dispara deploy a fc.amunet.com.mx
```

**Nunca** push directo a `main`. **Nunca** merge a `main` sin haber pasado por
staging primero.

## Cosas que NO se hacen

- No edites archivos directamente en `/opt/odoo/production` o
  `/opt/odoo/staging` en el server. El próximo deploy los sobrescribe con
  `git reset --hard`.
- No commitees secrets (`.env`, llaves SSH, tokens, passwords). Si lo hacés
  por error, contactá al admin para rotarlos y rebasear/borrar el commit.
- No agregues branches al trigger de `deploy.yml`. La convención `main →
  prod, staging → staging, otras → nada` es deliberada (ver
  `.github/workflows/README.md`).
- No quites los `sleep` y retry loops del `deploy.yml`. Existen para evitar
  errores `SerializationFailure` de Postgres.

## Referencia rápida

- Convenciones detalladas: [`.github/workflows/README.md`](.github/workflows/README.md)
- Runbook operativo: documentación interna `ODOO_RUNBOOK_2026-05-04.md`
- Análisis del modelo: documentación interna `ODOO_STAGING_FLOW_2026-05-04.md`

## Problema TLS conocido

`staging.fc.amunet.com.mx` y `portainer.fc.amunet.com.mx` fallan en TLS
handshake desde el edge de Cloudflare (cert universal CF no cubre depth-2).
Acceso temporal: usar SSH al server o cambiar esos hosts a "DNS only" (gris)
en Cloudflare.
