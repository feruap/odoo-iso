{
    'name': 'Amunet - Kiosco de Soluciones (PIN en tablet)',
    'version': '19.0.1.0.0',
    'summary': 'Tablet compartida en el area de soluciones: el PIN identifica a quien elabora',
    'description': """
Kiosco de soluciones
====================

En el area de soluciones hay tablets compartidas. La sesion de Odoo en la tablet
es de un usuario OPERATIVO del area, no de una persona. Este modulo hace que el
PIN IDENTIFIQUE a quien elabora, para que el expediente registre a la persona
real y no a la tablet.

Distincion clave:
  - PIN de IDENTIFICACION ("quien eres"): solo hace falta en dispositivo
    compartido. Desde el telefono propio NO se pide: la sesion ya identifica.
  - PIN de FIRMA ("confirmas que tu lo haces"): siempre, en cualquier
    dispositivo. Enviar a supervision, solicitar analisis y producir.

Reglas de la sesion de trabajo:
  - Una sesion por elaboracion (no por turno).
  - Se cierra sola por inactividad (10 min por defecto, parametrizable).
  - Se cierra al enviar a supervision.
  - Si otra persona pone su PIN, la anterior se cierra (relevo).
  - Solo puede firmar quien tiene abierta la elaboracion.
  - Un PIN que coincida con MAS DE UNA persona se rechaza: el expediente no
    puede quedar con firma ambigua.

ACOTADO A SOLUCIONES: no toca amunet.generic.signature.wizard ni el flujo de
firmas de Calidad, que siguen validando el PIN contra el usuario de la sesion.
""",
    'author': 'Amunet',
    'category': 'Manufacturing',
    'license': 'LGPL-3',
    'depends': ['amunet_production', 'amunet_quality', 'amunet_process_inspection', 'mrp'],
    'data': [
        'security/amunet_soluciones_kiosco_security.xml',
        'security/ir.model.access.csv',
        'data/ir_config_parameter.xml',
        'data/ir_cron.xml',
        'views/amunet_kiosco_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
