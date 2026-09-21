# -*- coding: utf-8 -*-
from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _amunet_es_ingreso_produccion(self):
        """El ingreso que Produccion entrega a Almacen."""
        self.ensure_one()
        tipo = self.env.ref(
            'amunet_production.picking_type_ingreso_produccion',
            raise_if_not_found=False)
        return bool(tipo) and self.picking_type_id == tipo

    def _amunet_signature_allowed_methods(self):
        """Metodos que el wizard de firma puede ejecutar sobre un picking."""
        base = []
        heredado = getattr(super(), '_amunet_signature_allowed_methods', None)
        if heredado:
            base = list(heredado())
        return base + ['_amunet_firmar_ingreso_produccion']

    def button_validate(self):
        """El ingreso de produccion se valida FIRMANDO.

        Almacen confirma con su PIN que tiene el material fisicamente, con ese
        lote y esa cantidad. Es el espejo de lo que ya firma cuando surte, y
        de lo que firma Produccion cuando recibe. Mery, 21-sep-2026.
        """
        ingresos = self.filtered(
            lambda p: p._amunet_es_ingreso_produccion()
            and not self.env.context.get('amunet_ingreso_firmado'))
        if ingresos:
            if len(ingresos) > 1:
                raise UserError(_(
                    'Valida un ingreso de produccion a la vez: cada uno lleva '
                    'su firma.'))
            ingreso = ingresos[0]
            return self.env['amunet.generic.signature.wizard'].open_for(
                ingreso,
                '_amunet_firmar_ingreso_produccion',
                _('Ingreso de produccion'),
                _('Firma de Almacen: recibe %s de Produccion.') % ingreso.name)
        return super().button_validate()

    def _amunet_firmar_ingreso_produccion(self):
        self.ensure_one()
        return self.with_context(
            amunet_ingreso_firmado=True).button_validate()
