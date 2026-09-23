# -*- coding: utf-8 -*-
"""El folio de una orden que nunca se trabajo regresa al consecutivo.

El folio de la MO (MMAA/NN/ABR) sale de un contador que avanza y nunca vuelve.
Una orden creada por equivocacion se lleva su numero para siempre, y el siguiente
producto arranca en 02 aunque sea el primero del mes.

Paso el 3-sep-2026: se crearon y cancelaron DIEZ ordenes en el mismo minuto, y
por eso CAL, TUB, PSS e ICN quedaron corridos. La de Procalcitonina se corrigio a
mano el 23-sep (0926/02/ICN -> 0926/01/ICN, y la cancelada quedo como
0926/01/ICN-CANCELADA).

Regla de Mery (23-sep-2026): que el folio regrese al borrar Y al cancelar, para
cualquier produccion.

Solo se devuelve si la orden NO se trabajo. Una orden que ya consumio material o
produjo piezas conserva su folio aunque se cancele: ese numero esta en los
movimientos y en las etiquetas, y reciclarlo dejaria dos registros distintos con
el mismo folio.

Y solo si es el ULTIMO folio emitido. Si ya se emitieron otros despues, retroceder
haria que dos ordenes acabaran con el mismo numero; en ese caso el hueco se queda,
que es lo correcto.
"""

from odoo import _, models

# Estados desde los que se considera que la orden nunca arranco.
ESTADOS_SIN_TRABAJAR = ('draft', 'confirmed')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _amunet_folio_es_devolvible(self):
        """La orden nunca se trabajo, asi que su folio se puede reciclar."""
        self.ensure_one()
        if self.state not in ESTADOS_SIN_TRABAJAR:
            return False
        # consumo de componentes
        if any(l.state == 'done' or l.quantity
               for mv in self.move_raw_ids for l in mv.move_line_ids):
            return False
        # produccion registrada
        if self.qty_produced:
            return False
        # actividades ya iniciadas
        if any(w.state not in ('pending', 'ready') for w in self.workorder_ids):
            return False
        # lote ya creado con movimientos
        lote = self.env['stock.lot'].sudo().search(
            [('name', '=', self.name), ('product_id', '=', self.product_id.id)], limit=1)
        if lote and self.env['stock.move.line'].sudo().search_count(
                [('lot_id', '=', lote.id)]):
            return False
        return True

    def _amunet_devolver_folio(self, motivo):
        """Regresa el folio al consecutivo y deja el rastro."""
        for rec in self:
            seq = rec.product_id.product_tmpl_id.mo_sequence_id
            if not seq or not rec._amunet_folio_es_devolvible():
                continue
            if seq._amunet_devolver_folio(rec.name):
                rec.message_post(body=_(
                    'Folio %(folio)s devuelto al consecutivo: la orden se '
                    '%(motivo)s sin haberse trabajado, así que ese número queda '
                    'libre para la siguiente orden de este producto.'
                ) % {'folio': rec.name, 'motivo': motivo})

    def unlink(self):
        # antes del borrado: despues ya no hay de donde leer el folio
        self._amunet_devolver_folio(_('borró'))
        return super().unlink()

    def action_cancel(self):
        # La foto se toma ANTES del super: al cancelar, Odoo recalcula
        # cantidades y suelta reservas, asi que despues ya no se puede saber si
        # la orden se habia trabajado. Pasarlo por alto hacia que una orden CON
        # produccion registrada reciclara su folio.
        antes = {}
        for rec in self:
            seq = rec.product_id.product_tmpl_id.mo_sequence_id
            if not seq or not rec.name or rec.name.endswith('-CANCELADA'):
                continue
            if rec._amunet_folio_es_devolvible():
                antes[rec.id] = (seq, rec.name)

        res = super().action_cancel()

        for rec in self:
            if rec.id not in antes or rec.state != 'cancel':
                continue
            seq, folio = antes[rec.id]
            if seq._amunet_devolver_folio(folio):
                # el folio se recicla, asi que esta orden no puede conservarlo:
                # si no, la siguiente naceria con el mismo nombre
                rec.write({'name': '%s-CANCELADA' % folio})
                rec.message_post(body=_(
                    'Folio %(folio)s devuelto al consecutivo: la orden se '
                    'canceló sin haberse trabajado. Esta orden queda como '
                    '%(nuevo)s para conservar el registro, y el número vuelve a '
                    'estar libre para la siguiente.'
                ) % {'folio': folio, 'nuevo': rec.name})
        return res
