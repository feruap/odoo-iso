# -*- coding: utf-8 -*-
from . import models


def post_init_hook(env):
    """Pre-llena el numero de tarjeta de los empleados ya conocidos del N3000.
    Clave = ID de empleado en Odoo, valor = numero de tarjeta."""
    cards = {
        202: '1014',       191: '1508161018', 193: '201191019',  197: '1011211020',
        194: '1711221021', 196: '2905201022', 195: '2905201023', 201: '1110211024',
        199: '1705231025', 200: '1105231026', 198: '1911221027', 203: '1011231028',
        204: '2002241030', 207: '2608241032', 209: '1803241034', 214: '2112241035',
        213: '1601251036', 216: '2805201038', 215: '3005251039', 192: '1004181041',
        219: '2605251043', 211: '2709241046', 208: '1403241049', 228: '1510241057',
        220: '2603261064',
    }
    Emp = env['hr.employee']
    for emp_id, card in cards.items():
        emp = Emp.browse(emp_id)
        if emp.exists() and not emp.n3000_card_no:
            emp.n3000_card_no = card
