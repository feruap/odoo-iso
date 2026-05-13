# -*- coding: utf-8 -*-
from odoo.exceptions import UserError as _DemoGuardError

ALLOWED_DB = "Amunet_testing"
if env.cr.dbname != ALLOWED_DB:
    raise _DemoGuardError(
        "SCRIPT DEMO: solo se ejecuta en BD %r. BD actual: %r. Abortado." % (
            ALLOWED_DB, env.cr.dbname
        )
    )


BOM_ID = 3

# (sequence, name, wc_code, time_minutes_for_2000pcs, components_consumed_here)
OPERATIONS = [
    (10, 'Pesar y preparar reactivos',                'WC-PESAJE',     60),
    (20, 'Pretratar y secar almohadillas',            'WC-PRETRAT',   120),
    (30, 'Laminar membrana en hoja maestra',          'WC-LAMINADO',   90),
    (40, 'Cortar hoja laminada',                      'WC-CORTE-HOJA', 60),
    (50, 'Cortar tiras',                              'WC-CORTE-TIRA', 90),
    (60, 'Ensamblar cassette',                        'WC-ENSAMBLE',  240),
    (70, 'Empaque primario - sellar pouch',           'WC-EMPAQ-PRIM',180),
    (80, 'Empaque secundario - etiquetado y caja',    'WC-EMPAQ-SEC',  90),
]

# componente -> indice de OPERATIONS donde se consume (0-based)
COMPONENT_TO_OP = {
    'SPHMT06':  2,  # se vuelve hoja maestra al laminar
    'MPMNC01':  2,  # membrana se lamina aqui
    'SPALMA08': 1,  # pretratamiento
    'SPALMA01': 1,  # pretratamiento
    'MPAAB01':  5,  # ensamble
    'MPAFV01':  5,  # ensamble
    'MPCAR65':  5,  # cassette en ensamble
    'MPBOL01':  6,  # empaque primario
    'STDSC01':  6,  # empaque primario
    'MICAJ10':  7,  # empaque secundario
}

def log(m): print('[ROUTE]', m)

bom = env['mrp.bom'].browse(BOM_ID)
log('BOM: %s code=%s' % (bom.id, bom.code))

# mrp.routing.workcenter
RW = env['mrp.routing.workcenter']
created_ops = {}  # idx -> rw record

# borrar operaciones previas si las hay (para idempotencia)
existing_ops = RW.search([('bom_id','=', BOM_ID)])
if existing_ops:
    log('Operaciones previas: %s. Borrando para recrear limpio.' % len(existing_ops))
    # primero desligar bom_lines
    for ln in bom.bom_line_ids:
        if ln.operation_id and ln.operation_id.id in existing_ops.ids:
            ln.operation_id = False
    existing_ops.unlink()

for idx, (seq, name, wc_code, time_min) in enumerate(OPERATIONS):
    wc = env['mrp.workcenter'].search([('code','=', wc_code)], limit=1)
    if not wc:
        raise Exception('WC %s no encontrado' % wc_code)
    op = RW.create({
        'bom_id': BOM_ID,
        'workcenter_id': wc.id,
        'name': name,
        'sequence': seq,
        'time_mode': 'manual',
        'time_cycle_manual': float(time_min),
        'company_id': env.company.id,
    })
    created_ops[idx] = op
    log('Op %s -> %s @ %s = %s min, op_id=%s' % (seq, name, wc_code, time_min, op.id))

# Ligar bom_lines a operations
for ln in bom.bom_line_ids:
    code = ln.product_id.default_code
    if code in COMPONENT_TO_OP:
        op_idx = COMPONENT_TO_OP[code]
        ln.operation_id = created_ops[op_idx].id
        log('  bom_line %s -> op %s (%s)' % (
            code, created_ops[op_idx].id, OPERATIONS[op_idx][1]))

env.cr.commit()
log('--- Resumen ---')
for op in RW.search([('bom_id','=', BOM_ID)], order='sequence'):
    bl_count = env['mrp.bom.line'].search_count([('bom_id','=', BOM_ID),('operation_id','=', op.id)])
    log(' op_id=%s seq=%s name=%s wc=%s time=%s min, bom_lines=%s' % (
        op.id, op.sequence, op.name, op.workcenter_id.code, op.time_cycle_manual, bl_count
    ))

print('TOTAL_OPS=%s' % len(created_ops))
