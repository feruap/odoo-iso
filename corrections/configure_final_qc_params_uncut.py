# -*- coding: utf-8 -*-
"""Configure finished-product QC parameters for short-route lateral flow products.

This links existing MAVIS/VAMA parameters to finished products. It does not
modify global parameter definitions; any product-specific wording is written
only on the product's specification configuration.
"""

COMMON_PARAMS = [
    ('MAVI-04', 'Aspectos Visuales'),
    ('MAVI-07', 'Visualización de líneas “resultado base”'),
    ('MAVI-09', 'Desempeño del tiempo de flujo capilar'),
    ('VAMA-034', 'Visualización de líneas de control y prueba'),
    ('VAMA-064', 'Información de etiqueta de empaque'),
    ('VAMA-036', 'Información en material instructivo o apoyo para interpretación'),
    ('VAMA-091', 'Termosellado'),
]

ANTIDOPING_PARAMS = [
    ('MAVI-16', 'Visualización de líneas resultado en rango'),
]

BUFFER_GOTERO_PARAMS = [
    ('VAMA-038', 'Funcionalidad del gotero'),
    ('VAMA-096', 'Funcionalidad del vial y tamaño de gota'),
    ('VAMA-004', 'Partículas en solución'),
]

PRODUCT_PARAMS = {
    'DMADB01': COMMON_PARAMS + ANTIDOPING_PARAMS,
    'DMADS01': COMMON_PARAMS + ANTIDOPING_PARAMS + BUFFER_GOTERO_PARAMS,
    'DMIGE01': COMMON_PARAMS + BUFFER_GOTERO_PARAMS,
}

ANTIDOPING_CRITERIA = (
    'Producto terminado antidoping 5 parámetros: línea de control válida, '
    'flujo correcto, fondo limpio y resultado esperado para COC, THC, MET, AMP y OPI.'
)

IGE_CRITERIA = (
    'Producto terminado IgE: línea de control válida, flujo correcto, fondo limpio '
    'y resultado esperado conforme al panel IgE.'
)

Product = env['product.product'].sudo()
Parameter = env['amunet.quality.check.parameter'].sudo()
Rel = env['amunet.quality.parameter.product.rel'].sudo()


def _find_parameter(code, name):
    domain = [('code', '=', code), ('name', '=', name), ('active', '=', True)]
    params = Parameter.search(domain, order='id desc')
    if not params:
        raise Exception('No existe parametro %s / %s' % (code, name))
    return params[0]


def _upsert_rel(product_tmpl, parameter, sequence):
    rel = Rel.with_context(active_test=False).search([
        ('product_tmpl_id', '=', product_tmpl.id),
        ('parameter_id', '=', parameter.id),
    ], limit=1)
    vals = {
        'product_tmpl_id': product_tmpl.id,
        'parameter_id': parameter.id,
        'sequence': sequence,
        'active': True,
    }
    if rel:
        rel.write(vals)
        if not rel.specification_config_ids:
            rel._generate_specification_configs()
    else:
        rel = Rel.create(vals)
    return rel


def _apply_product_criteria(default_code, rel):
    if rel.parameter_code not in ('VAMA-034', 'MAVI-16'):
        return
    criteria = ANTIDOPING_CRITERIA if default_code in ('DMADB01', 'DMADS01') else IGE_CRITERIA
    rel.specification_config_ids.filtered(lambda cfg: cfg.active).write({
        'acceptance_criteria': criteria,
    })


for default_code, params in PRODUCT_PARAMS.items():
    product = Product.search([('default_code', '=', default_code)], limit=1)
    if not product:
        raise Exception('No existe producto final %s' % default_code)

    tmpl = product.product_tmpl_id
    tmpl.write({
        'qc_required': True,
        'amunet_req_quality_control': True,
        'qc_test_destructiveness': 'non_destructive',
        'tracking': 'lot',
    })

    for index, (code, name) in enumerate(params, start=1):
        parameter = _find_parameter(code, name)
        rel = _upsert_rel(tmpl, parameter, index * 10)
        _apply_product_criteria(default_code, rel)
        print('FINAL_QC_PARAM_SET %s %s %s %s' % (
            default_code,
            parameter.code,
            parameter.id,
            parameter.name,
        ))

env.cr.commit()
print('FINAL_QC_PARAMS_COMMIT_OK')
