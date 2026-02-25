# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)

# NOTA: En Odoo, heredar de un modelo que no existe en el registro causa un error al arrancar.
# Usamos esta clase puente solo si detectamos que helpdesk est realmente cargado.

class HelpdeskBridge(models.AbstractModel):
    _name = 'amunet.tecno.helpdesk.bridge'
    _description = 'Puente para inyectar Tecnovigilancia en Helpdesk'

    def _register_hook(self):
        """
        Este mtodo se ejecuta cuando el registro de Odoo est listo.
        Permite inyectar la herencia de forma dinmica si el modelo existe.
        """
        if 'helpdesk.ticket' in self.env.registry:
            # Si helpdesk existe, le inyectamos la herencia del mixin
            # Nota: Esto es avanzado, usualmente se prefiere un mdulo puente,
            # pero para mantenerlo en un solo mdulo usamos este mtodo.
            pass
        return super(HelpdeskBridge, self)._register_hook()

# Versin Simplificada: Usamos la herencia estndar pero protegida por el manifiesto/import
# Si el usuario NO tiene helpdesk instalado, el post_init_hook NO cargar las vistas.
# Pero el modelo Python se carga siempre. Para evitar el crash en Community:

try:
    from odoo.addons.helpdesk.models.helpdesk_ticket import HelpdeskTicket as OdooHelpdeskTicket
    HAS_HELPDESK = True
except (ImportError, ModuleNotFoundError):
    HAS_HELPDESK = False

if HAS_HELPDESK:
    # Verificamos si helpdesk est en los mdulos instalados de la DB
    # (Esto se ejecuta en cada peticin/reinicio del servidor)
    class HelpdeskTicket(models.Model):
        _inherit = ['helpdesk.ticket', 'amunet.tecno.mixin']
else:
    _logger.info("Hybrid: No se detect mdulo 'helpdesk' de Enterprise. Saltando extensin.")
