"""
Activar y configurar STCON01 (id=1006) y SPCNL04 (id=1814) en producción.

El script anterior (20260901_calidad_stcnl_specs.py) los omitió porque
ProdTmpl.search() sin active_test=False no devuelve inactivos.

- STCON01: reactivar + limpiar params incorrectos (MAVI-04/VAMA-078/VAMA-114)
           + agregar MAVI-20 y MAVI-07 negativo.
- SPCNL04: reactivar + agregar MAVI-20 y MAVI-07 negativo.

Autorizado por Diana Flores, 2026-09-02.
"""
import json

ProdTmpl = env['product.template']
Param    = env['amunet.quality.check.parameter']
Rel      = env['amunet.quality.parameter.product.rel']
SpecConf = env['amunet.quality.parameter.specification.config']
SpecBase = env['amunet.quality.check.parameter.specification']

# Tomar el mapping de MAVI-07 negativo del STCNL01 ya configurado (id=1811)
param_mavi07 = Param.search([('code', '=', 'MAVI-07')], limit=1)
param_mavi20 = Param.search([('code', '=', 'MAVI-20')], limit=1)

# Obtener mappings del STCNL01 ya correcto
tmpl_stcnl01 = ProdTmpl.browse(1811)
rel_stcnl01_mavi07 = Rel.search([
    ('product_tmpl_id', '=', 1811),
    ('parameter_id', '=', param_mavi07.id),
], limit=1)
rel_stcnl01_mavi20 = Rel.search([
    ('product_tmpl_id', '=', 1811),
    ('parameter_id', '=', param_mavi20.id),
], limit=1)

# Obtener los spec configs correctos del STCNL01 como referencia
specs_mavi07 = SpecConf.with_context(active_test=False).search([
    ('product_parameter_rel_id', '=', rel_stcnl01_mavi07.id),
    ('active', '=', True),
])
specs_mavi20 = SpecConf.with_context(active_test=False).search([
    ('product_parameter_rel_id', '=', rel_stcnl01_mavi20.id),
    ('active', '=', True),
])

print(f"MAVI-07 specs en STCNL01: {len(specs_mavi07)}")
print(f"MAVI-20 specs en STCNL01: {len(specs_mavi20)}")

env = env(context=dict(env.context, amunet_alta_autorizada=True))

for tmpl_id, codigo, nombre in [(1006, 'STCON01', 'Control negativo'), (1814, 'SPCNL04', 'Control Negativo VPH')]:
    print(f"\n── {codigo} (id={tmpl_id}) ──")
    tmpl = ProdTmpl.with_context(active_test=False).browse(tmpl_id)
    
    # 1. Reactivar
    if not tmpl.active:
        tmpl.write({'active': True})
        print(f"  Reactivado.")
    
    # 2. Limpiar relaciones de parámetros incorrectos
    rels_actuales = Rel.search([('product_tmpl_id', '=', tmpl_id)])
    for r in rels_actuales:
        if r.parameter_id.code not in ('MAVI-20', 'MAVI-07'):
            print(f"  Eliminando rel {r.parameter_id.code} ...")
            # Desactivar specs primero
            SpecConf.with_context(active_test=False).search([
                ('product_parameter_rel_id', '=', r.id)
            ]).write({'active': False})
            r.unlink()
    
    # 3. Agregar/verificar MAVI-20
    rel_m20 = Rel.search([('product_tmpl_id', '=', tmpl_id), ('parameter_id', '=', param_mavi20.id)], limit=1)
    if not rel_m20:
        rel_m20 = Rel.create({'product_tmpl_id': tmpl_id, 'parameter_id': param_mavi20.id})
        print(f"  Rel MAVI-20 creada.")
    # Copiar specs de STCNL01
    for spec_ref in specs_mavi20:
        existe = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', rel_m20.id),
            ('specification_id', '=', spec_ref.specification_id.id),
        ], limit=1)
        if not existe:
            SpecConf.create({
                'product_parameter_rel_id': rel_m20.id,
                'specification_id': spec_ref.specification_id.id,
                'active': True,
                'evaluation_type': spec_ref.evaluation_type,
                'acceptance_criteria': spec_ref.acceptance_criteria,
                'text_phrase_mapping': spec_ref.text_phrase_mapping,
            })
            print(f"  Spec MAVI-20/{spec_ref.specification_id.name} creada.")
        else:
            existe.write({
                'active': True,
                'evaluation_type': spec_ref.evaluation_type,
                'acceptance_criteria': spec_ref.acceptance_criteria,
                'text_phrase_mapping': spec_ref.text_phrase_mapping,
            })
            print(f"  Spec MAVI-20/{spec_ref.specification_id.name} actualizada.")
    
    # 4. Agregar/verificar MAVI-07
    rel_m07 = Rel.search([('product_tmpl_id', '=', tmpl_id), ('parameter_id', '=', param_mavi07.id)], limit=1)
    if not rel_m07:
        rel_m07 = Rel.create({'product_tmpl_id': tmpl_id, 'parameter_id': param_mavi07.id})
        print(f"  Rel MAVI-07 creada.")
    for spec_ref in specs_mavi07:
        existe = SpecConf.with_context(active_test=False).search([
            ('product_parameter_rel_id', '=', rel_m07.id),
            ('specification_id', '=', spec_ref.specification_id.id),
        ], limit=1)
        if not existe:
            SpecConf.create({
                'product_parameter_rel_id': rel_m07.id,
                'specification_id': spec_ref.specification_id.id,
                'active': True,
                'evaluation_type': spec_ref.evaluation_type,
                'acceptance_criteria': spec_ref.acceptance_criteria,
                'text_phrase_mapping': spec_ref.text_phrase_mapping,
            })
            print(f"  Spec MAVI-07/{spec_ref.specification_id.name} creada.")
        else:
            existe.write({
                'active': True,
                'evaluation_type': spec_ref.evaluation_type,
                'acceptance_criteria': spec_ref.acceptance_criteria,
                'text_phrase_mapping': spec_ref.text_phrase_mapping,
            })
            print(f"  Spec MAVI-07/{spec_ref.specification_id.name} actualizada.")

    # 5. Aplicar nombre correcto
    tmpl.write({'name': nombre})
    print(f"  Nombre: '{nombre}'")

# Aplicar códigos de reporte a STCON01 y SPCNL04
print("\n── Códigos de reporte STCON01/SPCNL04 ──")
REFS_NEGATIVO = ('- ESPST-039\n'
                 '- Técnica de análisis TAST-039\n'
                 '- Inspección de Insumos PNOCC-002\n'
                 '- Método de muestreo de acuerdo a la Norma ANSI/ASQ Z1.4 PNOCC-005')
for codigo in ['STCON01', 'SPCNL04']:
    env.cr.execute("""
        UPDATE product_template SET
            report_document_code       = 'RAST-039',
            report_version             = 4,
            report_effective_date      = '2025-08-01',
            certificate_document_code  = 'CERST-039',
            certificate_version        = 4,
            certificate_effective_date = '2025-08-01',
            report_references          = %s
        WHERE default_code = %s
    """, (REFS_NEGATIVO, codigo))
    print(f"  {codigo}: {env.cr.rowcount} fila(s) actualizadas")

env.cr.commit()
print("\n✓ STCON01 y SPCNL04 activados y configurados.")
