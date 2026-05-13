# Demo HCG con MRP nativo + routing - DEMO-MRP-HCG-2000-20260510

> **⚠️ ADVERTENCIA — CERTIFICADOS Y LOTES DEMO**
>
> Esta carpeta documenta un escenario de fabricacion **simulado** sobre la
> base `Amunet_testing` (staging). **NO es evidencia regulatoria.**
>
> Especificamente:
>
> - Los **15 certificados de calibracion** vinculados a los equipos del
>   demo (cal_id 16-25) llevan `lab_name = "DEMO ISO 13485 - Laboratorio
>   de Calibracion Simulado"` y vencen 2027-05-10. Son **ficticios**.
>   No deben presentarse en una inspeccion Cofepris ni en una auditoria
>   ISO 13485 como prueba de conformidad. Antes de migrar a produccion
>   los equipos deben tener certs **reales** de un laboratorio acreditado,
>   subidos al modulo `amunet_equipment_calibration` con su PDF firmado.
>
> - Los **11 lotes de materiales y producto terminado** llevan prefijo
>   `DEMO-` (DEMO-SPHMT06-HCG-..., DEMO-MRP-HCG-2000-..., etc.). Son
>   lotes virtuales creados por scripts. Los lotes reales en stock siguen
>   intactos y nunca fueron tocados.
>
> - El **SOP DEMO-SOP-HCG-001** y las **capacitaciones DEMO** son
>   placeholders para que el flujo se complete; el equipo de produccion
>   real no esta capacitado contra ellos.
>
> - Toda esta evidencia debe regenerarse con datos reales antes de
>   considerar el flujo MRP listo para producir lotes regulatorios.

Ejercicio en STAGING (`Amunet_testing`) sobre 2026-05-10. Producción intacta.

Reconstruye el ejemplo de fabricación del lote piloto de prueba rápida hCG
2000 piezas como una orden de fabricación nativa (`mrp.production`) con BOM,
work centers, routing y trazabilidad de consumo move-by-move.

## Modulos instalados (solo en `Amunet_testing`, NO en `amunet_prod`)

| Modulo | Version | Notas |
|---|---|---|
| `mrp` | 19.0.2.0 | nativo Odoo Community |
| `amunet_production` | **19.0.1.3.0** | custom Amunet, depende de mrp + amunet_equipment_calibration |

**19.0.1.1.0**: M2M formal `amunet_equipment_ids` en `mrp.workcenter`
+ override de `mrp.workorder.button_start()` que valida que **todos** los
equipos vinculados tengan certificado de calibracion vigente. Vista nueva
`Equipos Amunet` en el form de cada workcenter.

**19.0.1.2.0** (actual):
- Fail-closed: workcenter sin equipos vinculados Y sin marca de excepcion
  bloquea `button_start` con UserError. Antes pasaba silenciosamente
  (riesgo: WC mal configurado dispara produccion sin chequeo).
- Validacion adicional de `equipment.state == 'active'`. Si esta en
  `maintenance` o `out_of_service`, la WO no arranca aunque tenga cert
  vigente.
- Campo nuevo `amunet_no_equipment_required` en `mrp.workcenter` para
  documentar excepcion ISO 13485 (mesa manual sin instrumento). Vista
  con boolean_toggle en la pestana "Equipos Amunet".
- Cuando se aplica la excepcion, el override publica nota en el chatter
  de la `mrp.production` padre (mrp.workorder no es mail.thread): "WO X
  iniciada sin equipos calibrados. Excepcion autorizada en WC Y...".

**19.0.1.3.0** (actual): reporte de la MO con **links clickeables** y
seccion **Trazabilidad ISO 13485**.

Cambios:
- `reports/mrp_production_report.xml`: inherit de `mrp.report_mrporder` y
  `mrp.report_mrp_production_components`. CSS con clase `amunet-link`.
- `data/system_parameters.xml`: registra
  `amunet_production.report_base_url = https://stagingfc.amunet.com.mx`
  para construir URLs absolutas. Si esta vacio, fallback a
  `web.base.url`.
- En el PDF cada uno de estos elementos lleva al expediente vivo:
  nombre de la MO, source (si es lote), producto terminado, lote
  producido, BOM, work center, cada componente del BOM, cada lote
  consumido por componente.
- Seccion "Trazabilidad ISO 13485" al final del PDF con tablas
  (linkeables): QC + hash DHR; ordenes de trabajo con WC, fechas,
  duracion y equipos vinculados; equipos calibrados con cert vigente;
  firmantes del QC.

Verificacion (PDF de MO 7 / `MO_AMP_00007_clickable.pdf`):
- 67 anotaciones de URI, 48 URLs unicas, 3 paginas, 51 KB.
- 1 link a la MO, 11 a productos, 12 a lotes (final + componentes),
  1 al BOM, 8 a workcenters, 1 al QC, 33 a equipos.


Backup pre-instalacion mrp:
`/opt/odoo/backups/db_20260510_074730_manual_Amunet_testing_pre_mrp_install.sql.gz` (6.2 MB)

Backup pre-update v110:
`/opt/odoo/backups/db_20260510_175751_pre_amunet_prod_v110.sql.gz` (6.5 MB)

## Resultado en `Amunet_testing`

### Work Centers (8)

| ID | code | name | M2M `amunet_equipment_ids` | costs/h |
|---|---|---|---|---|
| 1 | WC-PESAJE | Pesado y preparacion de reactivos | PRO/BAL/01, PRO/VOR/02, CAL/MIC/02, CAL/MIC/03 | 50 |
| 2 | WC-PRETRAT | Pretratamiento y secado de almohadillas | PRO/HOR/03 | 50 |
| 3 | WC-LAMINADO | Laminado de membrana en hoja maestra | PRO/HOR/03 | 50 |
| 4 | WC-CORTE-HOJA | Corte de hoja laminada | PRO/COH/01, CAL/MIE/01 | 50 |
| 5 | WC-CORTE-TIRA | Corte de tiras | PRO/COT/01, CAL/MIE/01 | 50 |
| 6 | WC-ENSAMBLE | Ensamble de cassette | CAL/LMP/01 | 50 |
| 7 | WC-EMPAQ-PRIM | Empaque primario - sellado pouch | PRO/SDM/01, PRO/SEL/01, CAL/CNM/01..04 | 50 |
| 8 | WC-EMPAQ-SEC | Empaque secundario - etiquetado y caja | CAL/LMP/01 | 50 |

`time_efficiency=100`, `oee_target=85`, `resource_calendar_id=1`.

Los equipos ahora estan vinculados como **relacion formal Many2many**
(`amunet_workcenter_equipment_rel`), no como texto en `note`. Cuando se
inicia una WO en un WC, el sistema valida calibracion vigente de TODOS
los equipos vinculados antes de arrancar. Si alguno esta caducado o sin
cert, lanza UserError detallado (ver `EVIDENCE_UserError_calibration.txt`).

### Operaciones de routing en BOM 3 (8)

| op_id | seq | name | workcenter | tiempo (min) p/2000 |
|---|---|---|---|---|
| 1 | 10 | Pesar y preparar reactivos | WC-PESAJE | 60 |
| 2 | 20 | Pretratar y secar almohadillas | WC-PRETRAT | 120 |
| 3 | 30 | Laminar membrana en hoja maestra | WC-LAMINADO | 90 |
| 4 | 40 | Cortar hoja laminada | WC-CORTE-HOJA | 60 |
| 5 | 50 | Cortar tiras | WC-CORTE-TIRA | 90 |
| 6 | 60 | Ensamblar cassette | WC-ENSAMBLE | 240 |
| 7 | 70 | Empaque primario - sellar pouch | WC-EMPAQ-PRIM | 180 |
| 8 | 80 | Empaque secundario - etiquetado y caja | WC-EMPAQ-SEC | 90 |

Tiempo total estimado: 930 min (~15.5 h sobre 2 dias laborales).

### Componentes BOM 3 ligados a operaciones

- **op 2 (Pretratamiento)**: SPALMA08, SPALMA01
- **op 3 (Laminado)**: SPHMT06, MPMNC01
- **op 6 (Ensamble)**: MPAAB01, MPAFV01, MPCAR65
- **op 7 (Empaque primario)**: MPBOL01, STDSC01
- **op 8 (Empaque secundario)**: MICAJ10

### MOs creadas

| ID | nombre | state | lote producido | hash DHR | notas |
|---|---|---|---|---|---|
| 2 | AMP/MO/00002 | done | DEMO-MRP-HCG-2000-20260510 (id=1364) | `66050d2556e80906d5533d5425a17933038c115e4088435875d3cffbdf454d0f` | V1 — sin routing, raws cancelados |
| 7 | AMP/MO/00007 | done | DEMO-MRP-HCG-2000-20260510-V2 (id=1367) | `78960f7b444649b08ff8ea75cdb4c1aaecf0b54b2ce3b9bdf9dcf598cfde0d7d` | **V2 — limpia, routing, consumo trazable, timestamps WO realistas** |

### Timestamps reales en las 8 WO de MO 7 (UTC)

Espaciados sobre 2 dias laborales:

| WO ID | WC | start | end | duration (min) |
|---|---|---|---|---|
| 25 | WC-PESAJE | 2026-05-10 13:00 | 2026-05-10 14:00 | 60 |
| 26 | WC-PRETRAT | 2026-05-10 14:00 | 2026-05-10 16:00 | 120 |
| 27 | WC-LAMINADO | 2026-05-10 16:00 | 2026-05-10 17:30 | 90 |
| 28 | WC-CORTE-HOJA | 2026-05-10 18:30 | 2026-05-10 19:30 | 60 |
| 29 | WC-CORTE-TIRA | 2026-05-10 19:30 | 2026-05-10 21:00 | 90 |
| 30 | WC-ENSAMBLE | 2026-05-11 13:00 | 2026-05-11 17:00 | 240 |
| 31 | WC-EMPAQ-PRIM | 2026-05-11 18:00 | 2026-05-11 21:00 | 180 |
| 32 | WC-EMPAQ-SEC | 2026-05-11 21:00 | 2026-05-11 22:30 | 90 |

Los timestamps se persistieron via SQL directo porque `date_finished` es
un campo `compute=True store=True` en `mrp.workorder`: escribirlo via
ORM provoca que el compute lo recalcule respetando el resource_calendar.

### QC creados

| ID | nombre | state / result |
|---|---|---|
| 664 | DEMO/QC/MRP/HCG/2000/20260510 | done / **pass** |
| 665 | DEMO/QC/MRP/HCG/2000/20260510-V2 | done / **pass** |

Ambos con 7 determinaciones y firmas analista (uid 63) / supervisor (uid 64) /
sanitario (uid 61). Equipos referenciados: CAL/MIE/01, CAL/CNM/01, CAL/MIC/02,
CAL/LMP/01.

### URLs en stagingfc.amunet.com.mx

- BOM 3 + routing: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_bom_form_action/3
- MO V1: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_production_action/2
- **MO V2 (limpia)**: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_production_action/7
- Lote V1: https://stagingfc.amunet.com.mx/odoo/action-stock.action_production_lot_form/1364
- **Lote V2**: https://stagingfc.amunet.com.mx/odoo/action-stock.action_production_lot_form/1367
- QC V1: https://stagingfc.amunet.com.mx/odoo/action-amunet_quality.action_amunet_quality_check/664
- **QC V2**: https://stagingfc.amunet.com.mx/odoo/action-amunet_quality.action_amunet_quality_check/665
- Work Centers: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_workcenter_action

## Como se resolvio el wizard `mrp.consumption.warning`

El wizard se dispara cuando `move.quantity != move.product_uom_qty` para
algun raw move al llamar a `button_mark_done`. La forma correcta (que
NO usa `skip_consumption=True`) es:

1. `mo.action_confirm()` y `mo.action_assign()`
2. Para cada raw move: `move.move_line_ids.unlink()`, crear nuevo
   `stock.move.line` con lot_id y quantity = qty del BOM, y luego
   `move.with_context(bypass_reservation_update=True).quantity = plan_qty`
   y `move.picked = True`.
3. NO tocar `move_finished_ids` — dejar que `_post_inventory` lo gestione
   via `lot_producing_ids` y `qty_producing`.
4. `mo.qty_producing = 2000`
5. Forzar `mo.lot_producing_ids = [(6, 0, [final_lot.id])]` DESPUES del
   `create()` y DESPUES de `action_confirm()`. El override de
   `amunet_production.create` autogenera un lote nuevo via
   `_auto_generate_lot_draft()` y sobreescribe lo que pongas en `vals`.
6. Marcar checklist operativa.
7. Procesar workorders.
8. `mo.button_mark_done()` — con todo lo anterior, retorna True y la MO
   queda en `done` sin disparar el wizard.

Si el wizard se dispara igual:

```python
res = mo.button_mark_done()
if isinstance(res, dict) and res.get('res_model') == 'mrp.consumption.warning':
    wiz_ctx = res.get('context', {})
    wiz = env['mrp.consumption.warning'].with_context(**wiz_ctx).create({
        'mrp_production_ids': wiz_ctx.get('default_mrp_production_ids'),
        'mrp_consumption_warning_line_ids': wiz_ctx.get('default_mrp_consumption_warning_line_ids', []),
    })
    wiz.action_confirm()  # equivale a "Continue" en la UI
```

## Materiales reales Amunet (catalogo) usados con lotes DEMO

11 productos reales (mismos IDs que en `amunet_prod`):

| Producto | Lote DEMO | Cantidad |
|---|---|---|
| DMHCG03 - Prueba rápida de Embarazo hCG en orina | DEMO-MRP-HCG-2000-20260510 (V1) / -V2 | 2000 piezas |
| SPHMT06 - Hoja Maestra hCG orina | DEMO-SPHMT06-HCG-20260510 | 70 |
| MPMNC01 - Membrana de nitrocelulosa 10 µm | DEMO-MPMNC01-HCG-20260510 | 70 |
| SPALMA08 - Almohadilla A8 muestra orina | DEMO-SPALMA08-HCG-20260510 | 2100 |
| SPALMA01 - Almohadilla A1 conjugado pretratada | DEMO-SPALMA01-HCG-20260510 | 2100 |
| MPAAB01 - Almohadilla absorbente | DEMO-MPAAB01-HCG-20260510 | 2100 |
| MPAFV01 - Almohadilla fibra de vidrio | DEMO-MPAFV01-HCG-20260510 | 2100 |
| MPCAR65 - Cartucho hCG | DEMO-MPCAR65-HCG-20260510 | 2000 |
| MPBOL01 - Bolsa termosellable 6x12 cm | DEMO-MPBOL01-HCG-20260510 | 2000 |
| STDSC01 - Desecantes | DEMO-STDSC01-HCG-20260510 | 2000 |
| MICAJ10 - Caja caple HCG | DEMO-MICAJ10-HCG-20260510 | 200 |

## Equipos reales Amunet usados (15)

Hoy todos vinculados formalmente via `amunet_equipment_ids` y todos con
**certificado DEMO vigente** (15/15). Los 4 que no tenian cert (CAL/CNM/02,
CAL/CNM/03, CAL/CNM/04, CAL/MIC/03) recibieron uno DEMO el 2026-05-10
para mantener el flujo MRP funcional. Ver
`EVIDENCE_UserError_calibration.txt` para la prueba del constraint.

## Inventario de productos terminados Amunet (95 PT)

Solo DMHCG03 tiene BOM (DEMO BOM 3). 0 PT con BOM real productivo.
15 PT con stock real, 1 con BOM DEMO.

**Prioridad sugerida** para crear BOMs reales (detalle abajo):
- **P1**: DMCAL01 (Calprotectina), DMPHV01 (pH vaginal) — tienen stock real sin BOM.
- **P2**: ~10 inmunológicas alta rotación (DMVIH01/02, DMSPN01/02, DMHPY01/02, DMTIF01, DMSAT01, DMENT01, DMGIA01, DMHCG01/02).
- **P3**: ~10 antidoping.
- **P4**: ~5 combos respiratorios.
- **P5**: 7 PCR rápidas (cadena distinta).
- **P6**: Equipos/soportes (probable reventa).

## Anti-prod guard en scripts

**Todos los scripts en este folder** llevan al inicio:

```python
from odoo.exceptions import UserError as _DemoGuardError

ALLOWED_DB = "Amunet_testing"
if env.cr.dbname != ALLOWED_DB:
    raise _DemoGuardError(
        "SCRIPT DEMO: solo se ejecuta en BD %r. BD actual: %r. Abortado." % (
            ALLOWED_DB, env.cr.dbname
        )
    )
```

Si alguien intenta correr cualquiera de estos scripts contra `amunet_prod`,
falla DURO con UserError antes de tocar nada.

## Scripts incluidos

- `create_demo_hcg_mrp.py` - V1 (con skip_consumption, deprecated)
- `create_qc_release.py` - QC V1
- `create_workcenters.py` - 8 work centers
- `create_routing.py` - 8 operations en BOM 3 + ligado bom_line.operation_id
- `mo_v2_forcelot.py` - **V2 limpia** con consumo trazable
- `qc_v2.py` - QC V2 + liberacion DHR
- `update_wo_timestamps.py` - tiempos realistas en WO de MO 7

Todos se corren con:

    docker cp <script> odoo-staging:/tmp/<script>
    docker exec odoo-staging odoo shell -c /etc/odoo/odoo.conf \
      -d Amunet_testing --no-http --db_host db-staging --db_port 5432 \
      --db_user odoo --db_password odoo_stg_2024_secure < /tmp/<script>

## Documentos adicionales

- `EVIDENCE_UserError_calibration.txt` — prueba del constraint de
  calibracion vigente con 3 escenarios (cert caducado, button_start,
  cert revertido).
- `MO_AMP_00007.pdf` — reporte de la MO V2 generado por el reporte nativo
  `mrp.action_report_production_order` (1 pagina, 20.3 KB, BOM completo
  con consumos done).

## PENDIENTE HUMANO

1. **Cargar certificados de calibracion REALES** en prod y staging para
   los 15 equipos. Hoy todos los certs son DEMO de un lab simulado;
   no sirven como evidencia regulatoria.
2. **Decidir migracion a produccion**:
   - ¿Se instalan `mrp` + `amunet_production` v19.0.1.1.0 en `amunet_prod`?
   - Si SI: requiere PR staging→main + backup pre-deploy + supervision
     visual. Aparecen menus de Manufactura para todos los usuarios; el
     constraint de calibracion empieza a aplicar.
   - Si NO: el demo se queda en staging.
3. **Capacitacion al equipo de produccion** en flujo MRP nativo: BOM,
   work orders, consumption warning, registro de qty_producing.
4. **Definir BOMs reales P1-P5** (~50 productos). Maxima prioridad:
   DMCAL01, DMPHV01.
5. **Resolver el override de `amunet_production.create`** que sobreescribe
   `lot_producing_ids` con un lote auto-generado. Hoy hay que forzar el
   lote manualmente despues del create. Documentar esto en el manual
   del equipo de produccion o ajustar el override para respetar `vals`
   cuando vienen explicitos.
5. **Calcular costo real por hora de cada workcenter** (hoy 50 MXN/h
   placeholder).
6. **Medir tiempos reales por operacion** sobre lotes reales.
7. **Asignar capacidades reales** en `mrp.workcenter.capacity` por
   producto si aplica.
8. **Marca `amunet_no_equipment_required`**: si en produccion existen
   workcenters legitimamente sin instrumentos (mesas manuales, areas de
   inspeccion visual), antes de instalar el modulo en `amunet_prod` se
   debe marcar la excepcion en cada uno con justificacion ISO 13485
   documentada (referencia a SOP/CAPA). Sin esa marca, button_start
   bloquea la WO completamente.
9. **Grupos MRP a admins (HALLAZGO 2026-05-10)**: cuando se instale
   `mrp` en `amunet_prod`, los usuarios admin no heredan los grupos de
   Manufacturing automaticamente. Aunque tengan `base.group_system`,
   los links del PDF a BOM y Work Center disparan AccessError. Asignar
   `mrp.group_mrp_manager` + `mrp.group_mrp_user` + `mrp.group_mrp_routings`
   a cada admin master tras la instalacion. En staging ya esta hecho
   para Fernando (uid 67) via odoo shell.
10. **Tours pendientes en master**: el usuario master Fernando tenia
    `tour_enabled=True` y 6 tours pendientes (purchase_tour, account_tour,
    discuss_channel_tour, etc.). Esto bloquea la carga del web client
    porque el tour intenta clickear menus que no estan disponibles aun.
    Solucion en staging: marcar tours como consumidos +
    `tour_enabled=False`. Para prod: hacer lo mismo a cada admin que
    no necesite el onboarding.
11. **Reemplazar SOP demo** con el SOP real de fabricacion hCG y
   capacitar al equipo contra el SOP real.

## Rollback total

    BACKUP=/opt/odoo/backups/db_20260510_074730_manual_Amunet_testing_pre_mrp_install.sql.gz
    cd /opt/odoo/staging
    docker compose -f docker-compose.staging.yml stop web-staging
    docker exec odoo-staging-db psql -U odoo -d postgres -c \
      "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='Amunet_testing' AND pid<>pg_backend_pid();"
    docker exec odoo-staging-db dropdb -U odoo --if-exists Amunet_testing
    docker exec odoo-staging-db createdb -U odoo -O odoo Amunet_testing
    gunzip -c "$BACKUP" | docker exec -i odoo-staging-db psql -U odoo -d Amunet_testing
    docker compose -f docker-compose.staging.yml up -d web-staging

## Rollback solo del bump v110 (mantiene mrp y datos demo)

    BACKUP=/opt/odoo/backups/db_20260510_175751_pre_amunet_prod_v110.sql.gz
    # mismo procedimiento; restaura el state pre-update del modulo
