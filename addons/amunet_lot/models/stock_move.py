# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'
    
    # Campo para el widget de generación de lotes de Odoo.
    # Lo mantenemos como un campo normal pero computado para sincronización inicial.
    next_serial = fields.Char(
        'First SN/Lot', 
        compute='_compute_next_serial', 
        store=True,
        readonly=False,
        inverse='_inverse_next_serial'
    )
    
    @api.depends('product_id', 'product_id.next_serial')
    def _compute_next_serial(self):
        """
        Sincroniza el campo next_serial del movimiento con el del producto.
        """
        for move in self:
            if move.product_id and not move.next_serial:
                move.next_serial = move.product_id.next_serial

    def _inverse_next_serial(self):
        pass

    # Campos técnicos para desactivar el prefijo nativo si es Amunet
    display_assign_serial = fields.Boolean(compute='_compute_display_assign_serial')

    @api.depends('product_id')
    def _compute_display_assign_serial(self):
        super(StockMove, self)._compute_display_assign_serial()
        for move in self:
            if move.product_id and move.product_id.tracking == 'lot':
                # Si es un producto Amunet, queremos que Odoo use el next_serial completo
                # No queremos que intente concatenar prefijos.
                pass

    def _inverse_next_serial(self):
        """
        Si el usuario cambia el número de serie manualmente en el widget,
        intentamos respetar el valor (aunque Amunet prefiere seguir su secuencia).
        """
        for move in self:
            # No guardamos nada en el move porque es store=False,
            # pero el widget de Odoo leerá el valor que se le asigne durante la sesión.
            pass
    
    def action_show_details(self):
        """
        Override para crear automáticamente una línea con lote cuando se abre el modal de detalles.
        
        CORRECCIÓN CRÍTICA: 
        - Restaura el comportamiento esperado donde al abrir "Detalles" aparece una línea editable
        - Genera el lote automáticamente si el producto tiene secuencia Amunet configurada
        - Garantiza compatibilidad con la generación automática de QC
        """
        self.ensure_one()
        
        # Si no hay líneas de movimiento Y el producto requiere tracking, crear una línea inteligente
        if not self.move_line_ids and self.product_uom_qty > 0:
            # Preparar valores base usando el método nativo
            vals = self._prepare_move_line_vals(quantity=0)
            
            # Si el producto tiene tracking de lote/serie, generar el lote automáticamente
            if self.product_id.tracking in ['lot', 'serial']:
                # Intentar generar usando la secuencia Amunet si existe
                if self.product_id.lot_sequence_id:
                    lot_name = self.product_id.lot_sequence_id.next_by_id()
                    
                    # Buscar o crear el lote
                    lot = self.env['stock.lot'].search([
                        ('name', '=', lot_name),
                        ('product_id', '=', self.product_id.id),
                        ('company_id', '=', self.company_id.id)
                    ], limit=1)
                    
                    if not lot:
                        lot = self.env['stock.lot'].create({
                            'name': lot_name,
                            'product_id': self.product_id.id,
                            'company_id': self.company_id.id,
                        })
                    
                    # Asignar el lote a la línea
                    vals['lot_id'] = lot.id
                    vals['lot_name'] = lot_name
                    
                    # Establecer quantity a 1.0 para productos con tracking individual
                    if self.product_id.tracking == 'serial':
                        vals['quantity'] = 1.0
                    else:
                        # Para tracking por lote, usar la cantidad demandada
                        vals['quantity'] = self.product_uom_qty
            else:
                # Sin tracking, usar la cantidad demandada
                vals['quantity'] = self.product_uom_qty
            
            # Crear la línea
            self.env['stock.move.line'].create(vals)
        
        # Continuar con el comportamiento estándar
        return super().action_show_details()


    def action_generate_serial(self, next_serial, count=1, fetch_next_serial=False, **kwargs):
        """
        Override para generar números de serie/lote.
        Reimplementado para asegurar compatibilidad con Odoo 17 (quantity vs qty_done)
        y evitar que las líneas desaparezcan.
        """
        self.ensure_one()
        
        # 1. Determinar el serial inicial
        if not next_serial:
            next_serial = self.next_serial or self.product_id.next_serial
            
        if not next_serial:
            # Si aún no hay serial, intentar generarlo
            # Odoo 17 standard helper
            next_serial = self.env['stock.lot'].generate_lot_names(self.product_id.id, count=1)[0]
            
        # 2. Generar nombres
        serial_names = []
        
        if self.product_id.lot_sequence_id:
            # Lógica Amunet: Usar la secuencia configurada en el producto
            for _ in range(count):
                serial_names.append(self.product_id.lot_sequence_id.next_by_id())
        else:
            # Fallback nativo
            serial_names = self.env['stock.lot'].generate_lot_names(self.product_id.id, count=count, first_lot=next_serial)
        
        # 3. Mapear líneas existentes a actualizar
        lines_to_update = self.move_line_ids.filtered(lambda l: not l.lot_id and not l.lot_name and (l.quantity == 0 or l.quantity == 1))
        
        vals_list = []
        for i, name in enumerate(serial_names):
            # Asegurar que el lote exista (para asignarlo por ID y evitar ambigüedades)
            lot = self.env['stock.lot'].search([
                ('name', '=', name),
                ('product_id', '=', self.product_id.id),
                ('company_id', '=', self.company_id.id)
            ], limit=1)
            
            if not lot:
                lot = self.env['stock.lot'].create({
                    'name': name,
                    'product_id': self.product_id.id,
                    'company_id': self.company_id.id,
                })

            # Si hay una línea vacía disponible, la actualizamos
            if i < len(lines_to_update):
                line = lines_to_update[i]
                line.write({
                    'lot_id': lot.id,
                    'lot_name': name,
                    'quantity': 1.0
                })
            else:
                # Crear nueva línea
                vals = {
                    'move_id': self.id,
                    'product_id': self.product_id.id,
                    'product_uom_id': self.product_uom.id,
                    'location_id': self.location_id.id,
                    'location_dest_id': self.location_dest_id.id,
                    'picking_id': self.picking_id.id,
                    'company_id': self.company_id.id,
                    'lot_id': lot.id,
                    'lot_name': name,
                    'quantity': 1.0,
                }
                vals_list.append(vals)
                
        if vals_list:
            self.env['stock.move.line'].create(vals_list)
            
        # Actualizar next_serial en el move y producto
        if serial_names:
            last_serial = serial_names[-1]
            try:
                next_generated = self.env['stock.lot'].generate_lot_names(self.product_id.id, count=1, first_lot=last_serial)[0]
                self.next_serial = next_generated
            except Exception:
                pass
            
        # No retornamos reload para evitar que el diálogo se cierre mal o se pierdan cambios en el formulario principal
        return True


    @api.model
    def generate_factory_lots_for_lines(self, move_line_ids):
        """
        Genera lotes de fábrica para las líneas especificadas.
        
        Crea un factory_lot por cada lote Amunet y los asocia automáticamente.
        
        EPIC-031 T-031-6: Método llamado desde el widget de generación de factory lots.
        
        Args:
            move_line_ids: Lista de IDs de stock.move.line
            
        Returns:
            dict: Resultado de la operación con contador de lotes creados
        """
        if not move_line_ids:
            raise UserError(_("No se proporcionaron líneas de movimiento."))
        
        lines = self.env['stock.move.line'].browse(move_line_ids)
        
        # Filtrar líneas que tienen lote pero no factory_lot
        lines_needing_factory_lot = lines.filtered(
            lambda l: l.lot_id and not l.factory_lot_id
        )
        
        if not lines_needing_factory_lot:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sin lotes para procesar'),
                    'message': _('Todas las líneas ya tienen lotes de fábrica asignados o no tienen lotes Amunet.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Generar nombres secuenciales únicos
        existing_factory_lots = self.env['amunet.lot.factory'].search([
            ('name', 'like', 'LOTEF%')
        ], order='name desc', limit=1)
        
        # Determinar el siguiente número
        if existing_factory_lots:
            try:
                last_number = int(existing_factory_lots[0].name.replace('LOTEF', ''))
                counter = last_number + 1
            except ValueError:
                counter = 1
        else:
            counter = 1
        
        created_count = 0
        for line in lines_needing_factory_lot:
            # Generar nombre secuencial único
            factory_lot_name = f"LOTEF{counter:02d}"
            
            # Verificar unicidad (por si acaso)
            while self.env['amunet.lot.factory'].search([('name', '=', factory_lot_name)], limit=1):
                counter += 1
                factory_lot_name = f"LOTEF{counter:02d}"
            
            # Crear lote de fábrica
            factory_lot = self.env['amunet.lot.factory'].create({
                'name': factory_lot_name,
                'ref': f'Auto-generado para {line.lot_id.name}',
            })
            
            # Asociar a línea
            line.factory_lot_id = factory_lot.id
            
            _logger.info(
                f"✓ Factory lot creado: {factory_lot_name} | "
                f"Asociado a lote Amunet: {line.lot_id.name} | "
                f"Línea: {line.id}"
            )
            
            counter += 1
            created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Lotes de fábrica generados'),
                'message': _('Se generaron %d lotes de fábrica correctamente.') % created_count,
                'type': 'success',
                'sticky': False,
            }
        }
