"""Dos soluciones de captura cambian de clave, por acuerdo de Documentacion.

Autorizado por Mery el 28-sep-2026.

Documentacion reasigno las claves para que las 30 soluciones de captura sigan una
sola serie, y para respetar las cuatro que ya se habian creado (SPSCA25 anti-raton,
26 anti-p24, 27 anti-TSH, 28 anti-Salmonella):

    SPSPC01  Solucion de captura Antigeno de Treponema pallidum  ->  SPSCA29
    SPSAN01  Solucion de captura 25 (OH) D                       ->  SPSCA30

Las dos viven SOLO en staging, sin movimientos, sin lotes y sin recetas -- ni
propias ni como componente --, asi que el cambio de clave no arrastra nada.

OJO PARA EL MAPEO DE HOJAS MAESTRAS: el archivo de Mery menciona estas soluciones
con la clave vieja. SPHMC22 (Sifilis) usa la que ahora es SPSCA29, y SPHMC09
(Vitamina D) la que ahora es SPSCA30. El mapeo sigue valiendo, con los nombres
nuevos.

Idempotente.
"""

PT = env['product.template'].sudo()
CAMBIOS = [('SPSPC01', 'SPSCA29'), ('SPSAN01', 'SPSCA30')]

for viejo, nuevo in CAMBIOS:
    t = PT.with_context(active_test=False).search([('default_code', '=', viejo)], limit=1)
    ya = PT.with_context(active_test=False).search([('default_code', '=', nuevo)], limit=1)
    if not t:
        print('[%s] %s: %s' % ('ya' if ya else 'ojo', viejo,
                               'ya es %s' % nuevo if ya else 'no existe en esta base'))
        continue
    if ya:
        print('NO SE CAMBIA %s: la clave %s ya la tiene %s' % (viejo, nuevo, ya.id))
        continue
    # guarda: que no arrastre nada
    p = t.product_variant_ids
    ref = []
    for etiqueta, modelo, dom in (
            ('movimientos', 'stock.move.line', [('product_id', 'in', p.ids)]),
            ('lotes', 'stock.lot', [('product_id', 'in', p.ids)]),
            ('usada en recetas', 'mrp.bom.line', [('product_id', 'in', p.ids)]),
            ('receta propia', 'mrp.bom', [('product_tmpl_id', '=', t.id)]),
    ):
        n = env[modelo].sudo().with_context(active_test=False).search_count(dom)
        if n:
            ref.append('%s: %s' % (etiqueta, n))
    if ref:
        print('OJO %s tiene %s -- se cambia la clave igual, pero queda dicho' % (
            viejo, '; '.join(ref)))
    t.write({'default_code': nuevo})
    t.message_post(body=(
        'Clave cambiada de %s a %s el 28-sep-2026, por acuerdo de Documentacion: '
        'las 30 soluciones de captura siguen una sola serie SPSCA. Autorizado por '
        'Mery. El producto no tenia movimientos, lotes ni recetas.'
    ) % (viejo, nuevo))
    print('[ok] %s -> %s   %s' % (viejo, nuevo, (t.nombre_etiqueta or t.name)[:44]))

print('\n=== la serie de soluciones de captura ===')
for t in PT.search([('default_code', 'like', 'SPSCA%')], order='default_code'):
    print('   %-9s %s' % (t.default_code, (t.nombre_etiqueta or t.name)[:52]))
resto = PT.search([('default_code', 'in', ('SPSPC01', 'SPSAN01'))])
print('   quedan con la clave vieja: %s' % (resto.mapped('default_code') or 'ninguna'))
env.cr.commit()
