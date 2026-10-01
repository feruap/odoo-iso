# -*- coding: utf-8 -*-
"""Avisarle al solicitante cuando su compra no salio como la pidio.

Decision de Direccion (1-oct-2026). El 1 de octubre se compraron 2 frascos
de triptona de los 10 que pedia SC/2026/00003, la probeta de 1 L no se
consiguio y la de 250 ml se surtio con otro modelo. Quien lo pidio no se
entero de nada.

Dos huecos lo hacian imposible:

  1. El renglon guardaba UNA sola cantidad. Al bajar la triptona de 10 a 2
     se perdio que habia pedido 10, asi que el sistema ya no tenia contra
     que comparar. Por eso ahora hay dos: `amunet_qty_pedida`, que se
     congela al enviar la solicitud, y `qty`, que es lo que se compro.
  2. En la mitad de las solicitudes el solicitante NO era seguidor de la
     suya, asi que el chatter le hablaba a nadie. Se suscribe al enviar.

El aviso se arma con plantilla fija y una lista cerrada de motivos. NO hay
campo libre: asi no se filtra al solicitante nada de logistica -- aduana,
domicilios de entrega, fletes, importacion -- ni importes, que ademas
siguen reservados al area de compras. Lo logistico se escribe en el
chatter como nota interna, que es otro canal y otra audiencia.
"""

from markupsafe import Markup

from odoo import _, fields, models

AJUSTES = [
    ('completo', 'Se compro completo'),
    ('parcial', 'Se compro menos de lo pedido'),
    ('equivalente', 'Se cambio por otro equivalente'),
    ('no_disponible', 'No se consiguio'),
]

# Lo unico que el solicitante lee como explicacion.
EXPLICACION = {
    'parcial': 'Habia menos existencia de la que pediste.',
    'equivalente': 'Se surtio con otro modelo equivalente.',
    'no_disponible': 'No se consiguio.',
}


class AmunetSolicitudCompraLine(models.Model):
    _inherit = 'amunet.solicitud.compra.line'

    amunet_qty_pedida = fields.Float(
        string='Pedida',
        digits='Product Unit of Measure',
        copy=False,
        help='Lo que pidio el solicitante. Se congela al enviar la solicitud '
             'y ya no cambia: es contra esto que se compara lo que de verdad '
             'se compro.',
    )
    amunet_ajuste = fields.Selection(
        AJUSTES, string='Ajuste', copy=False,
        help='Por que este renglon no salio como se pidio. Si se deja vacio '
             'se deduce de las cantidades; marcalo a mano solo cuando se '
             'cambio el producto.',
    )

    def _amunet_ajuste_real(self):
        """Lo capturado manda; si no, se deduce de las cantidades."""
        self.ensure_one()
        if self.amunet_ajuste:
            return self.amunet_ajuste
        pedida = self.amunet_qty_pedida or self.qty
        if not self.qty:
            return 'no_disponible'
        if self.qty < pedida:
            return 'parcial'
        return 'completo'


class AmunetSolicitudCompra(models.Model):
    _inherit = 'amunet.solicitud.compra'

    def _amunet_suscribir_solicitante(self):
        for req in self:
            socio = req.sudo().requester_id.partner_id
            if socio:
                req.message_subscribe(partner_ids=[socio.id])

    def action_enviar(self):
        """Al enviar se congela lo pedido y el solicitante pasa a seguir."""
        for req in self:
            for linea in req.line_ids:
                if not linea.amunet_qty_pedida:
                    linea.amunet_qty_pedida = linea.qty
        resultado = super().action_enviar()
        self._amunet_suscribir_solicitante()
        return resultado

    def _amunet_renglones_ajustados(self, todo_perdido=False):
        """(descripcion, pedida, comprada, explicacion) por renglon alterado."""
        self.ensure_one()
        filas = []
        for linea in self.line_ids:
            estado = 'no_disponible' if todo_perdido else linea._amunet_ajuste_real()
            if estado == 'completo':
                continue
            filas.append((
                linea.name or '?',
                linea.amunet_qty_pedida or linea.qty,
                0.0 if todo_perdido else linea.qty,
                EXPLICACION.get(estado, ''),
            ))
        return filas

    def _amunet_avisar_solicitante(self, titulo, todo_perdido=False):
        """Plantilla fija. Cantidades y motivo; nada de logistica ni importes."""
        self.ensure_one()
        self._amunet_suscribir_solicitante()
        filas = self._amunet_renglones_ajustados(todo_perdido=todo_perdido)

        if not filas:
            self.message_post(
                body=Markup('<p>%s</p>') % titulo,
                subtype_xmlid='mail.mt_comment')
            return False

        partes = [Markup('<p>%s</p><ul>') % titulo]
        for descripcion, pedida, comprada, explicacion in filas:
            partes.append(Markup(
                '<li><b>%s</b><br/>Pediste %s &middot; Se compro %s<br/>'
                '<i>%s</i></li>'
            ) % (descripcion, '{:g}'.format(pedida),
                 '{:g}'.format(comprada), explicacion))
        partes.append(Markup('</ul>'))
        self.message_post(body=Markup('').join(partes),
                          subtype_xmlid='mail.mt_comment')

        solicitante = self.sudo().requester_id
        if solicitante:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=solicitante.id,
                summary=_('Revisa los ajustes de tu solicitud %s') % self.name)
        return True

    def action_marcar_comprada(self):
        resultado = super().action_marcar_comprada()
        for req in self:
            req._amunet_avisar_solicitante(
                _('Tu solicitud %s ya se compro.') % req.name)
        return resultado

    def action_cancelar(self):
        resultado = super().action_cancelar()
        for req in self:
            req._amunet_avisar_solicitante(
                _('Tu solicitud %s se cancelo y no se va a comprar.') % req.name,
                todo_perdido=True)
        return resultado
