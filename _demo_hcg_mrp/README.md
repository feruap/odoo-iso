# Demo HCG con MRP nativo - DEMO-MRP-HCG-2000-20260510

Ejecutado en staging el 2026-05-10. Reconstruye el ejemplo de fabricacion
del lote piloto de prueba rapida hCG 2000 piezas usando el modulo nativo
`mrp` de Odoo (recien instalado este dia en staging).

## Modulos instalados en este ejercicio

| Modulo | Version | Notas |
|---|---|---|
| `mrp` | 19.0.2.0 | nativo Odoo Community |
| `amunet_production` | 19.0.1.0.0 | custom Amunet, depende de mrp |

Backup pre-instalacion:
`/opt/odoo/backups/db_20260510_074730_manual_Amunet_testing_pre_mrp_install.sql.gz` (6.2 MB)

## Objetos creados en `Amunet_testing`

| Objeto | ID | Identificador |
|---|---|---|
| BOM `mrp.bom` | 3 | `DEMO-MRP-HCG-2000-20260510` |
| MO `mrp.production` | 2 | `AMP/MO/00002` (state=done) |
| Lote final `stock.lot` | 1364 | `DEMO-MRP-HCG-2000-20260510` |
| QC `amunet.quality.check` | 664 | `DEMO/QC/MRP/HCG/2000/20260510` (pass) |
| Numero de analisis | - | `DEMO-AN-MRP-HCG-20260510-001` |
| Hash DHR | - | `66050d2556e80906d5533d5425a17933038c115e4088435875d3cffbdf454d0f` |

## Materiales reales Amunet con lotes DEMO consumidos

| Producto | Lote DEMO | Cantidad |
|---|---|---|
| SPHMT06 - Hoja Maestra hCG orina | DEMO-SPHMT06-HCG-20260510 | 70 |
| MPMNC01 - Membrana de nitrocelulosa 10 um | DEMO-MPMNC01-HCG-20260510 | 70 |
| SPALMA08 - Almohadilla A8 muestra orina | DEMO-SPALMA08-HCG-20260510 | 2100 |
| SPALMA01 - Almohadilla A1 conjugado pretratada | DEMO-SPALMA01-HCG-20260510 | 2100 |
| MPAAB01 - Almohadilla absorbente | DEMO-MPAAB01-HCG-20260510 | 2100 |
| MPAFV01 - Almohadilla fibra de vidrio | DEMO-MPAFV01-HCG-20260510 | 2100 |
| MPCAR65 - Cartucho hCG | DEMO-MPCAR65-HCG-20260510 | 2000 |
| MPBOL01 - Bolsa termosellable 6x12 cm | DEMO-MPBOL01-HCG-20260510 | 2000 |
| STDSC01 - Desecantes | DEMO-STDSC01-HCG-20260510 | 2000 |
| MICAJ10 - Caja caple HCG | DEMO-MICAJ10-HCG-20260510 | 200 |

## Equipos reales con certificados demo (de la fase previa)

CAL/MIE/01 (Micrometro), CAL/CNM/01 (Cronometro), CAL/MIC/02 (Micropipeta),
CAL/LMP/01 (Lampara QC), PRO/COH/01, PRO/COT/01, PRO/HOR/03, PRO/SDM/01,
PRO/SEL/01, PRO/BAL/01, PRO/VOR/02. Certificados vigentes hasta 2027-05-10.

## Usuarios y firmas en QC 664

| Rol | Usuario | uid |
|---|---|---|
| Almacen (responsable MO) | supalmacen@amunet.com.mx | - |
| Realizo QC | analista1cc@amunet.com.mx | 63 |
| Verifico QC | s.controldecalidad@amunet.com.mx | 64 |
| Autorizo y libero DHR | desarrollo@amunet.com.mx | 61 |

## URLs en stagingfc.amunet.com.mx

- BOM:    https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_bom_form_action/3
- MO:     https://stagingfc.amunet.com.mx/odoo/action-mrp.mrp_production_action/2
- Lote:   https://stagingfc.amunet.com.mx/odoo/action-stock.action_production_lot_form/1364
- QC:     https://stagingfc.amunet.com.mx/odoo/action-amunet_quality.action_amunet_quality_check/664
- mrp:    https://stagingfc.amunet.com.mx/odoo/manufacturing
- calidad:https://stagingfc.amunet.com.mx/odoo/calidad

## Limitacion conocida (documentada)

Los `stock_move` raw de la MO 2 quedaron en estado `cancel` con `quantity=0`
porque al marcarla como done se uso `skip_consumption=True` para evitar el
wizard interactivo de consumption warning de Odoo 19. La MO esta done y el
lote final fue producido y liberado correctamente, pero la trazabilidad
move-by-move de los componentes al BOM se perdio en `stock.move.line`.

Los lotes DEMO de los componentes siguen disponibles en `AMP/Existencias`
con la cantidad completa, asi que para una demo con consumos visibles
basta con repetir el flujo creando una nueva MO desde la UI y validandola
con el wizard nativo (no skip_consumption).

Esto es DEMO en staging, no afecta produccion. Documentado para mejora
futura: en una segunda iteracion conviene resolver el wizard de consumption
warning programaticamente (action_confirm sobre mrp.consumption.warning)
o pre-cargar los moves con `move.quantity` y `move.picked=True` ANTES de
button_mark_done.

## Scripts incluidos

- `create_demo_hcg_mrp.py` - crea BOM + MO + done
- `create_qc_release.py` - crea QC + firmas + libera DHR

Ambos se corren con:

    docker cp <script> odoo-staging:/tmp/<script>
    docker exec odoo-staging odoo shell \
      -c /etc/odoo/odoo.conf -d Amunet_testing --no-http \
      --db_host db-staging --db_port 5432 \
      --db_user odoo --db_password odoo_stg_2024_secure < /tmp/<script>

## Rollback

Si algo se cae:

    BACKUP=/opt/odoo/backups/db_20260510_074730_manual_Amunet_testing_pre_mrp_install.sql.gz
    cd /opt/odoo/staging
    docker compose -f docker-compose.staging.yml stop web-staging
    docker exec odoo-staging-db psql -U odoo -d postgres \
      -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'Amunet_testing' AND pid <> pg_backend_pid();"
    docker exec odoo-staging-db dropdb -U odoo --if-exists Amunet_testing
    docker exec odoo-staging-db createdb -U odoo -O odoo Amunet_testing
    gunzip -c "$BACKUP" | docker exec -i odoo-staging-db psql -U odoo -d Amunet_testing
    docker compose -f docker-compose.staging.yml up -d web-staging
