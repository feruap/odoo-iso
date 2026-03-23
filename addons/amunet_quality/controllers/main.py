# -*- coding: utf-8 -*-
"""
Epic-034: Control de Permisos Granular por Numeral en QC
HU-034-3: Sistema de bloqueo por usuario en proceso

Controlador HTTP para endpoints RPC de sistema de bloqueo.
"""

import logging
import traceback
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AmunetQualityController(http.Controller):
    """
    Controlador para endpoints RPC del módulo amunet_quality.
    """

    @http.route('/amunet_quality/download_certificate/<int:check_id>', type='http', auth='user')
    def download_quality_certificate(self, check_id, **kwargs):
        """
        Descarga directa del certificado con filename forzado usando content_disposition.
        """
        try:
            _logger.info(f"[PDF] download_quality_certificate - ID: {check_id}")
            check = request.env['amunet.quality.check'].sudo().browse(check_id)
            
            if not check.exists():
                _logger.error(f"[PDF] Registro amunet.quality.check({check_id}) no existe")
                return request.not_found()
            
            # Generar PDF
            report_xml_id = 'amunet_quality.action_report_quality_certificate'
            report = request.env.ref(report_xml_id, raise_if_not_found=False)
            
            if not report:
                _logger.error(f"[PDF] Acción de reporte '{report_xml_id}' no encontrada en la DB")
                return request.make_response(f"Error: No se encontró la acción de reporte '{report_xml_id}'. ¿Actualizó el módulo?", status=404)
            
            # Pass report XML ID and IDs list
            pdf_content, _ = report.sudo()._render_qweb_pdf(report_xml_id, [check_id])
            
            _logger.info(f"[PDF] PDF generado para {check_id}. Tamaño: {len(pdf_content)} bytes")
            
            # Obtener nombre de archivo
            filename = 'Certificado.pdf'
            if hasattr(check, 'get_pdf_filename'):
                filename = check.get_pdf_filename()
            else:
                filename = f'Certificado_{check.name}.pdf'
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            from odoo.http import content_disposition
            disposition = content_disposition(filename)
            
            pdfheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', disposition)
            ]
            
            return request.make_response(pdf_content, headers=pdfheaders)
            
        except Exception as e:
            _logger.error(f"[PDF ERROR] Error descargando certificado: {str(e)}", exc_info=True)
            return request.make_response(f"Error Interno (descarga): {str(e)}", status=500)

    @http.route('/amunet_quality/download_solicitud_report/<int:check_id>', type='http', auth='user')
    def download_solicitud_report(self, check_id, **kwargs):
        """
        Descarga directa del reporte "Solicitud-Reporte" con filename forzado.
        """
        try:
            _logger.info(f"[PDF] download_solicitud_report - ID: {check_id}")
            check = request.env['amunet.quality.check'].sudo().browse(check_id)
            
            if not check.exists():
                _logger.error(f"[PDF] Registro amunet.quality.check({check_id}) no existe")
                return request.not_found()
            
            # Generar PDF
            report_xml_id = 'amunet_quality.action_report_solicitud_reporte_v2'
            report = request.env.ref(report_xml_id, raise_if_not_found=False)
            
            if not report:
                _logger.error(f"[PDF] Acción de reporte '{report_xml_id}' no encontrada en la DB")
                return request.make_response(f"Error: No se encontró la acción de reporte '{report_xml_id}'. Verifique que el módulo esté actualizado.", status=404)
            
            # Pass report XML ID and IDs list
            pdf_content, _ = report.sudo()._render_qweb_pdf(report_xml_id, [check_id])

            # Agregar anexo si existe contenido en líneas, fotos o el usuario lo marcó
            if check.tiene_anexos or check.anexo_line_ids or check.anexo_photo_ids:
                try:
                    anexo_xml_id = 'amunet_quality.action_report_anexo_solicitud'
                    anexo_report = request.env.ref(anexo_xml_id, raise_if_not_found=False)
                    if anexo_report:
                        anexo_content, _ = anexo_report.sudo()._render_qweb_pdf(anexo_xml_id, [check_id])
                        from odoo.tools.pdf import merge_pdf
                        pdf_content = merge_pdf([pdf_content, anexo_content])
                        _logger.info(f"[PDF] Anexo integrado (merge) al reporte principal para {check_id}")
                except Exception as e_anx:
                    _logger.warning(f"Error integrando anexo al PDF para {check_id}: {e_anx}")
            
            _logger.info(f"[PDF] PDF de solicitud generado para {check_id}")

            # Obtener nombre de archivo
            ref_name = check.name or str(check_id)
            filename = f"Solicitud_Reporte_{ref_name.replace('/', '_')}.pdf"
            
            from odoo.http import content_disposition
            disposition = content_disposition(filename)
            
            pdfheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', disposition)
            ]
            
            return request.make_response(pdf_content, headers=pdfheaders)
            
        except Exception as e:
            _logger.error(f"[PDF ERROR] Error descargando solicitud: {str(e)}", exc_info=True)
            return request.make_response(f"Error Interno (solicitud): {str(e)}", status=500)

    @http.route('/amunet_quality/download_certificado_interno/<int:check_id>', type='http', auth='user')
    def download_certificado_interno(self, check_id, **kwargs):
        """
        Descarga directa del "Certificado Interno" con filename forzado.
        """
        try:
            _logger.info(f"[PDF] download_certificado_interno - ID: {check_id}")
            check = request.env['amunet.quality.check'].sudo().browse(check_id)
            
            if not check.exists():
                return request.not_found()
            
            # Incrementar contador y guardar (SUDO para asegurar escritura)
            check.sudo().write({'internal_certificate_count': check.internal_certificate_count + 1})
            
            # Generar PDF
            report_xml_id = 'amunet_quality.action_report_certificado_interno'
            report = request.env.ref(report_xml_id, raise_if_not_found=False)
            
            if not report:
                return request.make_response(f"Error: No se encontró la acción de reporte '{report_xml_id}'.", status=404)
            
            pdf_content, _ = report.sudo()._render_qweb_pdf(report_xml_id, [check_id])
            
            # Obtener nombre de archivo: CERMP-001-Nombre del producto
            # Limpiar nombre del producto para evitar caracteres inválidos
            product_name = (check.product_id.name or 'Producto').replace('/', '_').replace('\\', '_')
            seq_str = str(check.internal_certificate_count).zfill(3)
            filename = f"CERMP-{seq_str}-{product_name}.pdf"
            
            from odoo.http import content_disposition
            disposition = content_disposition(filename)
            
            pdfheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', disposition)
            ]
            
            return request.make_response(pdf_content, headers=pdfheaders)
            
        except Exception as e:
            _logger.error(f"[PDF ERROR] Error descargando certificado interno: {str(e)}", exc_info=True)
            return request.make_response(f"Error Interno: {str(e)}", status=500)

    @http.route('/qc/<int:check_id>/<string:check_number>', type='http', auth='public')
    def verify_quality_certificate(self, check_id, check_number, **kwargs):
        """
        Endpoint PÚBLICO para verificación de certificados vía QR.
        Valida que el ID y el check_number (analysis_number) coincidan.
        Si es válido, descarga el PDF.
        """
        try:
            _logger.info(f"[PDF] verify_quality_certificate - ID: {check_id}")
            # Sudo es necesario porque el usuario público puede no tener permisos de lectura directa
            check = request.env['amunet.quality.check'].sudo().browse(check_id)
            
            if not check.exists():
                _logger.warning(f"Verification failed: Check {check_id} not found.")
                return request.not_found()
                
            # Validación de Seguridad
            expected_number = check.analysis_number or check.name or 'draft'
            if check_number != expected_number and check_number != 'draft':
                 _logger.warning(f"Verification failed: Token mismatch for QC {check_id}. Received: {check_number}, Expected: {expected_number}")
                 return request.not_found()

            # Generar PDF
            report_xml_id = 'amunet_quality.action_report_quality_certificate'
            report = request.env.ref(report_xml_id, raise_if_not_found=False)
            
            if not report:
                _logger.error(f"Report action '{report_xml_id}' not found.")
                return request.not_found()
            
            # Pass report XML ID and IDs list
            pdf_content, _ = report.sudo()._render_qweb_pdf(report_xml_id, [check_id])
            
            filename = 'Certificado_Verificado.pdf'
            if hasattr(check, 'get_pdf_filename'):
                filename = check.get_pdf_filename()
            else:
                filename = f'Certificado_{check.name}.pdf'
            
            if not filename.endswith('.pdf'):
                filename += '.pdf'
            
            from odoo.http import content_disposition
            disposition = content_disposition(filename)
            
            pdfheaders = [
                ('Content-Type', 'application/pdf'),
                ('Content-Length', len(pdf_content)),
                ('Content-Disposition', disposition)
            ]
            
            return request.make_response(pdf_content, headers=pdfheaders)
            
        except Exception as e:
            _logger.error(f"[PDF ERROR] Error verificando certificado: {str(e)}", exc_info=True)
            return request.make_response(f"Error Interno (verificación): {str(e)}", status=500)

    @http.route('/amunet_quality/check_qc_lock', type='jsonrpc', auth='user')
    def check_qc_lock(self, check_id):
        """
        Endpoint RPC para verificar el estado de bloqueo de un QC.

        Args:
            check_id (int): ID del Control de Calidad

        Returns:
            dict con información del bloqueo:
                - is_locked (bool): Si está bloqueado
                - locked_by_user_id (int|False): ID del usuario que bloquea
                - locked_by_user_name (str|False): Nombre del usuario que bloquea
                - locked_at (str|False): Timestamp de bloqueo
                - last_edit_time (str|False): Timestamp última edición
                - lock_remaining_minutes (int): Minutos restantes
                - can_current_user_edit (bool): Si el usuario actual puede editar
                - lock_status_display (str): Texto descriptivo
        """
        try:
            check = request.env['amunet.quality.check'].browse(check_id)

            if not check.exists():
                return {
                    'error': True,
                    'message': 'QC no encontrado'
                }

            # Verificar timeout antes de retornar info
            check._check_lock_timeout()

            # Construir respuesta
            locked_by = False
            locked_by_name = False
            if check.locked_by_user_id:
                locked_by = check.locked_by_user_id.id
                locked_by_name = check.locked_by_user_id.name

            return {
                'error': False,
                'is_locked': check.is_locked,
                'locked_by_user_id': locked_by,
                'locked_by_user_name': locked_by_name,
                'locked_at': check.locked_at.isoformat() if check.locked_at else False,
                'last_edit_time': check.last_edit_time.isoformat() if check.last_edit_time else False,
                'lock_remaining_minutes': check.lock_remaining_minutes,
                'can_current_user_edit': check.can_current_user_edit,
                'lock_status_display': check.lock_status_display,
            }

        except Exception as e:
            _logger.error(f"[Epic-034] Error en check_qc_lock: {e}", exc_info=True)
            return {
                'error': True,
                'message': str(e)
            }

    @http.route('/amunet_quality/get_permission_matrix', type='jsonrpc', auth='user')
    def get_permission_matrix(self, user_ids=None, element_ids=None):
        """
        Endpoint RPC para obtener la matriz de permisos.

        Args:
            user_ids (list): Lista de IDs de usuarios (opcional)
            element_ids (list): Lista de IDs de elementos (opcional)

        Returns:
            dict con matriz de permisos
        """
        try:
            PermissionConfig = request.env['amunet.quality.permission.config']

            # Si no se especifican usuarios, obtener todos los activos
            if not user_ids:
                users = request.env['res.users'].search([
                    ('active', '=', True),
                    ('share', '=', False)
                ], limit=100)
                user_ids = users.ids

            # Si no se especifican elementos, obtener todos los configurables
            if not element_ids:
                elements = PermissionConfig.get_configurable_elements()
                element_ids = [e['id'] for e in elements]

            # Obtener matriz de permisos
            matrix = PermissionConfig.get_matrix_data(user_ids, element_ids)

            return {
                'error': False,
                'matrix': matrix,
            }

        except Exception as e:
            _logger.error(f"[Epic-034] Error en get_permission_matrix: {e}", exc_info=True)
            return {
                'error': True,
                'message': str(e)
            }
