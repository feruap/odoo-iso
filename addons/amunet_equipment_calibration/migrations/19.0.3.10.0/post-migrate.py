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
