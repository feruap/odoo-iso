# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import UserError


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    def _amunet_lc_check_start_gate(self):
        """Gating de Linea Corta al INICIAR una actividad:
          A) El Surtido de materiales debe estar ENTREGADO (terminado).
          B) El paso de produccion anterior debe haber INICIADO (se
             permite traslape; no necesita estar terminado).
        Solo aplica a ordenes con amunet_lc_gating (ordenes nuevas de
        ruta corta). Bloqueo duro, nadie se salta."""
        for wo in self:
            mo = wo.production_id
            if not mo or not mo.amunet_lc_gating:
                continue
            wos = mo.workorder_ids.filtered(lambda w: w.operation_id)
            if not wos:
                continue
            ordered = wos.sorted(lambda w: w.operation_id.sequence)
            surtido = ordered[:1]
            if wo == surtido:
                continue  # el Surtido inicia libremente
            cur_seq = wo.operation_id.sequence
            # A) Surtido entregado (terminado)
            if surtido.state != 'done':
                raise UserError(_(
                    'No puedes iniciar "%(act)s" todavia.\n\n'
                    'Primero el paso "%(sur)s" debe estar ENTREGADO '
                    '(terminado): el material debe estar surtido antes de '
                    'empezar la produccion.'
                ) % {'act': wo.display_name, 'sur': surtido.display_name})
            # B) Paso de produccion anterior iniciado
            prevs = ordered.filtered(
                lambda w: w.operation_id.sequence < cur_seq and w != surtido)
            if prevs:
                prev = prevs[-1]
                if prev.state not in ('progress', 'done'):
                    raise UserError(_(
                        'No puedes iniciar "%(act)s" todavia.\n\n'
                        'Primero debe haber INICIADO el paso anterior '
                        '"%(prev)s". En Linea Corta las actividades se '
                        'inician en secuencia (si se puede traslapar, pero '
                        'no saltar el orden).'
                    ) % {'act': wo.display_name, 'prev': prev.display_name})

    def button_start(self):
        self._amunet_lc_check_start_gate()
        return super().button_start()
