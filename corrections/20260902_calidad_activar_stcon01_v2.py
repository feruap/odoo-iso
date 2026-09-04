"""
Activar y configurar STCON01 (id=1006) y SPCNL04 (id=1814) — v2.
No borra relaciones (hay análisis que las referencian).
Solo desactiva specs incorrectas y agrega/actualiza MAVI-20 y MAVI-07 negativo.
"""
import json

ProdTmpl = env['product.template']
Param    = env['amunet.quality.check.parameter']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']

param_mavi07 = Param.search([('code', '=', 'MAVI-07')], limit=1)
param_mavi20 = Param.search([('code', '=', 'MAVI-20')], limit=1)

# Obtener specs de referencia desde STCNL01 (id=1811, ya correcto)
rel_ref_m20 = Rel.search([('product_tmpl_id', '=', 1811), ('parameter_id', '=', param_mavi20.id)], limit=1)
rel_ref_m07 = Rel.search([('product_tmpl_id', '=', 1811), ('parameter_id', '=', param_mavi07.id)], limit=1)
specs_ref_mavi20 = SpecConf.with_context(active_test=False).search([
    ('product_parameter_rel_id', '=', rel_ref_m20.id), ('active', '=', True)])
specs_ref_mavi07 = SpecConf.with_context(active_test=False).search([
    ('product_parameter_rel_id', '=', rel_ref_m07.id), ('active', '=', True)])
print(f"Specs referencia: MAVI-20={len(specs_ref_mavi20)}, MAVI-07={len(specs_ref_mavi07)}")

env = env(context=dict(env.context, amunet_alta_autorizada=True))

for tmpl_id, codigo, nombre in [(1006, 'STCON01', 'Control negativo'), (1814, 'SPCNL04', 'Control Negativo VPH')]:
    print(f"\n── {codigo} (id={tmpl_id}) ──")
    tmpl = ProdTmpl.with_context(active_test=False).browse(tmpl_id)
    
    # 1. Reactivar producto
    if not tmpl.active:
        tmpl.write({'active': True})
        print(f"  Reactivado.")
    
    # 2. Desactivar specs de parámetros incorrectos (sin borrar la rel)
    rels_actuales = Rel.with_context(active_test=False).search([('product_tmpl_id', '=', tmpl_id)])
    for r in rels_actuales:
        if r.parameter_id.code not in ('MAVI-20', 'MAVI-07'):
            specs_inc = SpecConf.with_context(active_test=False).search([
                ('product_parameter_rel_id', '=', r.id), ('active', '=', True)])
            if specs_inc:
                specs_inc.write({'active': False})
                print(f"  Desactivadas {len(specs_inc)} specs de {r.parameter_id.code}")
    
    # 3. MAVI-20: crear rel si no existe, luego copiar specs
    rel_m20 = Rel.search([('product_tmpl_id', '=', tmpl_id), ('parameter_id', '=', param_mavi20.id)], limit=1)
    if not rel_m20:
        rel_m20 = Rel.create({'product_tmpl_id': tmpl_id, 'parameter_id': param_mavi20.id})
        print(f"  Rel MAVI-20 creada (id={rel_m20.id})")
    for spec_ref in specs_ref_mavi20:
        existe = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', rel_m20.id),
            ('specification_id', '=', spec_ref.specification_id.id),
        ], limit=1)
        vals = {
            'active': True,
            'evaluation_type': spec_ref.evaluation_type,
            'acceptance_criteria': spec_ref.acceptance_criteria,
            'text_phrase_mapping': spec_ref.text_phrase_mapping,
        }
        if not existe:
            vals['product_parameter_rel_id'] = rel_m20.id
            vals['specification_id'] = spec_ref.specification_id.id
            SpecConf.create(vals)
            print(f"  Spec MAVI-20/{spec_ref.specification_id.name} CREADA")
        else:
            existe.write(vals)
            print(f"  Spec MAVI-20/{spec_ref.specification_id.name} actualizada")
    
    # 4. MAVI-07: crear rel si no existe, luego copiar specs
    rel_m07 = Rel.search([('product_tmpl_id', '=', tmpl_id), ('parameter_id', '=', param_mavi07.id)], limit=1)
    if not rel_m07:
        rel_m07 = Rel.create({'product_tmpl_id': tmpl_id, 'parameter_id': param_mavi07.id})
        print(f"  Rel MAVI-07 creada (id={rel_m07.id})")
    for spec_ref in specs_ref_mavi07:
        existe = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', rel_m07.id),
            ('specification_id', '=', spec_ref.specification_id.id),
        ], limit=1)
        vals = {
            'active': True,
            'evaluation_type': spec_ref.evaluation_type,
            'acceptance_criteria': spec_ref.acceptance_criteria,
            'text_phrase_mapping': spec_ref.text_phrase_mapping,
        }
        if not existe:
            vals['product_parameter_rel_id'] = rel_m07.id
            vals['specification_id'] = spec_ref.specification_id.id
            SpecConf.create(vals)
            print(f"  Spec MAVI-07/{spec_ref.specification_id.name} CREADA")
        else:
            existe.write(vals)
            print(f"  Spec MAVI-07/{spec_ref.specification_id.name} actualizada")
    
    print(f"  Nombre: '{nombre}'")

# Códigos de reporte
print("\n── Códigos de reporte ──")
REFS_NEGATIVO = ('- ESPST-039\n'
                 '- Técnica de análisis TAST-039\n'
                 '- Inspección de Insumos PNOCC-002\n'
                 '- Método de muestreo de acuerdo a la Norma ANSI/ASQ Z1.4 PNOCC-005')
for codigo in ['STCON01', 'SPCNL04']:
    env.cr.execute("""
        UPDATE product_template SET
            report_document_code='RAST-039', report_version=4,
            report_effective_date='2025-08-01',
            certificate_document_code='CERST-039', certificate_version=4,
            certificate_effective_date='2025-08-01',
            report_references=%s
        WHERE default_code=%s
    """, (REFS_NEGATIVO, codigo))
    print(f"  {codigo}: {env.cr.rowcount} fila(s)")

env.cr.commit()
print("\n✓ STCON01 y SPCNL04 configurados correctamente.")
