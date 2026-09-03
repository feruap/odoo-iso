# -*- coding: utf-8 -*-
"""Asigna estaciones (puesto de piso) al equipo de Alondra.
Fuente: Actividades_Produccion.xlsx (RRHH, 3-sep-2026) + organigrama Odoo.
Uso: odoo shell -d <db> < asignar_puestos_20260903.py
"""
WC = {c: env['mrp.workcenter'].search([('code', '=', c)], limit=1) for c in
      ('SOL', 'LSC', 'ENC', 'AC1', 'AC2', 'PROD')}
assert all(WC.values()), 'faltan estaciones: %s' % [c for c, w in WC.items() if not w]
PUESTOS = {
    # correo de trabajo : estaciones
    'produccionsub@amunet.com.mx': ['SOL', 'LSC', 'ENC', 'AC1', 'AC2', 'PROD'],  # Alondra
    'soluciones@amunet.com.mx':    ['SOL', 'LSC'],                                # Julissa
    's.produccion@amunet.com.mx':  ['LSC', 'ENC', 'AC1', 'AC2'],                  # Alma
    'operador1@amunet.com.mx':     ['LSC', 'ENC', 'AC1', 'AC2'],                  # Ivonne
    'operador2@amunet.com.mx':     ['LSC', 'ENC', 'AC1', 'AC2'],                  # Kimberlin
    'practicante.sol@amunet.com.mx': ['SOL'],                                     # Practicantes Soluciones
}
POR_NOMBRE = {'Gema Medina': ['SOL']}
Emp = env['hr.employee']
for mail, codes in PUESTOS.items():
    e = Emp.search([('work_email', '=', mail)], limit=1)
    if not e:
        print('NO ENCONTRADO', mail); continue
    e.amunet_mi_workcenter_ids = [(6, 0, [WC[c].id for c in codes])]
    print('OK', e.name, '->', codes)
for nombre, codes in POR_NOMBRE.items():
    e = Emp.search([('name', 'ilike', nombre)], limit=1)
    if not e:
        print('NO ENCONTRADO', nombre); continue
    e.amunet_mi_workcenter_ids = [(6, 0, [WC[c].id for c in codes])]
    print('OK', e.name, '->', codes)
env.cr.commit()
