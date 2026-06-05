# -*- coding: utf-8 -*-
import logging
import time
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


class AmunetCompetenciasGenericSignatureHook(models.TransientModel):
    """
    Extiende el wizard generico de firma para que los flujos paperless
    fuera de QC tambien respeten la matriz de capacitacion vigente.
    """
    _inherit = 'amunet.generic.signature.wizard'

    def _training_check_enabled(self):
        return self.env['ir.config_parameter'].sudo().get_param(
            'amunet_competencias.signature_training_check_enabled', 'False'
        ).lower() == 'true'

    def _target_required_procedures(self, record):
        if hasattr(record, '_amunet_signature_required_procedures'):
            procedures = record._amunet_signature_required_procedures()
            return procedures.filtered('active') if procedures else procedures
        if 'procedure_ids' in record._fields:
            return record.procedure_ids.filtered('active')
        if 'equipment_id' in record._fields and record.equipment_id:
            return record.equipment_id.procedure_ids.filtered('active')
        if 'source_check_id' in record._fields and record.source_check_id:
            return record.source_check_id.procedure_ids.filtered('active')
        if 'quality_check_id' in record._fields and record.quality_check_id:
            return record.quality_check_id.procedure_ids.filtered('active')
        if 'product_id' in record._fields and record.product_id:
            return self.env['amunet.quality.procedure'].search([
                ('active', '=', True),
                ('product_ids', 'in', record.product_id.id),
            ])
        return self.env['amunet.quality.procedure']

    def _validate_generic_training(self, record):
        if not self._training_check_enabled():
            return
        procedures = self._target_required_procedures(record)
        if not procedures:
            _logger.debug(
                "Firma generica sin PNOs vinculados: %s/%s",
                record._name, record.display_name,
            )
            return

        user = self.env.user
        MatrizSvc = self.env['amunet.matriz.competencias']
        bloqueos = []
        for procedure in procedures:
            if not MatrizSvc.verificar_competencia(
                user_id=user.id,
                procedure_id=procedure.id,
            ):
                bloqueos.append(
                    "  - SOP {} - '{}' (Registro: {})".format(
                        procedure.code, procedure.name, record.display_name)
                )
        if bloqueos:
            raise ValidationError(
                "FIRMA BLOQUEADA - Capacitacion insuficiente\n\n"
                "El usuario '{}' no tiene capacitacion VIGENTE para:\n\n"
                "{}\n\nRegulariza la capacitacion antes de firmar.".format(
                    user.name, "\n".join(bloqueos))
            )

    def action_confirm_signature(self):
        started_at = time.perf_counter()
        self.ensure_one()
        record = self._target_record()
        after_target = time.perf_counter()
        self._validate_generic_training(record)
        after_training = time.perf_counter()
        result = super().action_confirm_signature()
        _logger.warning(
            'AMUNET_SIGNATURE_TRAINING_TIMING model=%s res_id=%s method=%s total=%.3fs target_record=%.3fs training=%.3fs downstream=%.3fs',
            record._name,
            record.id,
            self.method_name,
            time.perf_counter() - started_at,
            after_target - started_at,
            after_training - after_target,
            time.perf_counter() - after_training,
        )
        return result
