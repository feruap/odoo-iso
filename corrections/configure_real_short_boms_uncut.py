# -*- coding: utf-8 -*-
"""Configure real short-route uncut-sheet BoMs.

Base rule supplied by Amunet:
- 1 uncut sheet makes 70 rapid tests.
- Uncut sheets are stocked in Odoo as 30 cm per sheet.
- Piece components consume 70 units per 70 finished tests.
"""

BASE_QTY = 70.0
SHEET_CM = 30.0

BOMS = {
    'DMADB01': {
        'name': 'ANTIDOPING 5 PARAMETROS SALIVA',
        'components': [
            ('SPHMC53', 'hoja', 'corte'),
            ('SPHMC54', 'hoja', 'corte'),
            ('MPCAR53', 'pieza', 'ensamble'),
            ('STDSC01', 'pieza', 'empaque'),
            ('MPBOL04', 'pieza', 'empaque'),
        ],
    },
    'DMADS01': {
        'name': 'ANTIDOPING 5 PARAMETROS SANGRE',
        'components': [
            ('SPHMC53', 'hoja', 'corte'),
            ('SPHMC54', 'hoja', 'corte'),
            ('MPCAC08', 'pieza', 'ensamble'),
            ('STDSC01', 'pieza', 'empaque'),
            ('MPBOL01', 'pieza', 'empaque'),
            ('STGOT06', 'pieza', 'ensamble'),
            ('STBPR01', 'pieza', 'ensamble'),
        ],
    },
    'DMIGE01': {
        'name': 'IgE',
        'components': [
            ('SPHMC50', 'hoja', 'corte'),
            ('MPCAR50', 'pieza', 'ensamble'),
            ('STDSC01', 'pieza', 'empaque'),
            ('MPBOL01', 'pieza', 'empaque'),
            ('STGOT04', 'pieza', 'ensamble'),
            ('STBPR01', 'pieza', 'ensamble'),
        ],
    },
}

Product = env['product.product'].sudo()
Bom = env['mrp.bom'].sudo()
Operation = env['mrp.routing.workcenter'].sudo()
BomLine = env['mrp.bom.line'].sudo()
Workcenter = env['mrp.workcenter'].sudo()
Category = env['product.category'].sudo()

unit_uom = env.ref('uom.product_uom_unit')
finished_category = Category.search([
    ('complete_name', '=', 'Producto terminado / Pruebas rápidas inmunológicas')
], limit=1)
if not finished_category:
    dmads = Product.search([('default_code', '=', 'DMADS01')], limit=1)
    finished_category = dmads.product_tmpl_id.categ_id
if not finished_category:
    raise Exception('No encontre categoria de producto terminado inmunologico')

def _find_workcenter(primary_code, fallback_codes, fallback_names):
    workcenter = Workcenter.search([('code', '=', primary_code)], limit=1)
    if workcenter:
        return workcenter
    for code in fallback_codes:
        workcenter = Workcenter.search([('code', '=', code)], limit=1)
        if workcenter:
            return workcenter
    for name in fallback_names:
        workcenter = Workcenter.search([('name', 'ilike', name)], limit=1)
        if workcenter:
            return workcenter
    return Workcenter.browse()


workcenters = {
    'corte': _find_workcenter('WC-CORTE-TIRA', ['LAM', 'PROD'], ['Corte', 'Laminad']),
    'ensamble': _find_workcenter('WC-ENSAMBLE', ['PROD'], ['Ensamble', 'Produccion']),
    'control': _find_workcenter('WC-CONTROL-PROCESO', ['CC', 'PROD'], ['Control de Calidad']),
    'empaque': _find_workcenter('WC-EMPAQ-PRIM', ['PROD', 'APT'], ['Empaque', 'Acondicionado']),
}
missing_wc = [key for key, wc in workcenters.items() if not wc]
if missing_wc:
    raise Exception('Faltan work centers: %s' % ', '.join(missing_wc))

ops_template = [
    ('corte', 'Corte de hojas maestras compradas', 10, 55),
    ('ensamble', 'Ensamble de cassette', 20, 120),
    ('control', 'Control en proceso lateral flow', 30, 40),
    ('empaque', 'Empaque y etiquetado', 40, 70),
]

for final_code, spec in BOMS.items():
    final_product = Product.search([('default_code', '=', final_code)], limit=1)
    if not final_product:
        raise Exception('No existe producto final %s' % final_code)

    tmpl = final_product.product_tmpl_id
    tmpl.write({
        'tracking': 'lot',
        'categ_id': finished_category.id,
        'qc_required': True,
        'amunet_req_quality_control': True,
        'qc_test_destructiveness': 'non_destructive',
    })

    bom_code = 'RUTA-CORTA-UNCUT-70-%s' % final_code
    bom = Bom.search([('code', '=', bom_code)], limit=1)
    if not bom:
        bom = Bom.create({
            'code': bom_code,
            'product_tmpl_id': tmpl.id,
            'product_qty': BASE_QTY,
            'product_uom_id': unit_uom.id,
            'type': 'normal',
        })
    else:
        bom.write({
            'product_tmpl_id': tmpl.id,
            'product_qty': BASE_QTY,
            'product_uom_id': unit_uom.id,
            'type': 'normal',
        })

    op_by_key = {}
    for key, op_name, sequence, minutes in ops_template:
        full_name = '%s - %s' % (op_name, spec['name'])
        operation = bom.operation_ids.filtered(lambda op: op.sequence == sequence)[:1]
        vals = {
            'bom_id': bom.id,
            'name': full_name,
            'sequence': sequence,
            'workcenter_id': workcenters[key].id,
            'time_cycle_manual': minutes,
        }
        if operation:
            operation.write(vals)
        else:
            operation = Operation.create(vals)
        op_by_key[key] = operation

    expected_product_ids = set()
    for comp_code, presentation, op_key in spec['components']:
        comp = Product.search([('default_code', '=', comp_code)], limit=1)
        if not comp:
            raise Exception('No existe componente %s para %s' % (comp_code, final_code))
        expected_product_ids.add(comp.id)
        qty = SHEET_CM if presentation.lower() == 'hoja' else BASE_QTY
        vals = {
            'bom_id': bom.id,
            'product_id': comp.id,
            'product_qty': qty,
            'product_uom_id': comp.uom_id.id,
            'operation_id': op_by_key[op_key].id,
        }
        line = bom.bom_line_ids.filtered(lambda bom_line: bom_line.product_id.id == comp.id)[:1]
        if line:
            line.write(vals)
        else:
            BomLine.create(vals)

    extras = bom.bom_line_ids.filtered(lambda line: line.product_id.id not in expected_product_ids)
    if extras:
        print('REAL_SHORT_BOM_EXTRA_LINES %s %s' % (
            final_code,
            ','.join(extras.mapped('product_id.default_code')),
        ))

    print('REAL_SHORT_BOM_CONFIGURED %s %s' % (final_code, bom_code))

env.cr.commit()
print('REAL_SHORT_BOMS_COMMIT_OK')
