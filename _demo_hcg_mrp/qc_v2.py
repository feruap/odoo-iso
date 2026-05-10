# -*- coding: utf-8 -*-
from datetime import date
from markupsafe import Markup

DEMO_TAG = 'DEMO-MRP-HCG-2000-20260510-V2'
TODAY = date(2026, 5, 10)
EXPIRY = date(2028, 5, 10)
QC_NAME = 'DEMO/QC/MRP/HCG/2000/20260510-V2'
ANALYSIS_NUMBER = 'DEMO-AN-MRP-HCG-20260510-002'

ANALYST_LOGIN = 'analista1cc@amunet.com.mx'
SUPERVISOR_LOGIN = 's.controldecalidad@amunet.com.mx'
SANITARY_LOGIN = 'desarrollo@amunet.com.mx'

def log(m): print('[QC-V2]', m)

def by_user(login):
    return env['res.users'].search([('login','=',login),('active','=',True)], limit=1)

def by_serial(s):
    return env['amunet.equipment'].search([('serial_number','=',s)], limit=1)

final_lot = env['stock.lot'].search([('name','=', DEMO_TAG)], limit=1)
final_product = final_lot.product_id

users = {
    'analyst': by_user(ANALYST_LOGIN),
    'supervisor': by_user(SUPERVISOR_LOGIN),
    'sanitary': by_user(SANITARY_LOGIN),
}
equipment = {
    'micrometer': by_serial('CAL/MIE/01'),
    'timer': by_serial('CAL/CNM/01'),
    'pipette': by_serial('CAL/MIC/02'),
    'lamp_qc': by_serial('CAL/LMP/01'),
}

mo = env['mrp.production'].search([('origin','=', DEMO_TAG)], limit=1)
log('MO ligada: %s id=%s state=%s' % (mo.name, mo.id, mo.state))

qc = env['amunet.quality.check'].search([
    ('lot_id','=', final_lot.id),
    ('name','=', QC_NAME),
], limit=1)
if qc:
    log('QC V2 ya existia: id=%s' % qc.id)
else:
    notes = (
        '%s\n'
        'Liberado a partir de orden de fabricacion nativa MRP V2 %s (id=%s).\n'
        'BOM con routing de 8 operaciones; raws done con qty correcta (sin skip_consumption).'
    ) % (DEMO_TAG, mo.name, mo.id)

    qc = env['amunet.quality.check'].create({
        'name': QC_NAME,
        'product_id': final_product.id,
        'lot_id': final_lot.id,
        'manufacturing_date': TODAY,
        'expiration_date': EXPIRY,
        'analysis_date': TODAY,
        'qty_sampling': 80,
        'qty_analyzed': 80,
        'qty_to_return': 0,
        'original_qty_received': 2000,
        'sampling_uom_id': final_product.uom_id.id,
        'info_reviewed': True,
        'sampling_confirmed': True,
        'anexos_text': notes,
    })
    log('QC creado: id=%s' % qc.id)

    checks = [
        ('MAVI-04','Apariencia de empaque y cartucho',equipment['lamp_qc'],
         'Muestra sin dano, cartucho cerrado y ventana limpia.','binary'),
        ('EXT-A','Ancho de tira laminada',equipment['micrometer'],
         'Ancho objetivo 4.00 mm; n=10 dentro de 3.8-4.2 mm.','numeric'),
        ('VAMA-034','Visualizacion de linea control y linea prueba',equipment['timer'],
         'Control positivo hCG: lineas C y T visibles.','binary'),
        ('VAMA-113','Funcionalidad del control positivo',equipment['pipette'],
         'Control positivo 25 mIU/mL reactivo y valido.','binary'),
        ('VAMA-114','Funcionalidad del control negativo',equipment['pipette'],
         'Control negativo sin linea T; linea C visible.','binary'),
        ('MAVI-09','Tiempo de flujo capilar',equipment['timer'],
         'Flujo completo entre 4 y 5 minutos.','numeric_time'),
        ('VAMA-064','Etiqueta y empaque secundario',equipment['lamp_qc'],
         'Lote, caducidad, IFU demo y caja HCG correctos.','binary'),
    ]
    Param = env['amunet.quality.check.parameter']
    Line = env['amunet.quality.test.line']
    Detail = env['amunet.quality.test.line.detail']

    for seq, (code, title, eq, criteria, kind) in enumerate(checks, start=1):
        param = Param.search([('code','=', code),('active','=', True)], limit=1)
        line = Line.create({
            'check_id': qc.id,
            'parameter_id': param.id if param else False,
            'name': title,
            'sequence': seq * 10,
            'equipment_id': eq.id,
            'result_notes': '%s | %s (%s)' % (DEMO_TAG, eq.name, eq.serial_number),
        })
        if kind == 'numeric':
            Detail.create({'test_line_id': line.id, 'name': 'Ancho de tira',
                'acceptance_criteria': criteria, 'evaluation_type': 'numeric_range',
                'min_value': 3.8, 'max_value': 4.2, 'result_numeric': 4.02, 'result_numeric_filled': True})
        elif kind == 'numeric_time':
            Detail.create({'test_line_id': line.id, 'name': 'Tiempo de flujo',
                'acceptance_criteria': criteria, 'evaluation_type': 'numeric_range',
                'min_value': 4.0, 'max_value': 5.0, 'result_numeric': 4.5, 'result_numeric_filled': True})
        else:
            Detail.create({'test_line_id': line.id, 'name': title,
                'acceptance_criteria': criteria, 'evaluation_type': 'binary_selection',
                'binary_option_pass': 'Cumple', 'binary_option_fail': 'No cumple',
                'result_selection': 'Cumple'})

    for d in qc.test_line_ids.mapped('detail_line_ids'):
        d._compute_verdict()
        d._compute_result_display()
    for ln in qc.test_line_ids:
        ln._compute_detail_counts()
        ln._compute_verdict()
        ln._compute_verdict_summary()
    qc._compute_global_result()
    qc._compute_parameter_counts()
    qc._compute_progress()

    qc.write({
        'analysis_number': ANALYSIS_NUMBER,
        'user_realized_id': users['analyst'].id,
        'user_verified_id': users['supervisor'].id,
        'user_authorized_id': users['sanitary'].id,
        'state': 'done',
        'change_reason': '%s | QC DEMO sobre MO V2 con routing y consumo trazable' % DEMO_TAG,
    })

    Audit = env['amunet.quality.audit.log'].sudo()
    for sig, user in [('realized', users['analyst']), ('verified', users['supervisor']), ('authorized', users['sanitary'])]:
        Audit.create({
            'model_name': 'amunet.quality.check',
            'res_id': qc.id, 'res_name': qc.name,
            'field_name': 'signature_%s' % sig,
            'old_value': 'N/A',
            'new_value': 'Firma DEMO V2 %s por %s' % (sig, user.login),
            'justification': '%s | QC V2 con MO MRP completa' % DEMO_TAG,
            'user_id': user.id,
        })

    log('QC %s finalizado: state=%s result=%s' % (qc.name, qc.state, qc.global_result))


# Liberar DHR
if final_lot.amunet_lot_release_state != 'released':
    final_lot.with_user(users['sanitary'])._action_release_lot(
        notes=('%s | Liberacion DHR sobre MO MRP V2 con routing y consumo trazable.\n'
               'BOM 3 + 8 operaciones + raws DEMO consumidos done. '
               'MO: %s (id=%s). QC: %s (id=%s).') % (DEMO_TAG, mo.name, mo.id, qc.name, qc.id)
    )
    log('Liberado: hash=%s' % final_lot.amunet_lot_release_hash)
else:
    log('Ya liberado: hash=%s' % final_lot.amunet_lot_release_hash)

env.cr.commit()
print('QC_V2_ID=%s' % qc.id)
print('QC_V2_NAME=%s' % qc.name)
print('QC_V2_STATE=%s' % qc.state)
print('QC_V2_RESULT=%s' % qc.global_result)
print('LOT_V2_ID=%s' % final_lot.id)
print('LOT_V2_RELEASE=%s' % final_lot.amunet_lot_release_state)
print('LOT_V2_HASH=%s' % final_lot.amunet_lot_release_hash)
