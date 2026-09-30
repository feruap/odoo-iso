from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Asigna location_id a todos los equipos según su departamento."""
    env = api.Environment(cr, SUPERUSER_ID, {})

    mapping = {
        'SOLUCIONES':                             'ARU/PRO/Soluciones',
        'LECTURA Y PRETRATAMIENTO':               'ARU/PRO/Lectura y Pretratamiento',
        'INYECCIÓN':                              'ARU/PRO/Inyección',
        'LAMINADO, SECADO Y CORTE':               'ARU/PRO/Laminado, Secado y Corte',
        'ENCARTUCHADO':                           'ARU/PRO/Encartuchado',
        'ACONDICIONADO 1':                        'ARU/PRO/Acondicionado 1',
        'ACONDICIONADO 2':                        'ARU/PRO/Acondicionado 2',
        'ALMACÉN TEMPORAL DE PRODUCTO TERMINADO': 'ARU/PRO/Almacén Temporal de PT',
        'CONTROL DE CALIDAD':                     'ARU/CAL',
        'ESTABILIDAD':                            'ARU/EST',
        'VALIDACIÓN':                             'ARU/VAL',
        'ALMACÉN DE MATERIA PRIMA':               'ARU/ALM',
        'ALMACÉN DE PRODUCTO TERMINADO':          'ARU/ALP',
        'DESARROLLO':                             'ARU/Desarrollo',
    }

    for dept, complete_name in mapping.items():
        location = env['stock.location'].search([('complete_name', '=', complete_name)], limit=1)
        if not location:
            continue
        equipos = env['amunet.equipment'].search([('department', '=', dept)])
        equipos.write({'location_id': location.id})

    # Equipos de Desarrollo nuevos no entran al programa FVA-002
    # (los 12 con código DES/MIC/01-10, DES/FUE/01 y DES/TER/01 sí están en FVA-002)
    fva002_codes = [
        'DES/MIC/01', 'DES/MIC/02', 'DES/MIC/03', 'DES/MIC/04', 'DES/MIC/05',
        'DES/MIC/06', 'DES/MIC/07', 'DES/MIC/08', 'DES/MIC/09', 'DES/MIC/10',
        'DES/FUE/01', 'DES/TER/01',
    ]
    env['amunet.equipment'].search([
        ('department', '=', 'DESARROLLO'),
        ('serial_number', 'not in', fva002_codes),
    ]).write({'calibration_required': False})
