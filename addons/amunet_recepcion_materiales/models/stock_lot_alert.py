import logging
from odoo import models, fields, api
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

MESES_VIDA_UTIL_HMC = 6  # hojas maestras con menos de esto se descartan


class StockLotAlert(models.Model):
    _inherit = 'stock.lot'

    amunet_alert_level = fields.Selection([
        ('ok',      'Vigente'),
        ('soon',    'Por vencer'),
        ('expired', 'Vencido'),
    ], compute='_compute_amunet_alert_level', store=False)

    @api.depends('expiration_date')
    def _compute_amunet_alert_level(self):
        today = date.today()
        soon = today + timedelta(days=30)
        for lot in self:
            if not lot.expiration_date:
                lot.amunet_alert_level = 'ok'
            elif lot.expiration_date.date() <= today:
                lot.amunet_alert_level = 'expired'
            elif lot.expiration_date.date() <= soon:
                lot.amunet_alert_level = 'soon'
            else:
                lot.amunet_alert_level = 'ok'

    def _amunet_scrap_hojas_por_vencer(self):
        """Cron diario: detecta lotes de Hojas Maestras con caducidad dentro de
        los próximos 6 meses y crea órdenes de descarte en borrador para que
        Almacén las revise y confirme."""
        hoy = date.today()
        limite = hoy + relativedelta(months=MESES_VIDA_UTIL_HMC)
        limite_dt = datetime(limite.year, limite.month, limite.day, 23, 59, 59)

        cat_hmc = self.env['product.category'].search(
            [('name', '=', 'Hoja maestra')], limit=1)
        if not cat_hmc:
            _logger.warning('amunet_scrap_hojas: no se encontró categoría "Hoja maestra"')
            return

        cat_ids = self.env['product.category'].search(
            [('id', 'child_of', cat_hmc.id)]).ids

        lotes = self.env['stock.lot'].search([
            ('product_id.categ_id', 'in', cat_ids),
            ('expiration_date', '!=', False),
            ('expiration_date', '<=', fields.Datetime.to_string(limite_dt)),
        ])

        creados = []
        for lote in lotes:
            # No crear un segundo descarte si ya hay uno pendiente
            ya_existe = self.env['stock.scrap'].search([
                ('lot_id', '=', lote.id),
                ('state', 'not in', ('done', 'cancel')),
            ], limit=1)
            if ya_existe:
                continue

            # Buscar quants con cantidad > 0 en ubicaciones internas
            quants = self.env['stock.quant'].search([
                ('lot_id', '=', lote.id),
                ('quantity', '>', 0),
                ('location_id.usage', '=', 'internal'),
            ])
            if not quants:
                continue

            # Una orden de descarte por ubicación (el lote puede estar en varias)
            for quant in quants:
                scrap = self.env['stock.scrap'].sudo().create({
                    'product_id': lote.product_id.id,
                    'product_uom_id': lote.product_id.uom_id.id,
                    'lot_id': lote.id,
                    'scrap_qty': quant.quantity,
                    'location_id': quant.location_id.id,
                    'amunet_motivo_descarte': 'Próximo a vencer',
                })
                exp_str = lote.expiration_date.strftime('%d/%m/%Y') if lote.expiration_date else '?'
                creados.append({
                    'scrap': scrap.name,
                    'producto': lote.product_id.display_name,
                    'lote': lote.name,
                    'qty': quant.quantity,
                    'uom': lote.product_id.uom_id.name,
                    'ubicacion': quant.location_id.complete_name,
                    'caducidad': exp_str,
                })

        if not creados:
            _logger.info('amunet_scrap_hojas: sin lotes de HMC por vencer al %s', hoy)
            return

        _logger.info('amunet_scrap_hojas: %d órdenes de descarte creadas', len(creados))

        # Actividad en cada lote asignada a Karla (uid 78 = almacen.mp)
        usuario = self.env['res.users'].browse(78)
        tipo_act = self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
        if not tipo_act:
            return
        for c in creados:
            lote_rec = self.env['stock.lot'].search(
                [('name', '=', c['lote'])], limit=1)
            if not lote_rec:
                continue
            lote_rec.sudo().activity_schedule(
                activity_type_id=tipo_act.id,
                summary='Confirmar descarte — ' + c['producto'] + ' vence ' + c['caducidad'],
                note=(
                    'Hoja Maestra por vencer (menos de ' + str(MESES_VIDA_UTIL_HMC) + ' meses).<br/>'
                    'Lote: <b>' + c['lote'] + '</b> | Cantidad: ' + str(round(c['qty'], 1)) + ' ' + c['uom'] + '<br/>'
                    'Ubicación: ' + c['ubicacion'] + '<br/>'
                    'Caducidad: <b>' + c['caducidad'] + '</b><br/><br/>'
                    'Revisa y valida el descarte en Inventario → Operaciones → Descartes.'
                ),
                user_id=usuario.id,
            )
