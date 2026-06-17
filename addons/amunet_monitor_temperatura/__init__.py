from . import models
from . import wizards


def post_init_hook(env):
    """Crea las 12 areas de monitoreo ligadas a su departamento (por nombre).
    Idempotente: no duplica si ya existe el codigo."""
    Area = env['amunet.temp.area']
    Dept = env['hr.department']

    def dept(name):
        return Dept.search([('name', '=', name)], limit=1)

    H3 = [9.0, 13.0, 18.0]
    H2 = [9.0, 18.0]
    # (codigo, nombre, departamento responsable, pool, horarios)
    cfg = [
        ('TMP-ALMMP', 'Almacen Materia Prima', 'Almacén Materia Prima', False, H3),
        ('TMP-ALMPT', 'Almacen Producto Terminado', 'Almacén de Producto Terminado', False, H3),
        ('TMP-ALMTPT', 'Almacen Temporal PT', 'Producción', True, H3),
        ('TMP-EST', 'Estabilidad', 'Control de Calidad', False, H3),
        ('TMP-CC', 'Control de Calidad', 'Control de Calidad', False, H2),
        ('TMP-LSC', 'Laminado, Secado y Corte', 'Producción', True, H2),
        ('TMP-ENC', 'Encartuchado', 'Producción', True, H2),
        ('TMP-AC1', 'Acondicionado 1', 'Producción', True, H2),
        ('TMP-AC2', 'Acondicionado 2', 'Producción', True, H2),
        ('TMP-SOL', 'Soluciones', 'Producción', True, H2),
        ('TMP-INY', 'Inyeccion', 'Producción', True, H2),
    ]
    seq = 10
    for code, name, dname, pool, horas in cfg:
        if Area.search([('code', '=', code)], limit=1):
            continue
        d = dept(dname)
        if not d:
            continue
        Area.create({
            'code': code,
            'name': name,
            'sequence': seq,
            'responsible_department_id': d.id,
            'capture_pool': pool,
            'temp_min': 15.0, 'temp_max': 30.0,
            'hum_required': True, 'hum_min': 0.0, 'hum_max': 65.0,
            'tolerance_minutes': 15,
            'slot_ids': [(0, 0, {'time_hour': h}) for h in horas],
        })
        seq += 10
