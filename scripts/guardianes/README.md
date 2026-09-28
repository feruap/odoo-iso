# Guardianes

Los tres scripts que vigilan que no se pierda trabajo, mas el ayudante de correo
que usan para avisar.

| script | cuando corre | que vigila |
|---|---|---|
| `guardian_git_staging.sh` | 22:00 diario | archivos sin guardar, trabajo sin subir a GitHub, stashes abiertos, ramas sin integrar |
| `audit_modulos_sin_codigo.sh` | 07:30 diario | modulos instalados cuyo codigo ya no esta, y modulos que git no sigue |
| `chequeo_calidad.sh` | 07:30 diario | configuracion de Control de Calidad en produccion |
| `_send_mail.py` | — | lo usan los anteriores para mandar el aviso por correo |

## Por que viven aqui y no en ~/scripts

Hasta el 28-sep-2026 vivian solo en `~/scripts/`, fuera de todo repositorio: los
scripts que cuidan de que no se pierda codigo eran justo los que se podian
perder sin dejar rastro, y cualquiera los editaba en vivo sin que quedara
historia de que cambio ni por que.

Ahora viven en git y `~/scripts/<nombre>` es un **symlink** que apunta aqui. El
crontab sigue llamando a `~/scripts/...`, asi que no hubo que tocarlo.

## Como se editan

Se edita el archivo de esta carpeta y se commitea, como cualquier otro cambio.
El efecto es inmediato: el symlink ya apunta a este archivo, no hay que copiar
nada ni reiniciar nada.

## Lo que NO va aqui

`~/.smtp_creds` tiene las credenciales del correo y **se queda fuera de git**.
`_send_mail.py` solo las lee de ahi; no las trae dentro.

Los `.log` tambien se quedan en `~/scripts/` y `~/logs/`: son salida, no codigo.
