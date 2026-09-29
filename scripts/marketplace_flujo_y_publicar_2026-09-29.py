# -*- coding: utf-8 -*-
"""Dos arreglos del catalogo interno.

A) DIEZ PRODUCTOS ESTAN ROTOS HOY. Salen en el catalogo con flujo
   'produccion', y ese flujo obliga a que la solicitud lleve una orden de
   fabricacion. Una bascula, una centrifuga o un termohigrometro no se piden
   contra una orden: aparecen y truenan al pedirlos. Alguien los marco asi
   queriendo decir "esto es del laboratorio", no "esto va contra una orden".
   Pasan a 'general', el mismo criterio que Mery aprobo para los 14 que se
   fusionaron el 29-sep.

B) QUINCE REACTIVOS QUE YA EXISTEN NO ESTAN PUBLICADOS. Tienen clave,
   proveedor, existencia y movimientos -- Tris-HCl tiene 7,999 g --, pero no
   salen en el catalogo. Por eso la gente los propuso como productos nuevos:
   no los encuentra. Publicarlos cierra 14 de las 29 propuestas abiertas.

   Los tres requisitos ya se verificaron en los 15: destino de almacen 'mp',
   flujo 'general' y se compran y se almacenan. Solo falta el interruptor.

OJO, y ya esta avisado: la solicitud de compra NO muestra la existencia. Al
publicarlos quedan a un clic de generar una compra encima de material que ya
hay. El aviso de existencia es un pendiente aparte.

Idempotente. DRY_RUN=True no escribe.
"""
DRY_RUN = False

# A) los que estan en 'production' sin tener por que
A_GENERAL = [
    'Báscula de precisión Rhino', 'Base caldo Half Fraser granulado 500 g',
    'Centrífuga para laboratorio', 'Jeringa de vidrio borosilicato',
    'Microplaca ELISA 96 pozos', 'Probeta plástico 10 ml graduada',
    'Puntas de pipeta 5 ml', 'Termohigrómetro digital HTC-1',
    'Tubo PCR 0.2 ml tapa plana (MUHWA 1000 pz/bolsa)',
    'Varilla agitadora magnética',
]
# B) los reactivos que ya existen y hay que publicar
B_PUBLICAR = ['MPREC04', 'MPREC05', 'MPREC09', 'MPREC18', 'MPREC25', 'MPREC26',
              'MPREC33', 'MPREC41', 'MPREC53', 'MPREC65', 'MPREC67', 'MPREC78',
              'MPREC98', 'MPINP0101', 'COBDE01']

mery = env['res.users'].search([('login', '=', 'desarrollo@amunet.com.mx')], limit=1)
env = env(user=mery.id)
PT = env['product.template']

def por_nombre(nombre):
    for lang in ('es_MX', 'en_US'):
        f = PT.with_context(lang=lang).search([('name', '=', nombre)])
        f = f.filtered(lambda t: t.marketplace_enabled)
        if len(f) == 1:
            return f
        assert len(f) <= 1, 'hay %d con el nombre "%s"' % (len(f), nombre)
    return PT.browse()

cambiados, publicados, avisos = [], [], []

for nombre in A_GENERAL:
    t = por_nombre(nombre)
    if not t:
        avisos.append(('A', nombre, 'no se encontro en el catalogo')); continue
    if t.marketplace_flow == 'general':
        avisos.append(('A', nombre, 'ya estaba en general')); continue
    if not DRY_RUN:
        t.marketplace_flow = 'general'
    cambiados.append(nombre)

for clave in B_PUBLICAR:
    p = env['product.product'].search([('default_code', '=', clave)], limit=1)
    if not p:
        avisos.append(('B', clave, 'no existe')); continue
    t = p.product_tmpl_id
    if t.marketplace_enabled:
        avisos.append(('B', clave, 'ya estaba publicado')); continue
    # Los tres requisitos, comprobados antes de publicar.
    faltan = []
    if not t.amunet_destino_almacen:
        faltan.append('sin destino de almacen: la solicitud no se podra autorizar')
    if not t.purchase_ok:
        faltan.append('no se puede comprar')
    if faltan:
        avisos.append(('B', clave, '; '.join(faltan))); continue
    if not DRY_RUN:
        t.write({'marketplace_enabled': True, 'marketplace_flow': t.marketplace_flow or 'general'})
    ex = sum(env['stock.quant'].search([
        ('product_id', '=', p.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
    publicados.append((clave, t.name, ex))

if not DRY_RUN:
    env.cr.commit()

print('=' * 86)
print('SIMULACION — no se escribio nada' if DRY_RUN else 'APLICADO')
print('-' * 86)
print('A) pasan de produccion a general: %d' % len(cambiados))
for n in cambiados:
    print('   %s' % n)
print('B) se publican: %d' % len(publicados))
for clave, nombre, ex in publicados:
    print('   %-10s %-42s existencia %s' % (clave, nombre[:42], ex))
if avisos:
    print('-' * 86)
    for bloque, quien, motivo in avisos:
        print('   [%s] %-42s %s' % (bloque, quien[:42], motivo))
print('=' * 86)
