# -*- coding: utf-8 -*-
"""Captura de la entrega de producto terminado al almacen de PT.

Una sola pantalla: cuanto se entrega, si es parcial o total, y el PIN de quien
entrega. El PIN valida contra el usuario en sesion -no identifica a nadie-,
porque cada quien entra a Odoo con su propia cuenta. Es distinto del kiosco de
soluciones, donde el PIN si identifica porque la tablet se comparte.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# Hasta esta fecha se permite entregar material sin liberacion de Calidad.
P_GRACIA = 'amunet_woocommerce.entrega_pt.gracia_sin_liberacion'


class AmunetEntregaPtWizard(models.TransientModel):
    _name = 'amunet.entrega.pt.wizard'
    _description = 'Entrega de producto terminado al almacen de PT'

    production_id = fields.Many2one(
        'mrp.production', string='Orden de produccion', required=True,
        readonly=True)
    product_id = fields.Many2one(
        'product.product', string='Producto', readonly=True)
    lot_id = fields.Many2one('stock.lot', string='Lote', readonly=True)
    qty_pendiente = fields.Float(
        string='Pendiente por entregar', readonly=True, digits='Product Unit')

    tipo = fields.Selection(
        [('total', 'Entrega total'), ('parcial', 'Entrega parcial')],
        string='Tipo de entrega', default='total', required=True)
    quantity = fields.Float(
        string='Piezas a entregar', required=True, digits='Product Unit')

    pin = fields.Char(string='Tu PIN', password=True)

    aviso_liberacion = fields.Char(string='Aviso', readonly=True)
    aviso_caducidad = fields.Char(string='Aviso de caducidad', readonly=True)

    # Datos del lote a la vista al entregar. Peticion de Mery (2026-09-02): que
    # la caducidad se revise AQUI, cuando el material se entrega, y no andarla
    # ajustando despues. Es el momento natural: quien entrega tiene el producto
    # fisico en la mano y puede comparar contra la etiqueta impresa.
    lote_caducidad = fields.Char(string='Caducidad del lote', readonly=True)
    lote_fabricacion = fields.Char(string='Fecha de fabricacion', readonly=True)
    lote_orden_dice = fields.Char(string='La orden dice', readonly=True)
    datos_correctos = fields.Boolean(
        string='Confirmo que estos datos coinciden con el producto fisico',
        help='Compara contra la etiqueta impresa antes de firmar.')

    # ------------------------------------------------------------------
    @api.onchange('tipo')
    def _onchange_tipo(self):
        """En total se entrega todo lo pendiente; en parcial lo escribe la persona."""
        if self.tipo == 'total':
            self.quantity = self.qty_pendiente

    # ------------------------------------------------------------------
    @api.model
    def abrir_para(self, production):
        Delivery = self.env['amunet.entrega.pt']
        lot = Delivery._resolve_lot_from_production(production)
        if not lot:
            raise UserError(_(
                'La orden %s todavia no tiene lote de producto terminado. '
                'Produccion debe registrar el lote antes de entregarlo.'
            ) % production.name)
        pendiente = Delivery._entrega_pt_pendiente(lot, production)
        if pendiente <= 0:
            raise UserError(_(
                'No hay piezas pendientes por entregar del lote %s.\n\n'
                'O ya se entrego todo lo de esta orden, o la orden no tiene '
                'cantidad por fabricar. Revisa en la orden cuanto falta por '
                'producir.'
            ) % lot.name)
        wizard = self.create([{
            'production_id': production.id,
            'product_id': production.product_id.id,
            'lot_id': lot.id,
            'qty_pendiente': pendiente,
            'quantity': pendiente,
            'aviso_liberacion': self._aviso_liberacion(lot, production),
            'aviso_caducidad': self._aviso_caducidad(lot),
            'lote_caducidad': (lot.expiration_date.strftime('%d/%m/%Y')
                               if lot.expiration_date else _('sin fecha')),
            'lote_fabricacion': (lot.manufacturing_date.strftime('%d/%m/%Y')
                                 if lot.manufacturing_date else _('sin fecha')),
            'lote_orden_dice': production.amunet_expiration_text or _('sin dato'),
        }])
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entrega de PT'),
            'res_model': self._name,
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @api.model
    def _aviso_caducidad(self, lot):
        """Aviso propio cuando el lote ya vencio o esta por vencer.

        Sustituye al wizard generico de Odoo, que en este flujo no se puede
        atender y dejaba el documento a medias en silencio. Este se ve ANTES de
        firmar y junto a la fecha, que es cuando sirve.
        """
        if not lot.expiration_date:
            return ''
        hoy = fields.Date.context_today(self)
        cad = fields.Date.to_date(lot.expiration_date)
        if cad < hoy:
            return _(
                'ATENCION: este lote figura como VENCIDO desde el %s. '
                'Si la caducidad esta mal capturada, corrigela en la orden '
                'ANTES de entregar: aqui todavia se puede.'
            ) % cad.strftime('%d/%m/%Y')
        if (cad - hoy).days <= 60:
            return _(
                'Este lote caduca el %s, en %s dias. Verifica que sea correcto '
                'antes de entregarlo.'
            ) % (cad.strftime('%d/%m/%Y'), (cad - hoy).days)
        return ''

    @api.model
    def _aviso_liberacion(self, lot, production=None):
        """Aviso sobre la liberacion del lote.

        OJO con la distincion, que confundio a Mery el 2026-09-02: que Calidad
        haya APROBADO EL ANALISIS de la orden no es lo mismo que el LOTE este
        liberado. Son dos estados distintos y el aviso decia "Calidad no lo ha
        liberado" en ordenes con el analisis ya aprobado, que es exactamente al
        reves de lo que pasa: con el analisis aprobado el lote se libera SOLO
        cuando el almacen valide esta entrega.
        """
        if getattr(lot, 'amunet_lot_release_state', False) == 'released':
            return ''
        aprobado = production is not None and getattr(
            production, 'quality_analysis_status', False) == 'approved'
        if aprobado:
            return _(
                'Calidad ya aprobo el analisis de esta orden. El lote se '
                'liberara SOLO, en automatico, cuando el almacen valide esta '
                'entrega: no hay que pedir nada mas.')
        return _(
            'Calidad todavia NO ha aprobado el analisis de esta orden. Se puede '
            'entregar, pero el material quedara RETENIDO: entra al almacen y no '
            'se puede vender hasta que Calidad apruebe.')

    # ------------------------------------------------------------------
    def _validar_pin(self):
        """El PIN confirma que quien entrega es quien esta en sesion."""
        self.ensure_one()
        if not self.pin:
            raise UserError(_('Escribe tu PIN para firmar la entrega.'))
        pin_record = self.env['amunet.quality.signature.pin'].sudo().search(
            [('user_id', '=', self.env.user.id)], limit=1)
        if not pin_record:
            raise UserError(_(
                'No tienes PIN de firma configurado.\n\n'
                'Puedes crearlo en tu perfil, en "Mi firma electronica".'))
        if not pin_record.check_pin(self.pin):
            raise UserError(_('El PIN no es correcto.'))

    def _validar_gracia_liberacion(self):
        """Vencida la gracia, no se entrega material que Calidad no aprobo.

        Se aceptan DOS formas de tener el visto bueno de Calidad, porque son dos
        estados distintos del mismo hecho:
          - el LOTE ya liberado, o
          - el ANALISIS de la orden ya aprobado (el lote se libera solo cuando
            el almacen valide esta entrega).
        Antes solo se miraba el lote, asi que una orden con el analisis aprobado
        se habria bloqueado al vencer la gracia sin ninguna razon.
        """
        self.ensure_one()
        if getattr(self.lot_id, 'amunet_lot_release_state', False) == 'released':
            return
        if getattr(self.production_id, 'quality_analysis_status',
                   False) == 'approved':
            return
        limite = self.env['ir.config_parameter'].sudo().get_param(P_GRACIA)
        if limite and fields.Date.context_today(self) <= fields.Date.to_date(limite):
            return
        raise UserError(_(
            'Calidad no ha aprobado el analisis del lote %(lote)s y el periodo '
            'de gracia termino el %(fecha)s.\n\n'
            'Calidad debe aprobar el analisis antes de entregarlo al almacen.'
        ) % {'lote': self.lot_id.name, 'fecha': limite or '-'})

    # ------------------------------------------------------------------
    def action_confirmar(self):
        self.ensure_one()
        if self.quantity <= 0:
            raise UserError(_('La cantidad a entregar debe ser mayor a 0.'))
        if self.quantity > self.qty_pendiente + 0.0001:
            raise UserError(_(
                'No puedes entregar %(pide)s: solo quedan %(quedan)s pendientes '
                'del lote %(lote)s.'
            ) % {'pide': self.quantity, 'quedan': self.qty_pendiente,
                 'lote': self.lot_id.name})
        if not self.datos_correctos:
            raise UserError(_(
                'Antes de firmar, revisa los datos del lote contra el producto '
                'que tienes en la mano:\n\n'
                '  Lote:               %(lote)s\n'
                '  Caducidad:          %(cad)s\n'
                '  Fecha de fabricacion: %(fab)s\n\n'
                'Si algo no coincide con la etiqueta impresa, NO entregues: '
                'avisa para corregirlo primero. Corregirlo aqui es facil; '
                'despues de que el lote se libere ya no lo es.\n\n'
                'Si todo coincide, marca la casilla de confirmacion.'
            ) % {'lote': self.lot_id.name or '',
                 'cad': self.lote_caducidad or '',
                 'fab': self.lote_fabricacion or ''})
        self._validar_gracia_liberacion()
        self._validar_pin()

        Delivery = self.env['amunet.entrega.pt']
        entrega = Delivery.with_context(amunet_entrega_pt=True).create({
            'production_id': self.production_id.id,
            'product_id': self.product_id.id,
            'lot_id': self.lot_id.id,
            'quantity_delivered': self.quantity,
            'delivered_by': self.env.user.id,
            'delivered_date': fields.Datetime.now(),
        })
        # 0) Que las piezas existan. La orden esta en curso, asi que Odoo aun no
        #    ha creado el producto terminado: se marca hecho solo el pedazo que
        #    se entrega. No cambia el folio, no crea orden hija y no toca los
        #    insumos (ver _entrega_pt_materializar).
        entrega._entrega_pt_materializar()
        # 1) El material sale de produccion y queda en custodia del almacen.
        entrega._entrega_pt_mover(
            entrega._entrega_pt_origen(), entrega._entrega_pt_entrada(),
            _('Entrega de PT %s') % self.production_id.name)
        # 2) Documento que el almacenista valida para volverlo existencia.
        picking = entrega._entrega_pt_generar_ingreso()

        entrega.message_post(body=_(
            'Entrega firmada por <b>%(quien)s</b> con su PIN: '
            '<b>%(qty)s</b> pza(s) del lote <b>%(lote)s</b> (%(tipo)s).<br/>'
            'El material esta en APT/Entrada. Falta que el almacen valide '
            '<b>%(doc)s</b> para que entre a existencias.',
            quien=self.env.user.display_name, qty=self.quantity,
            lote=self.lot_id.name,
            tipo=dict(self._fields['tipo'].selection)[self.tipo],
            doc=picking.name))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Entrega de PT'),
            'res_model': 'amunet.entrega.pt',
            'res_id': entrega.id,
            'view_mode': 'form',
            'target': 'current',
        }
