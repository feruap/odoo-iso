# -*- coding: utf-8 -*-
"""Apaga la bandera de analisis de calidad en 8 soluciones.

Decidido por Mery el 21-sep-2026. Son reactivos concentrados y soluciones
madre: no llevan analisis de liberacion.

Seis tenian UN solo parametro configurado, una tenia dos (Borato 0.1 M) y dos
tenian CERO -- esas dos generaban un analisis en blanco que se quedaba
atrapado en borrador.

Conservan analisis SPSPB01 y SPSPB02 (bloqueos de BSA), que tambien tienen un
solo parametro.

Correr con:
  /opt/odoo/scripts/run_correction.sh production soluciones_apagar_analisis_2026-09-21.py
"""

CLAVES = [
    'SPSAC01',   # Solucion HCl 6 M
    'SPSAS01',   # Azida de sodio 20 %
    'SPSHS01',   # Solucion Hidroxido de Sodio 1 M
    'SPSHS02',   # Hidroxido de sodio 20%
    'SPSRB01',   # Reactivo de Bradford
    'SPSPC03',   # Solucion Amortiguadora de Borato 0.1 M
    'SPACL01',   # Acido cloroaurico 1%      (sin parametros)
    'SPCDS01',   # Citrato de sodio 1%       (sin parametros)
]

T = env['product.template']
print('%-10s %-42s %-10s %s' % ('CLAVE', 'NOMBRE', 'ANTES', 'AHORA'))
cambiados = 0
for c in CLAVES:
    t = T.search([('default_code', '=', c)], limit=1)
    if not t:
        print('%-10s *** NO EXISTE ***' % c)
        continue
    antes = t.amunet_req_quality_control
    if antes:
        t.amunet_req_quality_control = False
        cambiados += 1
    print('%-10s %-42s %-10s %s' % (
        c, (t.name or '')[:40], 'pedia' if antes else 'ya estaba', 'NO pide'))
print('\nproductos modificados: %d' % cambiados)

# Las ordenes ABIERTAS que quedaron con el letrero viejo. Solo se tocan las
# que estan en 'Pendiente de Solicitar': si ya hay un analisis solicitado,
# aprobado o rechazado NO se toca -- es registro regulado.
MO = env['mrp.production']
rezago = MO.search([
    ('quality_analysis_status', '=', 'to_request'),
    ('state', 'not in', ('done', 'cancel')),
]).filtered(lambda m: not m.product_id.amunet_req_quality_control)
print('\nordenes abiertas con el letrero viejo: %d' % len(rezago))
for m in rezago:
    print('   %-14s %-10s %s' % (m.name, m.product_id.default_code, m.state))
rezago.write({'quality_analysis_status': 'none'})

intactas = MO.search_count([
    ('quality_analysis_status', 'in', ('requested', 'approved', 'rejected'))])
print('ordenes con analisis real, NO tocadas: %d' % intactas)

# Verificacion
sols = T.search([('categ_id.complete_name', 'ilike', 'soluc')])
piden = sols.filtered('amunet_req_quality_control')
print('\nRESULTADO: %d piden analisis | %d no piden (de %d soluciones)' % (
    len(piden), len(sols) - len(piden), len(sols)))
sin_param = [
    t.default_code for t in piden
    if env['amunet.quality.parameter.specification.config'].search_count(
        [('product_tmpl_id', '=', t.id)]) == 0]
print('piden analisis SIN parametros: %s' % (sin_param or 'NINGUNA'))

env.cr.commit()
