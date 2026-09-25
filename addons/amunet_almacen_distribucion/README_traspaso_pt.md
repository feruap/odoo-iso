# Traspaso de Producto Terminado a Distribucion

Desplegado a produccion el 21-sep-2026 (PR #77, commit 9d9d4989 sobre main).

## Que hace

Cada ingreso al anaquel `APT/Existencias_Presentacion 1 pieza` genera una
solicitud de traspaso, **una por lote**. Luis la autoriza (el material pasa a
`ADT/Stock` y queda vendible) o la rechaza (pasa a `APT/Rechazo`) escribiendo
el motivo, que es obligatorio y de al menos 10 caracteres.

Menu: Distribucion -> Operaciones -> Traspasos de Producto Terminado

## Donde tocar si algo no cuadra

Todo se configura en Ajustes -> Tecnico -> Parametros del sistema. **No hay
ids de ubicacion escritos en el codigo**, porque ADT/Stock es el 73 en staging
y el 66 en produccion.

| Parametro | Produccion | Staging | Que es |
|---|---|---|---|
| `amunet.distribucion.location_pt` | 14 | 14 | Anaquel que dispara la solicitud |
| `amunet.distribucion.location_adt` | 66 | 73 | Destino si se autoriza |
| `amunet.distribucion.location_rechazo` | 55 | 55 | Destino si se rechaza |
| `amunet.distribucion.picking_type_pt` | 15 | 15 | Tipo de operacion del traslado |
| `amunet.distribucion.responsable_uid` | 83 (Luis) | 83 | A quien avisa el cron |
| `amunet.distribucion.dias_aviso` | 3 | 3 | Dias antes de avisar |

**Ojo**: un parametro cambiado por consola no lo ven los procesos web hasta el
reinicio. Cambiarlo por la interfaz, no por `odoo shell`.

## Como apagarlo sin desinstalar nada

Poner `amunet.distribucion.location_pt` en `0`. El disparador deja de actuar
porque esa ubicacion no existe, y nada mas se rompe: las solicitudes ya
creadas siguen ahi y se pueden resolver.

## Cosas que conviene saber

- **Dispara con todo ingreso al anaquel**, incluidos los ajustes de inventario
  y las devoluciones de cliente. Hoy es por ahi por donde entra casi todo
  (234 de 267 movimientos del ultimo mes), no por produccion.
- **La produccion NO cae en el anaquel** sino en `APT/Almacen Temporal PT`. La
  solicitud nace despues, cuando el material llega al anaquel: ya descontado
  lo de Calidad y el museo de retencion.
- **No toca lo que ya estaba**. Las 961 pz que estaban en el anaquel al momento
  del despliegue no generaron solicitud; esas las revisa Luis aparte.
- Una devolucion desde ADT hacia el anaquel vuelve a generar solicitud. Es
  correcto, pero sorprende la primera vez.

## Respaldo previo al despliegue

`/opt/odoo/backups/db_20260921_124045_pre-traspaso-distribucion_amunet_prod.sql.gz`

## Como se valido

`-u` sobre un clon del dump de produccion, con los addons de produccion mas
este modulo. Se comprobo que un movimiento de materia prima no genera
solicitud ni falla, que un ingreso al anaquel si la genera, y que autorizar
mueve el lote a ADT.
