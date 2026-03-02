# -*- coding: utf-8 -*-
import logging
from odoo import models, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AmunetCompetenciasSignatureHook(models.TransientModel):
    """
    Extensión del wizard de firma electrónica de amunet_quality.
    Inyecta validación de competencia ANTES de solicitar el PIN.

    Mecanismo:
    - _inherit del wizard original (no se modifica ningún archivo de amunet_quality)
    - Override de action_confirm_signature()
    - Si el parámetro 'amunet_competencias.signature_training_check_enabled' = True,
      valida que el usuario tenga capacitación vigente para TODOS los SOPs
      vinculados al control de calidad que va a firmar.
    - Si falla → ValidationError (el PIN nunca se solicita)
    - Si pasa → llama a super() para continuar el flujo original (PIN + firma + audit log)

    ISO 13485:2016 §6.2 | FDA 21 CFR Part 11
    """
    _inherit = 'amunet.quality.signature.wizard'

    def action_confirm_signature(self):
        """
        Override: Validar competencia antes del PIN.
        El bloqueo es controlado por parámetro de sistema.
        """
        self.ensure_one()

        # ── 1. ¿Está habilitado el bloqueo? ──────────────────────────────────
        check_enabled = self.env['ir.config_parameter'].sudo().get_param(
            'amunet_competencias.signature_training_check_enabled', 'False'
        ).lower() == 'true'

        if not check_enabled:
            _logger.debug("Validación de competencia DESACTIVADA (parámetro = False).")
            return super().action_confirm_signature()

        # ── 2. Validar competencia para cada control de calidad ──────────────
        user = self.env.user
        MatrizSvc = self.env['amunet.matriz.competencias']

        bloqueos = []  # Acumular todos los errores para mostrarlos juntos

        for check in self.check_ids:
            # procedure_ids es Many2many calculado desde el producto del check
            procedures = check.procedure_ids if hasattr(check, 'procedure_ids') else []

            if not procedures:
                # Sin SOPs vinculados al check → no hay restricción de competencia
                _logger.debug(
                    "Check '%s' sin SOPs vinculados — omitiendo validación de competencia.",
                    check.name
                )
                continue

            for procedure in procedures:
                if not procedure.active:
                    continue  # Ignorar SOPs archivados

                is_competent = MatrizSvc.verificar_competencia(
                    user_id=user.id,
                    procedure_id=procedure.id,
                )

                if not is_competent:
                    bloqueos.append(
                        "  • SOP {} – '{}' (Check: {})".format(
                            procedure.code, procedure.name, check.name
                        )
                    )

        # ── 3. Lanzar error si hay bloqueos ──────────────────────────────────
        if bloqueos:
            lista = "\n".join(bloqueos)
            raise ValidationError(
                f"❌ FIRMA BLOQUEADA — Capacitación insuficiente\n\n"
                f"El analista '{user.name}' no tiene capacitación VIGENTE "
                f"para los siguientes procedimientos:\n\n"
                f"{lista}\n\n"
                "Contacte al Responsable de Capacitación para regularizar "
                "su entrenamiento antes de firmar."
            )

        # ── 4. Todo OK → continuar con el flujo original (PIN + firma) ───────
        _logger.info(
            "Validación de competencia EXITOSA para usuario '%s' en %d check(s).",
            user.name, len(self.check_ids)
        )
        return super().action_confirm_signature()
