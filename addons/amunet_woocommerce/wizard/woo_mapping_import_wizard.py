# -*- coding: utf-8 -*-

import base64
import csv
import io

from odoo import fields, models, _
from odoo.exceptions import UserError

EXPECTED_COLUMNS = {
    'woo_id', 'woo_sku', 'titulo', 'piezas', 'odoo_default_code',
    'odoo_track', 'odoo_use_exp', 'confianza', 'metodo', 'justificacion',
}

CONFIDENCE_MAP = {
    'alta': 'high',
    'media': 'medium',
    'baja': 'low',
}


class AmunetWooMappingImportWizard(models.TransientModel):
    """Importación idempotente del CSV de mapeo de SKU Woo ↔ Odoo.

    - Busca el producto Odoo por ``default_code`` exacto. Si no hay una única
      coincidencia, conserva el artículo Woo como mapeo pendiente sin producto.
    - Actualiza por tienda + ID Woo: reimportar el mismo archivo no duplica
      mapeos ni snapshots CSV.
    - ``piezas`` es inventario disponible observado, nunca equivalencia de caja.
    - Reporta creados, actualizados, no encontrados y errores, y deja
      registro en la bitácora.
    """

    _name = 'amunet.woo.mapping.import.wizard'
    _description = 'Importar mapeo de SKU Woo - Odoo (CSV)'

    company_id = fields.Many2one(
        'res.company', string='Compañía', required=True,
        default=lambda self: self.env.company)
    backend_id = fields.Many2one(
        'amunet.woo.backend', string='Tienda', required=True,
        domain="[('company_id', '=', company_id)]",
        help='Tienda a la que pertenecen los IDs Woo del archivo.')
    data_file = fields.Binary(string='Archivo CSV', required=True)
    filename = fields.Char(string='Nombre de archivo')
    snapshot_date = fields.Datetime(
        string='Fecha de observación del inventario',
        required=True,
        default=fields.Datetime.now,
        help='Momento en que se observaron las cantidades de la columna '
             '"piezas". No es necesariamente la fecha de importación.')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('done', 'Procesado'),
    ], default='draft', required=True)
    created_count = fields.Integer(string='Creados', readonly=True)
    updated_count = fields.Integer(string='Actualizados', readonly=True)
    not_found_count = fields.Integer(string='No encontrados', readonly=True)
    error_count = fields.Integer(string='Errores', readonly=True)
    report = fields.Text(string='Reporte', readonly=True)

    def _parse_rows(self):
        self.ensure_one()
        try:
            raw = base64.b64decode(self.data_file)
            text = raw.decode('utf-8-sig')
        except (ValueError, UnicodeDecodeError) as exc:
            raise UserError(_(
                'No se pudo leer el archivo como CSV UTF-8: %s') % exc)
        reader = csv.DictReader(io.StringIO(text))
        missing = EXPECTED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise UserError(_(
                'El CSV no tiene las columnas esperadas. Faltan: %s'
            ) % ', '.join(sorted(missing)))
        return list(reader)

    def _row_values(self, row, product):
        confianza = (row.get('confianza') or '').strip().lower()
        return {
            'backend_id': self.backend_id.id,
            'product_id': product.id if product else False,
            'woo_sku': (row.get('woo_sku') or '').strip(),
            'woo_name': (row.get('titulo') or '').strip(),
            'confidence': CONFIDENCE_MAP.get(confianza, 'unknown'),
            'match_method': (row.get('metodo') or '').strip(),
            'review_notes': (row.get('justificacion') or '').strip(),
            'relation_state': 'pending',
        }

    def _upsert_csv_snapshot(self, mapping, row):
        """Conserva un snapshot CSV por mapeo y fecha de observación.

        El archivo únicamente acredita la columna disponible. Las demás
        categorías permanecen explícitamente desconocidas. Reimportar la
        misma observación actualiza el registro; una fecha nueva conserva el
        histórico en un snapshot separado.
        """
        raw_pieces = (row.get('piezas') or '').strip()
        if not raw_pieces:
            return
        try:
            pieces = float(raw_pieces)
        except ValueError as exc:
            raise UserError(_('piezas inválidas: %s') % raw_pieces) from exc
        if pieces < 0:
            raise UserError(_('piezas no puede ser negativo: %s') % raw_pieces)
        Snapshot = self.env['amunet.woo.stock.snapshot']
        snapshot = Snapshot.search([
            ('mapping_id', '=', mapping.id),
            ('source', '=', 'csv'),
            ('date', '=', self.snapshot_date),
        ], order='date desc, id desc', limit=1)
        values = {
            'mapping_id': mapping.id,
            'source': 'csv',
            'date': self.snapshot_date,
            'available_known': True,
            'qty_available': pieces,
            'reserved_known': False,
            'expired_known': False,
            'damaged_known': False,
            'notes': _('Inventario disponible importado de %s.') % (
                self.filename or 'CSV'),
        }
        if snapshot:
            snapshot.write(values)
        else:
            Snapshot.create(values)

    def _upsert_mapping_row(self, Mapping, row, product, woo_id):
        values = self._row_values(row, product)
        mapping = Mapping.search([
            ('backend_id', '=', self.backend_id.id),
            ('woo_product_id', '=', woo_id),
            ('woo_parent_id', '=', 0),
        ], limit=1)
        created = not mapping
        if mapping:
            # Una fuente automática nunca deshace una decisión humana. Los
            # campos de revisión solo se refrescan mientras el vínculo sigue
            # pendiente y aún no tiene estampa de revisor.
            update_values = {
                key: values[key]
                for key in ('backend_id', 'woo_sku', 'woo_name')
            }
            if not mapping.reviewer_id and \
                    mapping.relation_state == 'pending':
                update_values.update({
                    key: values[key]
                    for key in (
                        'product_id', 'confidence', 'match_method',
                        'review_notes', 'relation_state',
                    )
                })
            mapping.with_context(skip_review_stamp=True).write(update_values)
        else:
            mapping = Mapping.create(dict(
                values,
                company_id=self.company_id.id,
                woo_product_id=woo_id,
                woo_parent_id=0,
            ))
        self._upsert_csv_snapshot(mapping, row)
        return created

    def action_import(self):
        """Procesa el CSV. Idempotente: actualiza por ID Woo."""
        self.ensure_one()
        rows = self._parse_rows()
        Product = self.env['product.product']
        Mapping = self.env['amunet.woo.product.mapping']
        created = updated = not_found = errors = 0
        messages = []
        for line_no, row in enumerate(rows, start=2):
            label = (row.get('woo_sku') or row.get('woo_id') or '?').strip()
            try:
                woo_id = int((row.get('woo_id') or '').strip())
            except ValueError:
                errors += 1
                messages.append(_('Línea %(n)s (%(l)s): woo_id inválido.',
                                  n=line_no, l=label))
                continue
            default_code = (row.get('odoo_default_code') or '').strip()
            products = Product.search([
                ('default_code', '=', default_code),
                ('company_id', 'in', [False, self.company_id.id]),
            ], limit=2) if default_code else Product.browse()
            product = products if len(products) == 1 else Product.browse()
            unresolved = not product
            if unresolved:
                not_found += 1
                reason = _('sin odoo_default_code') if not default_code else (
                    _('default_code "%s" ambiguo') % default_code
                    if len(products) > 1 else
                    _('no existe default_code "%s"') % default_code)
                messages.append(_(
                    'Línea %(n)s (%(l)s): %(reason)s; se conserva como '
                    'mapeo pendiente sin producto Odoo.',
                    n=line_no, l=label, reason=reason))
            try:
                with self.env.cr.savepoint():
                    was_created = self._upsert_mapping_row(
                        Mapping, row, product, woo_id)
                if was_created:
                    created += 1
                else:
                    updated += 1
            except Exception as exc:  # noqa: BLE001 - se reporta por línea
                errors += 1
                messages.append(_('Línea %(n)s (%(l)s): %(err)s',
                                  n=line_no, l=label, err=str(exc)[:300]))
        state = 'success' if not (not_found or errors) else (
            'partial' if (created or updated) else 'error')
        self.env['amunet.woo.sync.log'].create({
            'backend_id': self.backend_id.id,
            'company_id': self.company_id.id,
            'operation': 'csv_import',
            'state': state,
            'date_end': fields.Datetime.now(),
            'total_count': len(rows),
            'done_count': created + updated,
            'failed_count': errors,
            'message': _('Archivo: %(file)s\nCreados: %(c)s | Actualizados: '
                         '%(u)s | No encontrados: %(nf)s | Errores: %(e)s',
                         file=self.filename or '-', c=created, u=updated,
                         nf=not_found, e=errors),
        })
        self.write({
            'state': 'done',
            'created_count': created,
            'updated_count': updated,
            'not_found_count': not_found,
            'error_count': errors,
            'report': '\n'.join(messages) or _(
                'Todas las líneas se procesaron correctamente.'),
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back(self):
        self.write({'state': 'draft'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
