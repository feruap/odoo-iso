from odoo import _, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    amunet_solicitud_compra_id = fields.Many2one(
        'amunet.solicitud.compra',
        string='Solicitud de compra',
        readonly=True, copy=False, index=True,
        help='Solicitud que origino esta recepcion al autorizarse.',
    )

    def _action_done(self):
        """Al validar la ultima recepcion, la solicitud se cierra sola.

        Antes el cierre era 100% manual: Almacen validaba la entrada y la
        solicitud se quedaba en "Comprada" hasta que alguien entrara a
        apretar Cerrar. Nadie se enteraba de que ya se podia, y por eso al
        30-sep-2026 no habia UNA SOLA solicitud cerrada.

        Se cierra solo cuando ya no queda ninguna recepcion pendiente de esa
        solicitud: si la compra llego en dos entregas, la primera no la cierra.

        Una solicitud que seguia en "Autorizada" pasa por "Comprada" antes de
        cerrarse: si el material llego y se recibio, la compra ocurrio, aunque
        nadie hubiera apretado el boton.
        """
        res = super()._action_done()
        for solicitud in self.mapped('amunet_solicitud_compra_id'):
            if solicitud.state not in ('approved', 'purchased'):
                continue
            # sudo: quien valida ve los pickings de SU almacen. En una
            # solicitud repartida en dos almacenes, sin sudo no veria la del
            # otro y cerraria la solicitud con material todavia sin llegar.
            pendientes = solicitud.sudo().picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel'))
            if pendientes:
                continue
            if solicitud.state == 'approved':
                solicitud.state = 'purchased'
                solicitud.message_post(body=_(
                    'Marcada como comprada automaticamente: el material llego '
                    'y Almacen valido su entrada.'))
            solicitud.state = 'closed'
            solicitud.message_post(body=_(
                'Cerrada automaticamente al validarse %s: el material entro '
                'al inventario.') % ', '.join(self.filtered(
                    lambda p: p.amunet_solicitud_compra_id == solicitud
                ).mapped('name')))
        return res
