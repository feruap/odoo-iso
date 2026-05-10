# -*- coding: utf-8 -*-
from datetime import date
from markupsafe import Markup

DEMO_TAG = 'DEMO-MRP-HCG-2000-20260510'
TODAY = date(2026, 5, 10)
EXPIRY = date(2028, 5, 10)
QC_NAME = 'DEMO/QC/MRP/HCG/2000/20260510'
ANALYSIS_NUMBER = 'DEMO-AN-MRP-HCG-20260510-001'

ANALYST_LOGIN = 'analista1cc@amunet.com.mx'
SUPERVISOR_LOGIN = 's.controldecalidad@amunet.com.mx'
SANITARY_LOGIN = 'desarrollo@amunet.com.mx'


def log(m):
    print('[QC-DHR-MRP]', m)


def by_user(login):
    return env['res.users'].search([('login', '=', login), ('active', '=', True)], limit=1)


def by_serial(serial):
    return env['amunet.equipment'].search([('serial_number', '=', serial)], limit=1)


# Lote final de la MO
final_lot = env['stock.lot'].search([('name', '=', DEMO_TAG)], limit=1)
if not final_lot:
    raise Exception('No se encontro lote final %s' % DEMO_TAG)
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
for k, v in equipment.items():
    if not v:
        raise Exception('Equipo %s no encontrado' % k)

# La MO de mrp ligada
mo = env['mrp.production'].search([
    ('origin', '=', DEMO_TAG),
    ('product_id', '=', final_product.id),
], limit=1)
log('MO ligada: %s id=%s state=%s' % (mo.name, mo.id, mo.state))


# QC idempotente
qc = env['amunet.quality.check'].search([
    ('lot_id', '=', final_lot.id),
    ('name', '=', QC_NAME),
], limit=1)
if qc:
    log('QC ya existia: id=%s state=%s' % (qc.id, qc.state))
else:
    material_notes = (
        '%s\n'
        'Liberado a partir de orden de fabricacion nativa MRP %s (id=%s).\n'
        'BOM: DEMO-MRP-HCG-2000-20260510 (consumio lotes DEMO-* reales en stock).'
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
        'anexos_text': material_notes,
    })
    log('QC creado: id=%s' % qc.id)

    checks = [
        ('MAVI-04', 'Apariencia de empaque y cartucho', equipment['lamp_qc'],
         'Muestra sin dano, cartucho cerrado y ventana limpia.', 'binary'),
        ('EXT-A',   'Ancho de tira laminada', equipment['micrometer'],
         'Ancho objetivo 4.00 mm; n=10 dentro de 3.8-4.2 mm.', 'numeric'),
        ('VAMA-034','Visualizacion de linea control y linea prueba', equipment['timer'],
         'Control positivo hCG: lineas C y T visibles dentro del tiempo.', 'binary'),
        ('VAMA-113','Funcionalidad del control positivo', equipment['pipette'],
         'Control positivo 25 mIU/mL reactivo y valido.', 'binary'),
        ('VAMA-114','Funcionalidad del control negativo', equipment['pipette'],
         'Control negativo sin linea T; linea C visible.', 'binary'),
        ('MAVI-09', 'Tiempo de flujo capilar', equipment['timer'],
         'Flujo completo entre 4 y 5 minutos.', 'numeric_time'),
        ('VAMA-064','Etiqueta y empaque secundario', equipment['lamp_qc'],
         'Lote, caducidad, IFU demo y caja HCG correctos.', 'binary'),
    ]
    Param = env['amunet.quality.check.parameter']
    Line = env['amunet.quality.test.line']
    Detail = env['amunet.quality.test.line.detail']

    for seq, (code, title, eq, criteria, kind) in enumerate(checks, start=1):
        param = Param.search([('code', '=', code), ('active', '=', True)], limit=1)
        line = Line.create({
            'check_id': qc.id,
            'parameter_id': param.id if param else False,
            'name': title,
            'sequence': seq * 10,
            'equipment_id': eq.id,
            'result_notes': '%s | Equipo usado: %s (%s)' % (DEMO_TAG, eq.name, eq.serial_number),
        })
        if kind == 'numeric':
            Detail.create({
                'test_line_id': line.id,
                'name': 'Ancho de tira',
                'acceptance_criteria': criteria,
                'evaluation_type': 'numeric_range',
                'min_value': 3.8,
                'max_value': 4.2,
                'result_numeric': 4.01,
                'result_numeric_filled': True,
            })
        elif kind == 'numeric_time':
            Detail.create({
                'test_line_id': line.id,
                'name': 'Tiempo de flujo',
                'acceptance_criteria': criteria,
                'evaluation_type': 'numeric_range',
                'min_value': 4.0,
                'max_value': 5.0,
                'result_numeric': 4.6,
                'result_numeric_filled': True,
            })
        else:
            Detail.create({
                'test_line_id': line.id,
                'name': title,
                'acceptance_criteria': criteria,
                'evaluation_type': 'binary_selection',
                'binary_option_pass': 'Cumple',
                'binary_option_fail': 'No cumple',
                'result_selection': 'Cumple',
            })

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
        'change_reason': '%s | QC DEMO sobre orden MRP nativa' % DEMO_TAG,
    })

    Audit = env['amunet.quality.audit.log'].sudo()
    for sig, user in [
        ('realized', users['analyst']),
        ('verified', users['supervisor']),
        ('authorized', users['sanitary']),
    ]:
        Audit.create({
            'model_name': 'amunet.quality.check',
            'res_id': qc.id,
            'res_name': qc.name,
            'field_name': 'signature_%s' % sig,
            'old_value': 'N/A',
            'new_value': 'Firma DEMO %s por %s' % (sig, user.login),
            'justification': '%s | Firma demo precargada para escenario MRP en staging' % DEMO_TAG,
            'user_id': user.id,
        })

    if hasattr(qc, 'message_post'):
        qc.message_post(
            body=Markup('<b>QC DEMO sobre MO MRP nativa:</b> lote piloto hCG 2000.<br/>'
                        'Firmas: analista, supervisor, sanitario. Resultado: aprobado.'),
            message_type='notification',
        )
    log('QC finalizado: id=%s state=%s result=%s' % (qc.id, qc.state, qc.global_result))


# Liberar DHR del lote final (idempotente)
if final_lot.amunet_lot_release_state != 'released':
    final_lot.with_user(users['sanitary'])._action_release_lot(
        notes=(
            '%s | Liberacion DHR sobre orden MRP nativa.\n'
            'BOM: DEMO-MRP-HCG-2000-20260510 (id=%s).\n'
            'Manufacturing Order: %s (id=%s).\n'
            'QC: %s (id=%s).'
        ) % (DEMO_TAG, qc.lot_id.id, mo.name, mo.id, qc.name, qc.id)
    )
    log('Lote liberado: hash=%s state=%s' % (
        final_lot.amunet_lot_release_hash, final_lot.amunet_lot_release_state
    ))
else:
    log('Lote ya estaba liberado: hash=%s' % final_lot.amunet_lot_release_hash)

env.cr.commit()

print('QC_ID=%s' % qc.id)
print('QC_NAME=%s' % qc.name)
print('QC_STATE=%s' % qc.state)
print('QC_GLOBAL_RESULT=%s' % qc.global_result)
print('FINAL_LOT_ID=%s' % final_lot.id)
print('FINAL_LOT_NAME=%s' % final_lot.name)
print('FINAL_LOT_RELEASE_STATE=%s' % final_lot.amunet_lot_release_state)
print('FINAL_LOT_RELEASE_HASH=%s' % final_lot.amunet_lot_release_hash)
print('MO_ID=%s' % mo.id)
print('MO_NAME=%s' % mo.name)
