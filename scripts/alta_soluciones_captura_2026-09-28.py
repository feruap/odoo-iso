# -*- coding: utf-8 -*-
"""Alta de las soluciones de captura (lista de Mery, 28-sep-2026).

QUE SON. La solucion de captura es la que se imprime en la MEMBRANA en la
linea de laminado: es la linea de prueba. Cambia segun el analito que se
busca y segun el tipo de prueba, igual que el conjugado cambia por hoja.

Se dan de alta con los mismos atributos que el conjugado (SPCDE01), que es
su hermano de proceso: semiprocesado de linea, se fabrica, se guarda por
categoria en ARU, lote propio con prefijo de clave, no se compra ni se vende.

PENDIENTE DE MERY (no se inventa):
  - caducidad de cada una
  - si requieren analisis de Calidad por lote
  - receta (amortiguador + concentracion del anticuerpo)
Por eso quedan sin texto de caducidad y sin BoM.

Idempotente: si la clave ya existe, no la duplica.
"""

MODELO = 'SPCDE01'

SOLUCIONES = [
    ('SPSCA01', 'Solución de captura anti-influenza A'),
    ('SPSCA02', 'Solución de captura anti-influenza B'),
    ('SPSCA03', 'Solución de captura anti-THC'),
    ('SPSCA04', 'Solución de captura anti-COC'),
    ('SPSCA05', 'Solución de captura anti-AMP'),
    ('SPSCA06', 'Solución de captura anti-MET'),
    ('SPSCA07', 'Solución de captura anti-OPI'),
    ('SPSCA08', 'Solución de captura anti-biotina'),
    ('SPSCA09', 'Solución de captura anti-mioglobina'),
    ('SPSCA10', 'Solución de captura anti-CK-MB'),
    ('SPSCA11', 'Solución de captura anti-cTnI'),
    ('SPSCA12', 'Solución de captura anti-Chlamydia trachomatis'),
    ('SPSCA13', 'Solución de captura IgG anti-humano'),
    ('SPSCA14', 'Solución de captura IgM anti-humano'),
    ('SPSCA15', 'Solución de captura anti-proteína N'),
    ('SPSCA16', 'Solución de captura anti-NS1'),
    ('SPSCA17', 'Solución de captura anti-ALC'),
    ('SPSCA18', 'Solución de captura anti-ferritina'),
    ('SPSCA19', 'Solución de captura anti-hCG'),
    ('SPSCA20', 'Solución de captura anti-hemoglobina glicada'),
    ('SPSCA21', 'Solución de captura anti-PSA'),
    ('SPSCA22', 'Solución de captura anti-rotavirus'),
    ('SPSCA23', 'Solución de captura anti-adenovirus'),
    ('SPSCA24', 'Solución de captura anti-RSV'),
    ('SPSPC01', 'Solución de captura Antígeno de Treponema pallidum'),
    ('SPSAN01', 'Solución de captura 25 (OH) D'),
]

# El alta la firma Mery, no el bot: odoo shell corre como __system__ y dejaria
# su nombre en create_uid de 26 productos regulados. Y el candado de alta pide
# la bandera de autorizacion explicita.
mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
assert mery, 'No se encontro el usuario de Mery'
env = env(user=mery.id, context=dict(env.context, amunet_alta_autorizada=True))

modelo = env['product.product'].search([('default_code', '=', MODELO)], limit=1)
assert modelo, 'No se encontro el producto modelo %s' % MODELO
tm = modelo.product_tmpl_id
ruta_fab = env.ref('mrp.route_warehouse0_manufacture')

base = {
    'type': tm.type,
    'is_storable': tm.is_storable,
    'tracking': 'lot',
    'categ_id': tm.categ_id.id,
    'uom_id': tm.uom_id.id,
    'sale_ok': False,
    'purchase_ok': False,
    'amunet_destino_almacen': tm.amunet_destino_almacen,
    'amunet_resguardo_aru': tm.amunet_resguardo_aru,
    'amunet_etapa_ll': 'soluciones',
    'amunet_lot_reset_monthly': True,
    'route_ids': [(6, 0, [ruta_fab.id])],
}

creados, existentes = [], []
for clave, nombre in SOLUCIONES:
    ya = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if ya:
        existentes.append((clave, ya.name))
        continue
    vals = dict(base, name=nombre, default_code=clave)
    tmpl = env['product.template'].create(vals)
    # El prefijo de lote es la clave sin las 2 primeras letras: SPSCA01 -> SCA01.
    # Al escribirlo se crea sola la ir.sequence del lote.
    tmpl.serial_prefix_format = clave[2:]
    # El nombre es traducible: si no se escribe tambien en es_MX, el usuario
    # sigue viendo el valor viejo (o vacio) en la interfaz en espanol.
    tmpl.with_context(lang='es_MX').name = nombre
    creados.append((clave, nombre, tmpl.lot_sequence_id.prefix or '(sin secuencia)'))

env.cr.commit()

print('=' * 78)
print('CREADAS: %d' % len(creados))
for clave, nombre, pref in creados:
    print('  %-9s %-52s lote %s' % (clave, nombre[:52], pref))
print('YA EXISTIAN: %d' % len(existentes))
for clave, nombre in existentes:
    print('  %-9s %s' % (clave, nombre))
print('=' * 78)
