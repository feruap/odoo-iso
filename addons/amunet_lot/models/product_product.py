# -*- coding: utf-8 -*-
from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _amunet_next_lot_names(self, count=1):
        """Devuelve `count` nombres de lote consecutivos SIN consumir la secuencia.

        En vez de usar `next_by_id()` (que AVANZA el contador de la secuencia cada
        vez que se llama, aunque el usuario no guarde), calcula el siguiente numero
        a partir del MAXIMO existente para el prefijo del periodo actual, mirando:
          - los lotes (stock.lot) ya creados del producto, y
          - las lineas de movimiento pendientes con lot_name pero sin lot todavia.

        Asi es idempotente y sin huecos: abrir el modal "Detalles" N veces propone
        SIEMPRE el mismo numero hasta que una recepcion se guarda/valida; y al
        borrar un borrador, la numeracion se recupera sola.

        Es el mismo patron que ya usa el modulo para los factory lots (LOTEF).
        """
        self.ensure_one()
        seq = self.lot_sequence_id
        if not seq:
            # Sin secuencia Amunet: usar el helper nativo de Odoo
            return self.env['stock.lot'].generate_lot_names(self.id, count)

        # Prefijo/sufijo interpolados con la fecha de hoy (mes/anio), sin consumir
        try:
            prefix, suffix = seq._get_prefix_suffix()
        except Exception:
            prefix, suffix = (seq.prefix or ''), (seq.suffix or '')
        prefix = prefix or ''
        suffix = suffix or ''
        padding = seq.padding or 0
        plen, slen = len(prefix), len(suffix)

        Lot = self.env['stock.lot']
        MoveLine = self.env['stock.move.line']
        existing = Lot.with_context(active_test=False).search(
            [('product_id', '=', self.id), ('name', '=like', prefix + '%')]
        ).mapped('name')
        pending = MoveLine.search(
            [('product_id', '=', self.id), ('lot_id', '=', False),
             ('lot_name', '=like', prefix + '%')]
        ).mapped('lot_name')

        maxn = 0
        for nm in list(existing) + list(pending):
            if not nm:
                continue
            core = nm[plen:]
            if slen and core.endswith(suffix):
                core = core[:-slen]
            if core.isdigit():
                maxn = max(maxn, int(core))

        return ['%s%0*d%s' % (prefix, padding, maxn + 1 + i, suffix)
                for i in range(count)]
