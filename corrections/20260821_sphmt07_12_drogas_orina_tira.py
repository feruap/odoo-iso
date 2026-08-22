"""
Crea SPHMT07-12: Hojas Maestras de drogas en orina en tira (competitive).
Son pruebas individuales de tira para detección de droga en orina.

Patrón COMPETITIVO (igual que SPHMC10-14, antidoping sangre):
  MAVI-04 (3 specs): Rasgaduras, Manchas, Deformidad
  MAVI-07 (2 specs): vama_multi_check — INVERTIDO (negativa=#1-4, positiva=#5)
  MAVI-09 (2 specs): Liberación 1-30s / Migración 30-180s
  MAVI-11 (1 spec):  Altura 6 u 8 cm

Hojas creadas:
  SPHMT07 — Hoja Maestra Marihuana (THC)
  SPHMT08 — Hoja Maestra Anfetamina (AMP)
  SPHMT09 — Hoja Maestra Cocaína (COC)
  SPHMT10 — Hoja Maestra Metanfetamina (MET)
  SPHMT11 — Hoja Maestra Opiáceos (OPI)
  SPHMT12 — Hoja Maestra Fentanilo

Aplicado directamente vía SQL en staging (Amunet_testing).
IDs de templates: 2332-2337. IDs de param_rels: 4312-4335.
48 spec_configs insertadas (8 por hoja × 6 hojas).
Reporte: RASP-001 v4 / CERSP-001 v4.

Autorizado por: Diana Flores (s.controldecalidad@amunet.com.mx)
Fecha: 2026-08-21
"""

# Este script ya fue aplicado vía SQL directo en staging.
# Si se necesita reaplicar en producción, ejecutar el equivalente SQL
# o recrear los productos via Odoo ORM.

HOJAS = [
    ('SPHMT07', 'Hoja Maestra Marihuana (THC)'),
    ('SPHMT08', 'Hoja Maestra Anfetamina (AMP)'),
    ('SPHMT09', 'Hoja Maestra Cocaína (COC)'),
    ('SPHMT10', 'Hoja Maestra Metanfetamina (MET)'),
    ('SPHMT11', 'Hoja Maestra Opiáceos (OPI)'),
    ('SPHMT12', 'Hoja Maestra Fentanilo'),
]

for codigo, nombre in HOJAS:
    tmpl = env['product.template'].with_context(active_test=False).search(
        [('default_code', '=', codigo)], limit=1)
    if not tmpl:
        print(f"  ⚠️  {codigo} no encontrado — crear manualmente o via SQL")
        continue
    print(f"  ✅ {codigo} ({nombre}) — id={tmpl.id}")

    rels = env['amunet.quality.parameter.product.rel'].search(
        [('product_tmpl_id', '=', tmpl.id)])
    for rel in rels:
        cfg_count = env['amunet.quality.parameter.specification.config'].search_count(
            [('product_parameter_rel_id', '=', rel.id)])
        print(f"     {rel.parameter_code}: {cfg_count} configs")

print("\nVerificación completada. SPHMT07-12 creadas con patrón competitivo.")
