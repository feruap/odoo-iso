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
        quien = self.env.user.name
        for solicitud in self.mapped('amunet_solicitud_compra_id'):
            if solicitud.state not in ('approved', 'purchased'):
                continue
            # TODO EL CIERRE VA CON sudo, no solo la lectura. Dos razones:
            #
            # 1. Quien valida la entrada es Almacen, y Almacen tiene LECTURA pero
            #    no escritura sobre la solicitud de compra. Sin sudo, validar
            #    reventaba con "No puede modificar registros 'Solicitud de
            #    compra'" y la recepcion no se podia cerrar. Le paso a Karla el
            #    01-oct-2026 en AMP/IN/00489.
            #
            # 2. Y NO se arregla dandole escritura a Almacen: la solicitud lleva
            #    el monto, la forma de pago y la referencia del pago. Ampliar sus
            #    permisos ahi abriria datos de compras a quien no le corresponde.
            #    El cierre lo hace el SISTEMA al entrar el material, no la persona
            #    que valida, asi que sudo es lo que describe lo que pasa.
            #
            # El sudo de la lectura, ademas, sigue siendo necesario: quien valida
            # solo ve los pickings de SU almacen, y en una solicitud repartida en
            # dos almacenes no veria la del otro y la cerraria con material sin
            # llegar.
            solicitud_sys = solicitud.sudo()
            pendientes = solicitud_sys.picking_ids.filtered(
                lambda p: p.state not in ('done', 'cancel'))
            if pendientes:
                continue
            recepciones = ', '.join(self.filtered(
                lambda p: p.amunet_solicitud_compra_id == solicitud).mapped('name'))
            if solicitud_sys.state == 'approved':
                solicitud_sys.state = 'purchased'
                solicitud_sys.message_post(body=_(
                    'Marcada como comprada automaticamente: el material llego '
                    'y Almacen valido su entrada (%s).') % quien)
            solicitud_sys.state = 'closed'
            # Queda escrito QUIEN valido: el cierre lo ejecuta el sistema, pero
            # el acto que lo dispara es de una persona y eso tiene que poder
            # rastrearse.
            solicitud_sys.message_post(body=_(
                'Cerrada automaticamente al validarse %(recepciones)s por '
                '%(quien)s: el material entro al inventario.'
            ) % {'recepciones': recepciones, 'quien': quien})
        return res
