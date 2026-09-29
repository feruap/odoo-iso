# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, AccessDenied

_logger = logging.getLogger(__name__)

class AmunetQualitySignatureWizard(models.TransientModel):
    """
    Wizard para solicitar contraseña (Firma Electrónica) al finalizar
    un Control de Calidad, cumpliendo con 21 CFR Part 11 / ISO 13485.
    """
    _name = 'amunet.quality.signature.wizard'
    _description = 'Firma Electrónica de Calidad'

    check_ids = fields.Many2many(
        'amunet.quality.check',
        string="Controles a Firmar",
        required=True
    )

    password = fields.Char(
        string="Contraseña / PIN",
        required=True,
        help="Ingrese su contraseña o PIN de firma."
    )

    signature_type = fields.Selection([
        ('finalize', 'Finalizar'),
        ('realized', 'Realizó'),
        ('verified', 'Verificó'),
        ('authorized', 'Autorizó'),
    ], string="Tipo de Acción", default='finalize', required=True)

    # ---- Aviso de muestreo antes de la firma que cierra ----------------------
    # Se pregunta AQUI, en la firma de hecho, y no antes: quien cierra es quien
    # responde por lo que pasa con las piezas, y al cerrar corre la disposicion
    # que manda a Desechos lo que no se devuelve. Pedido por Mery el 29-sep-2026,
    # a raiz de QC/2026/00514: la devolucion quedo en 0 con 80 de muestra y 20
    # analizadas, y se fueron 60 pruebas buenas a la basura sin que nadie lo viera.
    amunet_aviso_muestreo = fields.Html(
        string='Revision del muestreo',
        compute='_compute_amunet_aviso_muestreo',
    )

    amunet_muestreo_ok = fields.Boolean(
        string='Revise las cantidades y confirmo que son correctas',
    )

    amunet_pide_confirmar = fields.Boolean(
        compute='_compute_amunet_aviso_muestreo',
    )

    @api.depends('check_ids', 'signature_type')
    def _compute_amunet_aviso_muestreo(self):
        for wiz in self:
            # solo en la firma que CIERRA el analisis
            if wiz.signature_type not in ('authorized', 'finalize'):
                wiz.amunet_aviso_muestreo = False
                wiz.amunet_pide_confirmar = False
                continue
            bloques = []
            pide = False
            for check in wiz.check_ids:
                r = check._amunet_resumen_muestreo()
                if not r:
                    continue
                grave = r['desecho'] > 0 and not r['cuadra'] and not r['hay_motivo']
                if grave:
                    pide = True
                color = 'alert-warning' if grave else 'alert-info'
                filas = _(
                    '<tr><td>Muestra que se llevó Calidad</td><td class="text-end"><b>%(mue)s %(uom)s</b></td></tr>'
                    '<tr><td>Analizada (se consume)</td><td class="text-end">%(ana)s %(uom)s</td></tr>'
                    '<tr><td>Regresa al almacén</td><td class="text-end"><b>%(dev)s %(uom)s</b></td></tr>'
                    '<tr><td>Se va a Desechos</td><td class="text-end"><b>%(des)s %(uom)s</b></td></tr>'
                ) % {'mue': r['muestra'], 'ana': r['analizada'], 'dev': r['devuelve'],
                     'des': r['desecho'], 'uom': r['uom']}
                if grave:
                    remate = _(
                        '<hr/><b>Lo esperado aquí serían %(esp)s %(uom)s de regreso</b>, '
                        'porque lo analizado se consume y el resto vuelve. Con lo '
                        'capturado, <b>%(des)s %(uom)s se dan por perdidas</b>.<br/><br/>'
                        'Si el número está bien, marque la casilla de abajo. Si no, '
                        'cancele, corrija la cantidad a devolver y vuelva a firmar. '
                        'También puede escribir el motivo de la merma en el análisis.'
                    ) % {'esp': r['esperado'], 'des': r['desecho'], 'uom': r['uom']}
                elif r['hay_motivo']:
                    remate = _('<hr/><i>Merma justificada: %s</i>') % (
                        check.amunet_return_deviation_reason or '')
                else:
                    remate = ''
                bloques.append(
                    '<div class="alert %s" role="alert"><b>%s</b> — %s'
                    '<table class="table table-sm mb-0 mt-2">%s</table>%s</div>' % (
                        color, check.name or '', check.product_id.display_name or '',
                        filas, remate))
            wiz.amunet_aviso_muestreo = ''.join(bloques) or False
            wiz.amunet_pide_confirmar = pide

    def _validate_credentials(self, password_or_pin):
        """
        Valida las credenciales del usuario (PIN o Contraseña).
        Ensura que el PIN esté hasheado.
        """
        user = self.env.user

        # 1. Intentar validar como PIN
        pin_record = self.env['amunet.quality.signature.pin'].search([
            ('user_id', '=', user.id)
        ], limit=1)
        
        if pin_record:
            _logger.info(f"Attempting PIN validation for {user.login}")
            if pin_record.check_pin(password_or_pin):
                _logger.info(f"User {user.login} authenticated via hashed PIN")
                return True
            else:
                _logger.warning(f"PIN validation FAILED for {user.login}")

        # 2. Intentar validar como Contraseña
        if self._validate_user_password(password_or_pin):
            _logger.info(f"User {user.login} authenticated via Password")
            return True

        # NOTA: Aquí había un fallback (login=admin + password=admin + parámetro
        # 'amunet_quality.signature_fallback_enabled'=True) que aceptaba la
        # firma. Eliminado el 2026-05-09 porque viola CFR 21 Part 11. Las
        # firmas electrónicas reguladas NO admiten bypass por configuración.

        return False

    def _validate_user_password(self, password):
        """
        Valida la contraseña del usuario usando múltiples estrategias
        actualizadas para Odoo 17+.
        """
        user = self.env.user
        db = self.env.cr.dbname
        
        _logger.info("=== DEBUG AUTHENTICATION START ===")
        _logger.info("Database: %s | User: %s (ID: %s)", db, user.login, user.id)

        if not password:
            _logger.warning("Password NO PROPORCIONADO")
            return False

        # ESTRATEGIA 1: res.users.authenticate (ESTÁNDAR ODOO 17+)
        try:
            _logger.info("Estrategia 1: Intentando res.users.authenticate (dict mode)")
            credentials = {
                'type': 'password',
                'db': db,
                'login': user.login,
                'password': password
            }
            # En Odoo 17+, authenticate espera un dict y el env del user agent
            uid = self.env['res.users'].authenticate(credentials, {'interactive': True})
            if uid:
                _logger.info("Estrategia 1 EXITOSA (UID: %s)", uid)
                return True
        except Exception as e:
            _logger.info("Estrategia 1 FALLIDA: %s", str(e))

        # NOTA: Anteriormente había una "Estrategia 3" de fallback que aceptaba
        # cualquier password de 4+ caracteres si el parámetro
        # 'amunet_quality.signature_fallback_enabled' estaba en True.
        # Eliminada el 2026-05-09 por ser incompatible con CFR 21 Part 11 y
        # con la auditoría de Cofepris: una firma electrónica regulada NO puede
        # tener bypass por configuración. Si la autenticación oficial de Odoo falla,
        # la firma DEBE rechazarse y el problema se diagnostica con los logs.

        _logger.warning("=== TODAS LAS ESTRATEGIAS FALLARON PARA %s ===", user.login)
        return False

    def action_confirm_signature(self):
        """
        Valida credenciales y ejecuta la firma correspondiente.
        Enfuerza Usuario Nominal y registra en Audit Log.
        """
        self.ensure_one()
        user = self.env.user

        if self.amunet_pide_confirmar and not self.amunet_muestreo_ok:
            raise ValidationError(_(
                'Antes de firmar, revise las cantidades de muestreo y devolución '
                'que muestra el aviso.\n\n'
                'Si son correctas, marque la casilla de confirmación. Si no, '
                'cancele y corrija la cantidad a devolver: al cerrar el análisis, '
                'lo que no se devuelve se manda a Desechos y esas piezas se dan '
                'por perdidas.'))

        if not self._validate_credentials(self.password):
            # Registrar fallido en log (Seguridad)
            self._log_signature_event(success=False)
            raise ValidationError("La contraseña o PIN es incorrecto.")

        # Procesar firma para cada check
        for check in self.check_ids:
            # Verificar nominal user (Ej: si el check ya tiene un analista asignado, debe ser él)
            # COFEPRIS/NOM-240 expect individual accountability
            self._enforce_nominal_user(check)

            # Los roles se verifican AQUI (servidor), no solo en el boton que
            # abre el wizard: el wizard se puede crear por RPC con cualquier
            # signature_type. Mismos grupos que action_sign_* del check.
            if self.signature_type == 'finalize':
                if not (self.env.user.has_group('amunet_quality.group_quality_sanitary') or
                        self.env.user.has_group('amunet_quality.group_quality_supervisor') or
                        self.env.user.has_group('amunet_quality.group_quality_manager')):
                    raise AccessDenied("Solo el Responsable Sanitario puede finalizar el QC.")
                check._action_finalize_logic()
            elif self.signature_type == 'realized':
                if not (self.env.user.has_group('amunet_quality.group_quality_user') or
                        self.env.user.has_group('amunet_quality.group_quality_supervisor')):
                    raise AccessDenied("No tiene permisos de Analista o Supervisor.")
                check._action_sign_realized_logic()
            elif self.signature_type == 'verified':
                if not self.env.user.has_group('amunet_quality.group_quality_supervisor'):
                    raise AccessDenied("No tiene permisos de Supervisor.")
                check._action_sign_verified_logic()
            elif self.signature_type == 'authorized':
                if not (self.env.user.has_group('amunet_quality.group_quality_sanitary') or
                        self.env.user.has_group('amunet_quality.group_quality_supervisor')):
                    raise AccessDenied("No tiene permisos de Responsable Sanitario o Supervisor.")
                check._action_sign_authorized_logic()
            
            # Registrar éxito en log
            self._log_signature_event(check, success=True)

        return {'type': 'ir.actions.act_window_close'}

    def _enforce_nominal_user(self, check):
        """
        Verificación de Usuario Nominal.
        Asegura que solo el usuario que firmó originalmente (si existe) pueda re-firmar,
        o que los roles se respeten.
        """
        user = self.env.user
        
        # Para 'Realizó' (Analista)
        if self.signature_type == 'realized':
            # Si ya hay una firma, solo el mismo usuario puede re-firmar (nominal accountability)
            if check.user_realized_id and check.user_realized_id != user:
                raise ValidationError(f"Solo el usuario que firmó originalmente ({check.user_realized_id.name}) puede re-firmar como 'Realizó'.")
        
        # Para 'Verificó' (Supervisor)
        elif self.signature_type == 'verified':
            if check.user_verified_id and check.user_verified_id != user:
                raise ValidationError(f"Solo el usuario que firmó originalmente ({check.user_verified_id.name}) puede re-firmar como 'Verificó'.")
        
        # Para 'Autorizó' (Sanitario)
        elif self.signature_type == 'authorized':
            if check.user_authorized_id and check.user_authorized_id != user:
                raise ValidationError(f"Solo el usuario que firmó originalmente ({check.user_authorized_id.name}) puede re-firmar como 'Autorizó'.")

    def _log_signature_event(self, check=None, success=True):
        """Registra el evento de firma en el Audit Log."""
        AuditLog = self.env['amunet.quality.audit.log'].sudo()
        status = "EXITOSA" if success else "FALLIDA"
        msg = f"Firma Electrónica {status} ({self.signature_type})"
        
        vals = {
            'model_name': 'amunet.quality.check',
            'res_id': check.id if check else 0,
            'res_name': check.name if check else 'WIZARD',
            'field_name': 'signature',
            'old_value': 'N/A',
            'new_value': msg,
            'justification': 'Proceso de firma electrónica obligatoria',
            'user_id': self.env.user.id,
        }
        # Usar sudo para asegurar el registro del log aunque haya fallado la auth inicial
        AuditLog.sudo().create(vals)
