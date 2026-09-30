"""PTESP01: fuera la MPBOL06 de la receta. La bolsa del kit es la COBME02 y va en la presentacion.

Autorizado por Mery el 30-sep-2026.

COMO SE EMPACA EL KIT, explicado por Mery: las 10 esponjas ya esterilizadas se meten en
bolsas Whirl-Pak, y solo caben 5 por bolsa -- de ahi las 2 COBPE01 de la receta-. Esas dos
bolsas se meten luego en la bolsa grande, que es la COBME02 (metalizada 19x25.5).

POR QUE SALE DE LA RECETA Y NO SE CAMBIA POR COBME02: porque la bolsa que agrupa la venta
va en la PRESENTACION, no en la receta. Al aprobar el plan de empaque,
_sync_secondary_components_to_production suma los componentes de la presentacion a los
materiales de la orden (approved_box_qty x qty_per_box). Si la COBME02 estuviera tambien
en la receta, el plan sobreescribiria la cantidad al aprobar.

Es el patron que ya usan los medios de cultivo:
    PTREC01  receta: MPBOL01 x1        (la bolsa del producto)
             presentacion: COBME02 x1  (la bolsa que agrupa las 10 piezas)

La MPBOL06 (termosellable 20x42) tiene existencia CERO. Mientras estuviera en la receta,
cualquier orden del kit de esponjas se trababa por falta de material. Esta pedida y va a
llegar, pero no es la bolsa de este kit.

QUE QUEDA EN LA RECETA: 10 esponjas STESP01 + 2 bolsas Whirl-Pak COBPE01. La COBME02 entra
por la presentacion al aprobar el plan.

No se toca ninguna orden ya fabricada: la receta solo alimenta las ordenes nuevas.

Idempotente.
"""
BomLine = env['mrp.bom.line'].sudo()

t = env['product.template'].sudo().search([('default_code', '=', 'PTESP01')], limit=1)
assert t, 'no existe PTESP01'
mp = env['product.product'].sudo().search([('default_code', '=', 'MPBOL06')], limit=1)

print('=== receta de PTESP01 antes ===')
for b in env['mrp.bom'].sudo().search([('product_tmpl_id', '=', t.id)]):
    for l in b.bom_line_ids:
        print('   %-12s %-40s %s' % (l.product_id.default_code or '?', (l.product_id.name or '')[:40], l.product_qty))

    linea = b.bom_line_ids.filtered(lambda l: l.product_id == mp)
    if not linea:
        print('   [ya] la MPBOL06 no esta en esta receta')
    else:
        # antes de quitarla: que ninguna orden viva dependa de ella
        moves = env['stock.move'].sudo().search([
            ('product_id', '=', mp.id),
            ('raw_material_production_id', '!=', False),
            ('state', 'not in', ('done', 'cancel')),
        ])
        if moves:
            print('   [ALTO] hay %d orden(es) viva(s) esperando MPBOL06: %s' % (
                len(moves), ', '.join(set(m.raw_material_production_id.name for m in moves))))
            print('          no se quita: primero hay que resolver esas ordenes')
        else:
            linea.unlink()
            print('   [ok] MPBOL06 fuera de la receta (ninguna orden viva la esperaba)')
            b.message_post(body=(
                'Se quitó <b>MPBOL06 (bolsa termosellable 20x42)</b> de la receta el '
                '30-sep-2026, autorizado por Mery.<br/><br/>'
                'El kit se empaca así: las 10 esponjas estériles van en <b>2 bolsas '
                'Whirl-Pak</b> (5 por bolsa), y esas dos van en la bolsa grande '
                '<b>COBME02</b>. La bolsa que agrupa la venta pertenece a la '
                '<b>presentación</b>, no a la receta: al aprobar el plan de empaque se '
                'suma sola a los materiales de la orden. Es el mismo patrón de los medios '
                'de cultivo.<br/><br/>'
                'La MPBOL06 tenía existencia cero, así que mientras estuviera aquí '
                'cualquier orden del kit se trababa por falta de material.'))

print('\n=== receta de PTESP01 despues ===')
for b in env['mrp.bom'].sudo().search([('product_tmpl_id', '=', t.id)]):
    for l in b.bom_line_ids:
        ex = sum(env['stock.quant'].sudo().search(
            [('product_id', '=', l.product_id.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
        print('   %-12s %-40s %5s   existencia %7.0f' % (
            l.product_id.default_code or '?', (l.product_id.name or '')[:40], l.product_qty, ex))
print('   + por la presentacion al aprobar el plan:')
for pres in env['amunet.packaging.presentation'].sudo().search([('product_tmpl_id', '=', t.id)]):
    for c in pres.component_ids:
        ex = sum(env['stock.quant'].sudo().search(
            [('product_id', '=', c.product_id.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
        print('   %-12s %-40s %5s   existencia %7.0f' % (
            c.product_id.default_code or '?', (c.product_id.name or '')[:40], c.qty_per_box, ex))
env.cr.commit()
