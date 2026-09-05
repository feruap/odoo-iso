import logging
from odoo import models

_logger = logging.getLogger(__name__)


class AmunetQualityCheckCopiaControlada(models.Model):
    _inherit = 'amunet.quality.check'

    def _action_finalize_logic(self):
        super()._action_finalize_logic()
        try:
            self.env['amunet.copia.controlada']._crear_desde_qc(self)
        except Exception:
            _logger.exception(
                'No se pudo crear la copia controlada para QC %s', self.id)
