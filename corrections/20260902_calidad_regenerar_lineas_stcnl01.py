"""
Regenerar líneas de prueba para QC/2026/00041 (STCNL01) en producción.
El análisis tiene 0 líneas porque el script anterior configuró los parámetros
en el producto DESPUÉS de que el análisis ya estaba en_progreso.

También: reactivar STCON01 (id=1006) y SPCNL04 (id=1814) y aplicarles
los parámetros correctos (MAVI-20 + MAVI-07 negativo) en producción.

Autorizado por Diana Flores, 2026-09-02.
"""
import json

QCheck = env['amunet.quality.check']
ProdTmpl = env['product.template']
Param = env['amunet.quality.check.parameter']
Rel = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
SpecBase = env['amunet.quality.check.parameter.specification']

# ── 1. Regenerar líneas de QC/2026/00041 (STCNL01) ──────────────────────────
print("── 1. Regenerar líneas de QC/2026/00041 (STCNL01) ──")
check = QCheck.browse(785)
print(f"  Análisis: {check.name} | producto: {check.product_id.default_code} | estado: {check.state}")
print(f"  Líneas actuales: {len(check.test_line_ids)}")

if len(check.test_line_ids) == 0:
    # Llamar al método que carga los parámetros
    check._load_product_parameters()
    env.cr.flush()
    print(f"  Líneas después de cargar: {len(check.test_line_ids)}")
    for line in check.test_line_ids:
        print(f"    - {line.name}")
else:
    print("  Ya tiene líneas, no se regeneran.")

# ── 2. Reactivar STCON01 (id=1006) y aplicar parámetros correctos ────────────
print("\n── 2. Verificar STCON01 (id=1006) ──")
tmpl_stcon01 = ProdTmpl.with_context(active_test=False).browse(1006)
print(f"  Nombre: {tmpl_stcon01.name} | activo: {tmpl_stcon01.active}")
print(f"  Parámetros actuales: {Rel.search([('product_tmpl_id', '=', 1006)]).mapped('parameter_id.code')}")

# ── 3. Verificar SPCNL04 (id=1814) ───────────────────────────────────────────
print("\n── 3. Verificar SPCNL04 (id=1814) ──")
tmpl_spcnl04 = ProdTmpl.with_context(active_test=False).browse(1814)
print(f"  Nombre: {tmpl_spcnl04.name} | activo: {tmpl_spcnl04.active}")
print(f"  Parámetros: {Rel.search([('product_tmpl_id', '=', 1814)]).mapped('parameter_id.code')}")

# ── 4. Ver también STCON01 activo (código STCON01 en el sistema) ─────────────
print("\n── 4. Buscar STCON01 por código ──")
tmpl_stcon_activo = ProdTmpl.with_context(active_test=False).search([('default_code', '=', 'STCON01')])
for t in tmpl_stcon_activo:
    rels = Rel.search([('product_tmpl_id', '=', t.id)])
    checks = QCheck.with_context(active_test=False).search([('product_id.product_tmpl_id', '=', t.id)])
    print(f"  id={t.id} activo={t.active} params={rels.mapped('parameter_id.code')} análisis={len(checks)}")
    for c in checks:
        print(f"    {c.name} | {c.state} | líneas: {len(c.test_line_ids)}")

env.cr.commit()
print("\n✓ Listo.")
