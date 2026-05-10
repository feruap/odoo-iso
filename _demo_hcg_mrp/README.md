# Demo HCG con MRP nativo + routing - DEMO-MRP-HCG-2000-20260510

Ejercicio en STAGING (`Amunet_testing`) sobre 2026-05-10. Producción intacta.

Reconstruye el ejemplo de fabricación del lote piloto de prueba rápida hCG
2000 piezas como una orden de fabricación nativa (`mrp.production`) con BOM,
work centers, routing y trazabilidad de consumo move-by-move.

## Modulos instalados (solo en `Amunet_testing`, NO en `amunet_prod`)

| Modulo | Version | Notas |
|---|---|---|
| `mrp` | 19.0.2.0 | nativo Odoo Community |
| `amunet_production` | 19.0.1.0.0 | custom Amunet, depende de mrp |

Backup pre-instalacion:
`/opt/odoo/backups/db_20260510_074730_manual_Amunet_testing_pre_mrp_install.sql.gz` (6.2 MB)

## Resultado en `Amunet_testing`

### Work Centers (8)

| ID | code | name | equipos asignados (texto en `note`) | costs/h |
|---|---|---|---|---|
| 1 | WC-PESAJE | Pesado y preparacion de reactivos | PRO/BAL/01, PRO/VOR/02, CAL/MIC/02, CAL/MIC/03 | 50 |
| 2 | WC-PRETRAT | Pretratamiento y secado de almohadillas | PRO/HOR/03 | 50 |
| 3 | WC-LAMINADO | Laminado de membrana en hoja maestra | PRO/HOR/03 | 50 |
| 4 | WC-CORTE-HOJA | Corte de hoja laminada | PRO/COH/01, CAL/MIE/01 | 50 |
| 5 | WC-CORTE-TIRA | Corte de tiras | PRO/COT/01, CAL/MIE/01 | 50 |
| 6 | WC-ENSAMBLE | Ensamble de cassette | CAL/LMP/01 | 50 |
| 7 | WC-EMPAQ-PRIM | Empaque primario - sellado pouch | PRO/SDM/01, PRO/SEL/01, CAL/CNM/01..04 | 50 |
| 8 | WC-EMPAQ-SEC | Empaque secundario - etiquetado y caja | CAL/LMP/01 | 50 |

`time_efficiency=100`, `oee_target=85`, `resource_calendar_id=1` (Standard 40h/week).
`mrp.workcenter` no expone FK a `amunet.equipment`, asi que la lista de equipos
queda como texto en el campo `note` de cada work center (HTML lista). Para una
integracion real conviene crear un campo M2M custom `amunet_equipment_ids` sobre
`mrp.workcenter`.

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

Tiempo total de fabricacion estimado: 930 min (~15.5 h). `time_mode=manual`.

### Componentes BOM 3 ligados a operaciones

Cada `bom_line.operation_id` apunta a la op donde se consume:

- **op 2 (Pretratamiento)**: SPALMA08, SPALMA01
- **op 3 (Laminado)**: SPHMT06, MPMNC01
- **op 6 (Ensamble)**: MPAAB01, MPAFV01, MPCAR65
- **op 7 (Empaque primario)**: MPBOL01, STDSC01
- **op 8 (Empaque secundario)**: MICAJ10

Las ops 1, 4 y 5 (pesaje, corte hoja, corte tiras) no tienen consumo material —
son operaciones intermedias.

### MOs creadas

| ID | nombre | state | lote producido | hash DHR | notas |
|---|---|---|---|---|---|
| 2 | AMP/MO/00002 | done | DEMO-MRP-HCG-2000-20260510 (id=1364) | `66050d2556e80906d5533d5425a17933038c115e4088435875d3cffbdf454d0f` | V1 — sin routing, raws cancelados (skip_consumption) |
| 7 | AMP/MO/00007 | done | DEMO-MRP-HCG-2000-20260510-V2 (id=1367) | `78960f7b444649b08ff8ea75cdb4c1aaecf0b54b2ce3b9bdf9dcf598cfde0d7d` | **V2 — con 8 work centers + routing, 10 raws done con qty trazable** |

### QC creados

| ID | nombre | state / result |
|---|---|---|
| 664 | DEMO/QC/MRP/HCG/2000/20260510 | done / **pass** |
| 665 | DEMO/QC/MRP/HCG/2000/20260510-V2 | done / **pass** |

Ambos con 7 determinaciones y firmas analista (uid 63) / supervisor (uid 64) /
sanitario (uid 61). Equipos referenciados: CAL/MIE/01, CAL/CNM/01, CAL/MIC/02,
CAL/LMP/01 (todos reales del catalogo Amunet, con calibraciones DEMO).

### URLs en stagingfc.amunet.com.mx

- BOM 3 + routing: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_bom_form_action/3
- MO V1: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_production_action/2
- **MO V2 (limpia)**: https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_production_action/7
- Lote V1: https://stagingfc.amunet.com.mx/odoo/action-stock.action_production_lot_form/1364
- **Lote V2**: https://stagingfc.amunet.com.mx/odoo/action-stock.action_production_lot_form/1367
- QC V1: https://stagingfc.amunet.com.mx/odoo/action-amunet_quality.action_amunet_quality_check/664
- **QC V2**: https://stagingfc.amunet.com.mx/odoo/action-amunet_quality.action_amunet_quality_check/665
- App Manufacturing: https://stagingfc.amunet.com.mx/odoo/manufacturing
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
6. Marcar checklist operativa: `amunet_check_history_log`,
   `amunet_check_calculations`, `amunet_check_dilution`,
   `amunet_check_aforar` = True, y `quality_analysis_status='approved'`.
7. Procesar workorders: `wo.button_start()` -> `wo.button_finish()`.
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

Asignados como referencia en notas de work centers. Calibraciones vigentes
DEMO (lab "DEMO ISO 13485 - Laboratorio de Calibracion Simulado") creadas el
2026-05-10, vencimiento 2027-05-10. Ningun equipo tiene calibracion REAL en
prod ni en staging — pendiente humano.

PRO/BAL/01, PRO/VOR/02, PRO/HOR/03, PRO/COH/01, PRO/COT/01, PRO/SDM/01,
PRO/SEL/01, CAL/MIE/01, CAL/LMP/01, CAL/CNM/01, CAL/CNM/02, CAL/CNM/03,
CAL/CNM/04, CAL/MIC/02, CAL/MIC/03.

## Inventario de productos terminados Amunet (95 PT)

Auditoria al 2026-05-10 sobre `Amunet_testing`:

- **95 productos terminados** con default_code asignado en categoria
  "Producto terminado / *".
- **Solo 1 con BOM** (DMHCG03, BOM 3 DEMO creado por este ejercicio).
  **Ningun PT tiene BOM real productivo aun**.
- **15 PT con lotes en stock** (todos lotes reales no DEMO):

| Producto | Categoria | Lotes reales |
|---|---|---|
| EQMIC01 - Micropipeta (5-50 µl) | Instrumentos de medición | 61 |
| EQMIC02 - Micropipeta (100-1000 µl) | Instrumentos de medición | 56 |
| EQCBV01 - Centrifuga de baja velocidad | Equipo | 20 |
| EQTER02 - Termobloque DB100 | Equipo | 13 |
| EQINC01 - Incubadora | Equipo | 10 |
| EQGRA03 - Gradilla plástico (2 ml) | Soporte | 4 |
| DMHCG03 - Prueba hCG en orina | Pruebas inmunológicas | 3 reales + 3 DEMO |
| EQGRA01 - Gradilla magnética (2 ml) | Soporte | 2 |
| EQGRA02 - Gradilla magnética (15 ml) | Soporte | 2 |
| EQGRA04 - Gradilla plástico (15 ml) | Soporte | 2 |
| DMCAL01 - Prueba Calprotectina | Pruebas inmunológicas | 1 |
| DMPHV01 - Prueba pH vaginal | Pruebas inmunológicas | 1 |
| EQSMI01 - Soporte de micropipetas | Soporte | 1 |
| EQTER01 - Termobloque MDB100 | Equipo | 1 |
| EQVOR01 - Vortex | Equipo | 1 |

### Sugerencia de prioridad para crear BOMs reales

**P1 — Pruebas con stock real (sin BOM)**: DMCAL01, DMPHV01.
Tienen lote real activo en stock pero ningun expediente de fabricacion
estructurado. Prioridad regulatoria alta para Cofepris/ISO.

**P2 — Pruebas inmunológicas de alta rotacion (sin BOM, sin lote pero
seguramente clave de catalogo)**: DMVIH01, DMVIH02, DMSPN01 (Estreptococo B),
DMSPN02 (Estreptococo A), DMHPY01/02 (Helicobacter), DMTIF01 (Tifoidea),
DMSAT01 (Salmonella), DMENT01 (Entamoeba), DMGIA01 (Giardia), DMHCG01,
DMHCG02 (otras hCG, comparten cadena con DMHCG03 — el BOM seria 80% reusable).

**P3 — Antidoping (regulado, alto volumen)**: DMACT02, DMADO02, DMADO03,
DMADO04, DMADS01, DMAMP02, DMMET02, DMOPI02, DMFEN02, DMALC01.

**P4 — Combos de pandemia/respiratorio**: DMICR01 (combo respiratorio),
DMCBR01 (Campylobacter), DMVSR01 (RSV), DMIAB01 (FluNet), DMRAV01 (Rotavirus).

**P5 — PCR rapidas (7 productos, posible cadena distinta a las inmunologicas
de tira reactiva, requiere otro routing)**: DLASAN01, DLHPY01, DLKRS01,
DLSFE01, DLTB02, DLVIH01, DLVPH01.

**P6 — Equipos y soportes (probablemente compra, no manufactura propia)**:
EQ* (familias de pipetas, gradillas, termobloques). No requieren BOM si
son productos de reventa.

Total con prioridad P1-P5 que SI requieren BOM productivo: ~50 productos.

## Limitacion conocida (V1) — RESUELTA en V2

La MO V1 (id=2) quedo done pero con sus 10 `stock_move` raw en estado
`cancel` y `quantity=0` por usar `skip_consumption=True`. La V2 (id=7)
resuelve esto: los 10 raws estan `done` con `quantity` igual al BOM y el
`stock.move.line` apunta al lote DEMO consumido. Trazabilidad completa.

## Scripts incluidos

- `create_demo_hcg_mrp.py` - V1 (con skip_consumption, deprecate)
- `create_qc_release.py` - QC V1
- `create_workcenters.py` - 8 work centers con equipos en `note`
- `create_routing.py` - 8 operations en BOM 3 + ligado bom_line.operation_id
- `mo_v2_forcelot.py` - **V2 limpia** con consumo trazable
- `qc_v2.py` - QC V2 + liberacion DHR

Todos se corren con:

    docker cp <script> odoo-staging:/tmp/<script>
    docker exec odoo-staging odoo shell -c /etc/odoo/odoo.conf \
      -d Amunet_testing --no-http --db_host db-staging --db_port 5432 \
      --db_user odoo --db_password odoo_stg_2024_secure < /tmp/<script>

## PENDIENTE HUMANO

1. **Cargar certificados de calibracion REALES** en prod (y staging) para
   los 15 equipos involucrados. Hoy todos los certs son DEMO. El equipo
   QC/Calidad debe subir los PDFs reales con sus fechas de vencimiento
   reales.
2. **Decidir migracion a produccion**:
   - ¿Se instalan `mrp` + `amunet_production` en `amunet_prod`?
   - Si SI: requiere PR staging->main + backup pre-deploy + supervision
     visual del CEO/sanitario en `fc.amunet.com.mx`. La instalacion del
     modulo afecta a todos los usuarios (nuevos menus de Manufactura).
   - Si NO: el demo se queda en staging como prueba de concepto.
3. **Capacitacion al equipo de produccion** en el flujo MRP nativo: BOM,
   work orders, consumption warning, registro de `qty_producing`. Hoy el
   personal no opera con MRP.
4. **Definir BOMs P1-P5** (ver inventario PT arriba). Prioridad maxima:
   DMCAL01 y DMPHV01 (tienen stock real activo).
5. **Crear campo M2M `amunet_equipment_ids`** en `mrp.workcenter` para
   formalizar la asignacion equipo->workcenter (hoy es texto en `note`).
   Requiere extender `amunet_production` o crear modulo nuevo.
6. **Resolver el override de `amunet_production.create`** que sobreescribe
   `lot_producing_ids` con un lote auto-generado. Hoy hay que forzar el
   lote manualmente despues del create. Si en prod se usa la UI, este
   comportamiento del override es el deseado, pero documentarlo.
7. **Calcular costo real por hora de cada workcenter** (hoy todos en 50
   MXN/h placeholder). Pedir a Finanzas/Operaciones el costo real.
8. **Definir tiempos reales de cada operacion** sobre lotes reales
   trabajados, no las estimaciones de este demo.

## Rollback total a pre-instalacion mrp

    BACKUP=/opt/odoo/backups/db_20260510_074730_manual_Amunet_testing_pre_mrp_install.sql.gz
    cd /opt/odoo/staging
    docker compose -f docker-compose.staging.yml stop web-staging
    docker exec odoo-staging-db psql -U odoo -d postgres -c \
      "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname='Amunet_testing' AND pid<>pg_backend_pid();"
    docker exec odoo-staging-db dropdb -U odoo --if-exists Amunet_testing
    docker exec odoo-staging-db createdb -U odoo -O odoo Amunet_testing
    gunzip -c "$BACKUP" | docker exec -i odoo-staging-db psql -U odoo -d Amunet_testing
    docker compose -f docker-compose.staging.yml up -d web-staging
