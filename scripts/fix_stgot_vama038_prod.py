"""
CORRECCIÓN TODOS LOS GOTEROS — Desactivar VAMA-038 (producción)
================================================================
Los 7 goteros (STGOT01-07) tienen VAMA-038. MAVI-17 "Conteo de gotas"
(5-10) ya cubre esa evaluación. Se desactivan todas las configs y rels
de VAMA-038 en todos los goteros.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-25
"""

Rel = env['amunet.quality.parameter.product.rel']
Cfg = env['amunet.quality.parameter.specification.config']
Prod = env['product.template']

# Rels de VAMA-038 en STGOT01-07 (confirmadas en producción)
vama_rel_ids = [408, 409, 410, 411, 412, 413, 414]

print("── Desactivando VAMA-038 en todos los goteros ──")
for rel in Rel.browse(vama_rel_ids):
    cfgs = Cfg.search([('product_parameter_rel_id', '=', rel.id)])
    activas = cfgs.filtered(lambda c: c.active)
    print(f"  {rel.product_tmpl_id.default_code}  rel {rel.id}: {len(activas)} configs activas → desactivando")
    cfgs.write({'active': False})
    rel.write({'active': False})

env.cr.commit()

print("\n── Verificación final ──")
for codigo in ['STGOT01','STGOT02','STGOT03','STGOT04','STGOT05','STGOT06','STGOT07']:
    tmpl = Prod.search([('default_code', '=', codigo)], limit=1)
    if not tmpl:
        continue
    rels = Rel.search([('product_tmpl_id', '=', tmpl.id), ('active', '=', True)])
    params = [r.parameter_code for r in rels]
    vama_restante = [p for p in params if p.startswith('VAMA')]
    status = '✓' if not vama_restante else f'⚠ VAMA aún activo: {vama_restante}'
    print(f"  {codigo}: {params}  {status}")

print("\n✓ VAMA-038 eliminado en todos los goteros.")
