# -*- coding: utf-8 -*-

PROCESS_EQUIPMENT_SERIALS = [
    'PRO/AGI/02', 'PRO/AGO/01', 'PRO/AMO/01', 'PRO/BAL/01',
    'PRO/CEN/02', 'CAL/CGR/01', 'EST/CLI/01', 'PRO/COH/01',
    'PRO/COT/01', 'PRO/ESP/01', 'PRO/HOR/01', 'PRO/HOR/02',
    'PRO/HOR/03', 'PRO/IMP/01', 'PRO/INY/01', 'ALM/REF/01',
    'PRO/SEC/01', 'PRO/SEL/01',
]


def post_init_hook(env):
    Equipment = env['amunet.equipment']
    Expediente = env['amunet.equipment.expediente']
    Calificacion = env['amunet.equipment.calificacion']

    for serial in PROCESS_EQUIPMENT_SERIALS:
        eq = Equipment.search([('serial_number', '=', serial)], limit=1)
        if not eq:
            continue
        existing = Expediente.search([('equipment_id', '=', eq.id)], limit=1)
        if existing:
            continue
        exp = Expediente.create({'equipment_id': eq.id})
        for qual_type in ('cd', 'ci', 'co', 'ce'):
            Calificacion.create({
                'expediente_id': exp.id,
                'qual_type': qual_type,
                'result': 'pendiente',
            })
