# Amunet - Consulta y planeación WooCommerce ↔ Odoo

Aplicación Odoo 19 de **consulta, validación y planeación** entre WooCommerce y
Odoo. Es una transformación completa del antiguo conector: ya **no publica
inventario** hacia la tienda.

## Reglas de la aplicación

- **Solo lectura hacia WooCommerce**: el backend REST únicamente hace llamadas
  `GET` (prueba de conexión y lectura de catálogo), con timeout, paginación
  acotada (máx. 50 páginas), validación TLS y bitácora sin secretos. No existe
  ningún `POST`/`PUT`/`PATCH`/`DELETE`, cron de publicación ni escritura de
  `stock_quantity`.
- **No modifica Odoo operativo**: nunca escribe `stock.quant`, lotes, órdenes
  MRP, controles de calidad, BOM ni presentaciones. Solo lee. Lo único editable
  es la configuración propia del módulo, los snapshots y la confirmación de
  mapeos.
- **"Dato ausente" nunca es cero**: cada cálculo trae su bandera
  `*_calculable` y un texto de razón. Cuando falta BOM, unidad, ubicación,
  equivalencia, liberación o snapshot se muestra **"No calculable"**. Si todo
  está configurado y el inventario real es insuficiente, cero sí es un
  resultado válido.
- **Trazabilidad**: mapeos, tiendas, snapshots y perfiles usan `mail.thread`;
  la revisión guarda revisor, fecha, estado y notas.
- **Multiempresa**: todos los modelos operativos tienen `company_id` y reglas
  de registro por compañía.

## Grupos

- **WooCommerce / Consulta**: solo lectura de toda la aplicación.
- **WooCommerce / Revisor**: edita la relación del mapeo (estado, confianza,
  método, notas, clasificación de abastecimiento). Un guard en `write()` le
  impide tocar cualquier otro campo, y las ACL le impiden editar backend,
  logs, snapshots y perfiles de proceso largo.
- **WooCommerce / Administrador**: tiendas y credenciales (visibles solo para
  este grupo, con `password="True"`), importación CSV, lectura GET del
  catálogo, carga de snapshots y perfiles de proceso largo.

La bitácora (`amunet.woo.sync.log`) es **inmutable**: se crea con su estado
final y nadie (ni el administrador) puede editarla o borrarla vía ACL.

## Pantalla de consulta (mapeo)

Menú raíz propio *WooCommerce Consulta* con vistas kanban (comparación visual
de las fotografías Woo y Odoo, sin JavaScript), lista y formulario. En la
ficha se ve: producto Woo (ID, SKU, nombre, URL de foto, estado, fecha del
último snapshot), producto Odoo, estado de la relación
(pendiente/confirmada/rechazada con confianza, método, notas, revisor y
fecha), clasificación de abastecimiento, inventario Woo por estado
(disponible/reservado/caducado/dañado, solo desde snapshot conocido),
inventario físico Odoo (interno, libre, en lotes liberados/pendientes),
configuración de calidad (`qc_required`, parámetros, controles), órdenes MRP
abiertas con acción para abrirlas, todas las presentaciones/piezas por caja
autorizadas en `amunet.packaging.presentation`, capacidad de fabricación
corta, perfil de fabricación larga y alertas legibles.

Filtros: pendientes, confirmados, rechazados, no calculables, con alertas,
fabricados, comprados y snapshot vencido. La antigüedad del snapshot se
configura con el parámetro `amunet_woocommerce.snapshot_max_age_days`
(por defecto 7 días).

## Importación CSV (idempotente)

*Configuración → Importar mapeo CSV*. Columnas:
`woo_id,woo_sku,titulo,piezas,odoo_default_code,odoo_track,odoo_use_exp,confianza,metodo,justificacion`.
Busca el producto Odoo por `default_code` exacto (nunca inventa
coincidencias). Cuando no hay una única coincidencia conserva el artículo Woo
como vínculo pendiente sin producto Odoo. La columna `piezas` es inventario
disponible observado, no piezas por caja. Actualiza por tienda + ID Woo;
reimportar la misma fecha de observación no duplica snapshots y una fecha
nueva conserva el histórico. Una importación automática nunca reemplaza un
vínculo ya revisado por una persona.

## Proceso largo por hoja maestra

Modelo auditable `amunet.woo.long.process` vinculado al producto final y a la
hoja maestra: BOM larga, tipo de equivalencia (piezas por hoja, o centímetros
utilizables por hoja + piezas por centímetro), rendimiento esperado y
porcentaje de merma (rendimiento 0–100; merma 0–&lt;100), requisito de liberación de calidad y
ubicación fuente opcional (fallback a la fuente de la BOM). Calcula, con
bandera y razón: hojas físicas/liberadas, hojas potenciales desde la BOM
larga, piezas desde hojas físicas/liberadas/potenciales y total potencial —
inventario existente y capacidad potencial siempre por separado. Si se exige
calidad, solo cuentan los lotes liberados; si el campo regulatorio
`amunet_lot_release_state` no existe, el dato es "No calculable".

## Entrega y recepción de material (Acondicionado -> almacén de venta)

El material llega al almacén que surte a la tienda en **dos pasos y con dos
personas** (control de dos partes, ISO 13485), reproduciendo en Odoo lo que
antes hacía el plugin AlmacenPT ("alguien entrega y el almacén acepta"):

1. **ACONDICIONADO ENTREGA** (`amunet.woo.delivery`, grupo
   `group_woo_acondicionado`). Se registra **desde la orden de fabricación**:
   por convención de Amunet la orden **ES** el lote (la orden `0826/01/PSS`
   produce el lote `0826/01/PSS`), así que producto, lote y caducidad salen de
   ahí. Dos botones: **Entrega completa** (todo lo pendiente) y **Entrega
   parcial** (la cantidad que se capture). Odoo 19 no tiene
   `lot_producing_id`: el lote se resuelve por `lot_producing_ids`, luego por
   los movimientos de producto terminado y, por último, por nombre de la orden.
2. **EL ALMACÉN RECIBE**: cuenta físicamente y captura las piezas. Si
   **coincide**, la entrega queda recibida y genera la `amunet.woo.reception`.
   Si **no coincide**, se **RECHAZA COMPLETA** para aclararla — no se acepta a
   medias, porque una diferencia sin resolver es justo lo que después aparece
   como existencia fantasma en la tienda.

### Recibir no es lo mismo que poder vender

Recibir material que Calidad todavía no ha liberado **SÍ está permitido**: pasa
cuando el material urge. Lo que no está permitido es **venderlo**. El candado
no está en recibir sino en **publicar**:

| Situación | Resultado |
| --- | --- |
| Lote liberado por Calidad | Vendible, se publica |
| Lote sin liberar, **con autorización** | Vendible **bajo concesión**, con el autorizante registrado |
| Lote sin liberar, sin autorización | **RETENIDO**: se recibe, pero no se publica |

La autorización es una **liberación bajo concesión** (ISO 13485 8.3), no un
salto silencioso del control: queda con nombre y fecha, se avisa en el chatter
para que Calidad se entere, y se muestra en rojo/ámbar en lista y formulario.
Solo la puede dar el grupo restringido `group_woo_autoriza_concesion`
(PM/Mery y Calidad); la membresía se asigna a mano, nunca por datos del módulo.

### Regularización de material histórico

El material que entró **antes** de existir este flujo no tiene entrega a la
cual autorizar. Por eso la concesión también vive en la **recepción**
(`authorized_by` propio): PM o Calidad pueden regularizar esas recepciones
retenidas una por una **o varias a la vez** desde la lista, con el filtro
**"Requiere regularización (PM/Calidad)"**. Al autorizarlas, lo que estaba
retenido se publica.

### Cantidades: no se puede recibir más de lo que existe

Tanto la entrega como la recepción descuentan lo ya entregado/recibido del lote
contra la existencia libre en la ubicación de piezas de APT. Sin ese candado,
aceptar la recepción del mismo lote varias veces "recibía" 795 pz de un lote de
265 (error real detectado en pruebas). La recepción directa desde el lote
("Aceptar recepción (venta)") queda como vía secundaria y también descuenta lo
ya recibido.

### Publicación

La publicación a la tienda la dispara la aceptación de la recepción, ya **no**
la liberación del lote ni el cierre de la orden de fabricación
(`stock_lot`/`mrp_production` ya no auto-publican). La acción legada
`action_publish_stock` delega en `action_publicar_recepciones` para no duplicar
existencias por dos caminos. Todo sigue tras el candado `allow_stock_publish` y
el Application Password de la tienda; deja bitácora en `woo_sync_log` y ledger
de idempotencia **por recepción** en `amunet.woo.stock.delivery`.

Nota de permisos: los campos de configuración de la tienda
(`apt_pieces_location_id`, `allow_stock_publish`, credenciales) están
reservados a `group_woo_admin`. Todo acceso interno desde código que corre como
almacén o Acondicionado usa `.sudo()`; si no, el usuario recibe un "Error de
acceso" al usar el botón.

## Integraciones y degradación segura

El módulo depende de `amunet_packaging_planning` para usar el catálogo
autorizado de presentaciones. La integración de calidad se detecta de forma
defensiva: si faltan `qc_required`, parámetros o liberación regulatoria de
lotes, esos datos se reportan como "No calculable" con su razón.

## Pruebas

`tests/` cubre: importación idempotente, revisión auditable y guards de
permiso, "No calculable", capacidad corta válida (y cero válido),
merma/equivalencia del proceso largo, restricciones de rango, y ausencia
total de métodos HTTP de escritura y de cron.

```
odoo -d <db> -i amunet_woocommerce --test-enable --stop-after-init
```
