# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    # Reinicio mensual opcional
    amunet_lot_reset_monthly = fields.Boolean(
        string='Reiniciar secuencia mensualmente',
        default=True,
        help="Si está activo, la secuencia se reiniciará el primer día de cada mes"
    )
    
    # Campo para mostrar solo el prefijo base (sin placeholders) al usuario
    amunet_lot_prefix = fields.Char(
        string='Número de serie/lote personalizado',
        compute='_compute_amunet_lot_prefix',
        inverse='_inverse_amunet_lot_prefix',
        store=False,
        help="Prefijo base para generar lotes automáticos. Ejemplo: 'CR8' generará lotes como 'CR8112501'"
    )
    
    def _is_amunet_auto_lot_enabled(self):
        """
        Determina si un producto tiene auto-generación de lotes Amunet activada.
        """
        return (
            self.tracking == 'lot' and
            self.lot_sequence_id and 
            self.lot_sequence_id.code and 
            self.lot_sequence_id.code.startswith('amunet.lot.')
        )
    
    @api.depends('lot_sequence_id', 'lot_sequence_id.prefix')
    def _compute_amunet_lot_prefix(self):
        """
        Computa el prefijo base (sin placeholders) desde el prefijo de la secuencia.
        
        Ejemplo: Si lot_sequence_id.prefix = "CR8%(month)s%(y)s", muestra "CR8"
        """
        for template in self:
            if template.lot_sequence_id and template.lot_sequence_id.prefix:
                prefix = template.lot_sequence_id.prefix
                # Extraer solo el prefijo base (antes de cualquier placeholder %(...)s)
                if '%(' in prefix:
                    template.amunet_lot_prefix = prefix.split('%(')[0]
                else:
                    template.amunet_lot_prefix = prefix
            else:
                template.amunet_lot_prefix = ''

    @api.depends('lot_sequence_id', 'lot_sequence_id.prefix')
    def _compute_serial_prefix_format(self):
        """
        Override del método nativo para mostrar el prefijo limpio (sin placeholders).
        Odoo nativo usa este campo para el widget de generación de lotes.
        """
        amunet_templates = self.filtered(lambda t: t._is_amunet_auto_lot_enabled())
        other_templates = self - amunet_templates
        
        if other_templates:
            try:
                super(ProductTemplate, other_templates)._compute_serial_prefix_format()
            except (AttributeError, TypeError):
                # Si no existe en el padre, simplemente no hacemos nada para el resto
                pass
            
        for template in amunet_templates:
            template._compute_amunet_lot_prefix()
            template.serial_prefix_format = template.amunet_lot_prefix
    
    def _inverse_amunet_lot_prefix(self):
        """
        Cuando el usuario cambia el prefijo, actualiza la secuencia con placeholders.
        
        Ejemplo: Si el usuario escribe "CR8", crea/actualiza secuencia con "CR8%(month)s%(y)s"
        """
        for template in self:
            if not template.amunet_lot_prefix:
                continue
            
            base_prefix = template.amunet_lot_prefix.strip()
            if not base_prefix:
                continue
            
            # Prefijo con placeholders para la secuencia
            sequence_prefix = f"{base_prefix}%(month)s%(y)s"
            
            # Buscar secuencia existente
            sequence_code = f"amunet.lot.{base_prefix}.{template.id}"
            existing_sequence = self.env['ir.sequence'].search([
                ('code', '=', sequence_code),
            ], limit=1)
            
            if existing_sequence:
                if existing_sequence.prefix != sequence_prefix:
                    existing_sequence.sudo().write({'prefix': sequence_prefix})
                template.lot_sequence_id = existing_sequence
            else:
                # Crear nueva secuencia
                new_sequence = self.env['ir.sequence'].sudo().create({
                    'name': f"Lote {base_prefix} - {template.name}",
                    'code': sequence_code,
                    'implementation': 'standard',
                    'prefix': sequence_prefix,
                    'padding': 2,
                    'number_next': 1,
                    'number_increment': 1,
                    'use_date_range': False,
                    'company_id': template.company_id.id if template.company_id else False,
                })
                template.lot_sequence_id = new_sequence
            
            _logger.info(f"✓ Secuencia configurada para {template.name} | Prefijo: {sequence_prefix}")
    
    @api.depends('serial_prefix_format', 'lot_sequence_id', 'lot_sequence_id.number_next_actual')
    def _compute_next_serial(self):
        """
        Override para mostrar next_serial con formato procesado cuando aplica formato Amunet.
        
        Para productos con formato Amunet, muestra solo: mes + año + número (sin prefijo base)
        Ejemplo: Si prefijo = "XXX" y secuencia = 1, muestra "112501" (noviembre 2025, número 01)
        
        El prefijo base ya se muestra en el campo amunet_lot_prefix, así que aquí solo
        mostramos la parte variable (mes+año+número).
        """
        from datetime import datetime
        
        # Primero ejecutar lógica nativa para productos sin formato Amunet
        amunet_templates = self.filtered(lambda t: t._is_amunet_auto_lot_enabled())
        other_templates = self - amunet_templates
        
        if other_templates:
            super(ProductTemplate, other_templates)._compute_next_serial()
        
        # Para productos con formato Amunet, mostrar solo mes+año+número (sin prefijo base)
        now = datetime.now()
        month_str = now.strftime('%m')  # Mes con 2 dígitos (01-12)
        year_str = now.strftime('%y')   # Año sin siglo (25 para 2025)
        
        for template in amunet_templates:
            # Forzamos la limpieza del prefijo para el cálculo
            template._compute_amunet_lot_prefix()
            prefix = template.amunet_lot_prefix or ""
            
            if template.lot_sequence_id:
                # Obtener número con padding
                number_str = '{:0{}d}'.format(
                    template.lot_sequence_id.number_next_actual,
                    template.lot_sequence_id.padding
                )
                template.next_serial = f"{prefix}{month_str}{year_str}{number_str}"
            else:
                template.next_serial = f"{prefix}{month_str}{year_str}01"
    
    @api.constrains('serial_prefix_format', 'tracking')
    def _check_amunet_lot_config(self):
        """Validar que si tiene prefijo configurado, tenga tracking por lotes."""
        for template in self:
            if template.serial_prefix_format and template.tracking != 'lot':
                raise ValidationError(
                    _("El producto '%s' tiene configurado el prefijo de lote (Custom Lot/Serial) "
                      "pero debe tener 'Seguimiento por lotes' activado.") % template.name
                )
    
    def _inverse_serial_prefix_format(self):
        """
        Override del método nativo para crear/actualizar secuencia con formato Amunet.
        
        Cuando tracking='lot' y serial_prefix_format está configurado, el prefijo debe usar placeholders:
        Ejemplo: Si serial_prefix_format = "CRI", se crea secuencia con prefijo "CRI%(month)s%(y)s"
        
        Los placeholders se procesan automáticamente por Odoo:
        - %(month)s = mes con 2 dígitos (01-12)
        - %(y)s = año sin siglo (25 para 2025)
        
        IMPORTANTE: Para productos con tracking='lot' y serial_prefix_format configurado, 
        NO usamos la lógica nativa porque necesitamos crear secuencias con placeholders.
        
        SOLUCIÓN VISUAL: El campo serial_prefix_format siempre muestra solo el prefijo base
        (sin placeholders). Los placeholders solo se usan internamente en lot_sequence_id.prefix.
        """
        # Separar productos con formato Amunet (tracking='lot' + serial_prefix_format) y otros
        amunet_templates = self.filtered(lambda t: t.tracking == 'lot' and t.serial_prefix_format and t.serial_prefix_format.strip())
        other_templates = self - amunet_templates
        
        # Para productos sin formato Amunet, usar lógica nativa
        if other_templates:
            super(ProductTemplate, other_templates)._inverse_serial_prefix_format()
        
        # Para productos con formato Amunet, crear/actualizar secuencia con placeholders
        for template in amunet_templates:
            # Obtener el valor actual del campo
            raw_value = template.serial_prefix_format.strip()
            
            # Extraer el prefijo base eliminando placeholders si existen
            # Esto limpia valores como "CR8%(month)s%(y)s" -> "CR8"
            if '%(month)s' in raw_value:
                base_prefix = raw_value.split('%(month)s')[0]
            elif '%(y)s' in raw_value:
                base_prefix = raw_value.split('%(y)s')[0]
            else:
                base_prefix = raw_value
            
            if not base_prefix:
                continue
            
            # Si el campo tiene placeholders, limpiarlo para mostrar solo el prefijo base
            if raw_value != base_prefix:
                # Actualizar el campo directamente en la base de datos para evitar recursión
                self.env.cr.execute(
                    "UPDATE product_template SET serial_prefix_format = %s WHERE id = %s",
                    (base_prefix, template.id)
                )
                # Invalidar el cache para que se refleje el cambio
                template.invalidate_recordset(['serial_prefix_format'])
                _logger.info(
                    f"✓ Campo serial_prefix_format limpiado para {template.name} | "
                    f"Antes: {raw_value} | Después: {base_prefix}"
                )
            
            # Prefijo con placeholders: PREFIJO + %(month)s + %(y)s
            # Ejemplo: "CRI" -> "CRI%(month)s%(y)s"
            # Este prefijo SOLO se usa en la secuencia, NO en el campo visible
            sequence_prefix = f"{base_prefix}%(month)s%(y)s"
            
            # Buscar secuencia existente con este código (no por prefijo, porque el prefijo cambia cada mes)
            sequence_code = f"amunet.lot.{base_prefix}.{template.id}"
            existing_sequence = self.env['ir.sequence'].search([
                ('code', '=', sequence_code),
            ], limit=1)
            
            if existing_sequence:
                # Actualizar prefijo si cambió
                if existing_sequence.prefix != sequence_prefix:
                    existing_sequence.sudo().write({
                        'prefix': sequence_prefix,
                    })
                    _logger.info(
                        f"✓ Prefijo de secuencia actualizado para {template.name} | "
                        f"Prefijo: {sequence_prefix}"
                    )
                template.lot_sequence_id = existing_sequence
            else:
                # Crear nueva secuencia con prefijo con placeholders
                sequence_name = f"Lote {base_prefix} - {template.name}"
                
                new_sequence = self.env['ir.sequence'].sudo().create({
                    'name': sequence_name,
                    'code': sequence_code,
                    'implementation': 'standard',
                    'prefix': sequence_prefix,
                    'padding': 2,  # 2 dígitos: 01, 02, ..., 99
                    'number_next': 1,
                    'number_increment': 1,
                    'use_date_range': False,
                    'company_id': template.company_id.id if template.company_id else False,
                })
                
                template.lot_sequence_id = new_sequence
                _logger.info(
                    f"✓ Secuencia creada para {template.name} | "
                    f"Prefijo: {sequence_prefix} | ID: {new_sequence.id}"
                )
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create para generar secuencia automáticamente cuando aplica formato Amunet."""
        records = super().create(vals_list)
        
        # _inverse_serial_prefix_format ya se ejecuta automáticamente si serial_prefix_format está en vals
        # No necesitamos hacer nada adicional aquí
        
        return records
    
    def write(self, vals):
        """Override write para actualizar secuencia si cambia serial_prefix_format."""
        # Limpiar placeholders del serial_prefix_format antes de guardar
        if 'serial_prefix_format' in vals and vals['serial_prefix_format']:
            raw_value = vals['serial_prefix_format'].strip()
            # Extraer prefijo base eliminando placeholders
            if '%(month)s' in raw_value:
                vals['serial_prefix_format'] = raw_value.split('%(month)s')[0]
            elif '%(y)s' in raw_value:
                vals['serial_prefix_format'] = raw_value.split('%(y)s')[0]
        
        res = super().write(vals)
        
        # Si cambia serial_prefix_format o tracking, actualizar secuencia
        if 'serial_prefix_format' in vals or 'tracking' in vals:
            for record in self:
                if record._is_amunet_auto_lot_enabled() and record.lot_sequence_id:
                    # Obtener prefijo base limpio
                    raw_prefix = record.serial_prefix_format.strip() if record.serial_prefix_format else ''
                    if '%(month)s' in raw_prefix:
                        base_prefix = raw_prefix.split('%(month)s')[0]
                    elif '%(y)s' in raw_prefix:
                        base_prefix = raw_prefix.split('%(y)s')[0]
                    else:
                        base_prefix = raw_prefix
                    
                    if base_prefix:
                        new_prefix = f"{base_prefix}%(month)s%(y)s"
                        if record.lot_sequence_id.prefix != new_prefix:
                            record.lot_sequence_id.sudo().write({
                                'prefix': new_prefix,
                            })
                            _logger.info(
                                f"✓ Prefijo actualizado para {record.name} | "
                                f"Nuevo prefijo: {new_prefix}"
                            )
        
        return res
    
    def action_reset_amunet_lot_sequence(self):
        """Acción manual para reiniciar la secuencia del lote."""
        self.ensure_one()
        
        if not self.lot_sequence_id:
            raise ValidationError(_("Este producto no tiene secuencia de lotes configurada."))
        
        # Solo reiniciar el número, el prefijo con placeholders se procesa automáticamente
        self.lot_sequence_id.sudo().write({
            'number_next': 1,  # Reiniciar a 1
        })
        
        _logger.info(
            f"✓ Secuencia reiniciada manualmente para {self.name} | "
            f"number_next: 1"
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Secuencia reiniciada'),
                'message': _('La secuencia de lotes ha sido reiniciada correctamente.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    @api.model
    def _cron_reset_amunet_lot_sequences_monthly(self):
        """
        Cron job que se ejecuta diariamente para reiniciar secuencias el primer día del mes.
        
        Solo reinicia secuencias de productos que tengan amunet_lot_reset_monthly=True.
        
        IMPORTANTE: No actualiza el prefijo porque usa placeholders %(month)s%(y)s que se procesan
        automáticamente. Solo reinicia number_next a 1.
        """
        from datetime import datetime
        
        # Solo ejecutar el día 1 del mes
        today = datetime.now()
        if today.day != 1:
            _logger.debug("Cron ejecutado pero no es día 1 del mes, omitiendo reinicio")
            return
        
        _logger.info("=== INICIANDO REINICIO MENSUAL DE SECUENCIAS ===")
        
        # Buscar productos con reinicio mensual activado y formato Amunet
        products = self.search([
            ('tracking', '=', 'lot'),
            ('serial_prefix_format', '!=', False),
            ('amunet_lot_reset_monthly', '=', True),
            ('lot_sequence_id', '!=', False),
        ])
        
        if not products:
            _logger.info("No hay productos con reinicio mensual activado")
            return
        
        reset_count = 0
        
        for product in products:
            try:
                # Solo reiniciar number_next a 1
                # El prefijo con placeholders %(month)s%(y)s se procesa automáticamente
                product.lot_sequence_id.sudo().write({
                    'number_next': 1,
                })
                
                reset_count += 1
                
                _logger.info(
                    f"✓ Secuencia reiniciada | "
                    f"Producto: {product.name} | "
                    f"Prefijo: {product.lot_sequence_id.prefix} | "
                    f"number_next: 1"
                )
            except Exception as e:
                _logger.error(
                    f"Error reiniciando secuencia para {product.name}: {e}"
                )
        
        _logger.info(
            f"=== REINICIO MENSUAL COMPLETADO === | "
            f"Productos reiniciados: {reset_count} | "
            f"Total productos: {len(products)}"
        )
