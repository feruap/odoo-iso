import base64
import io
from odoo import models, fields
from odoo.exceptions import UserError


def _build_excel(label, filas, fecha, sin_clabe=None):
    try:
        import xlsxwriter
    except ImportError:
        raise UserError('Falta la librería xlsxwriter. Avisa a desarrollo.')

    buf = io.BytesIO()
    wb = xlsxwriter.Workbook(buf, {'in_memory': True})
    ws = wb.add_worksheet('Lista 1 - Nomina')

    ws.set_column(0, 0, 38)
    ws.set_column(1, 1, 18)
    ws.set_column(2, 2, 22)
    ws.set_column(3, 3, 12)

    fmt_titulo       = wb.add_format({'bold': True, 'font_size': 12})
    fmt_header       = wb.add_format({'bold': True})
    fmt_texto        = wb.add_format({'num_format': '@'})
    fmt_bold_texto   = wb.add_format({'bold': True, 'num_format': '@'})
    fmt_bold_num     = wb.add_format({'bold': True})
    fmt_sin_clabe    = wb.add_format({'num_format': '@', 'bg_color': '#FFFF00'})
    fmt_bold_sc      = wb.add_format({'bold': True, 'num_format': '@', 'bg_color': '#FFFF00'})
    fmt_aviso        = wb.add_format({'bold': True, 'font_color': 'red'})

    ws.write(0, 0, 'DISPERSIÓN — %s — %s' % (label.upper(), fecha), fmt_titulo)
    for col, enc in enumerate(['EMPLEADO', 'BANCO', 'CLABE', 'MONTO']):
        ws.write(1, col, enc, fmt_header)

    for idx, (nombre, banco, clabe, monto, nuevo_ingreso) in enumerate(filas):
        fila = idx + 2
        fmt_n  = fmt_bold_num   if nuevo_ingreso else None
        fmt_c  = (fmt_bold_sc if nuevo_ingreso else fmt_sin_clabe) if not clabe else \
                 (fmt_bold_texto if nuevo_ingreso else fmt_texto)
        ws.write(fila, 0, nombre, fmt_n)
        ws.write(fila, 1, banco,  fmt_n)
        ws.write_string(fila, 2, clabe, fmt_c)
        ws.write_number(fila, 3, monto, fmt_n)

    total = sum(r[3] for r in filas)
    fila_total = len(filas) + 2
    ws.write(fila_total, 2, 'TOTAL', fmt_bold_texto)
    ws.write_number(fila_total, 3, total, fmt_bold_num)

    if sin_clabe:
        fila_av = fila_total + 2
        ws.write(fila_av, 0, '⚠ Sin CLABE (revisar antes de enviar al banco):', fmt_aviso)
        for i, nombre in enumerate(sin_clabe):
            ws.write(fila_av + 1 + i, 0, '  • ' + nombre)

    wb.close()
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


class DispersionWizard(models.TransientModel):
    _name = 'amunet.dispersion.wizard'
    _description = 'Generar archivos de dispersión'

    nombre_nomina = fields.Char(string='Archivo Nómina')
    archivo_nomina = fields.Binary(string='Nómina', readonly=True)
    nombre_honorarios = fields.Char(string='Archivo Honorarios')
    archivo_honorarios = fields.Binary(string='Honorarios', readonly=True)
    resumen = fields.Char(string='Resumen', readonly=True)
    advertencia = fields.Char(string='Advertencia', readonly=True)

    def action_descargar_nomina(self):
        att = self.env['ir.attachment'].create({
            'name': self.nombre_nomina,
            'type': 'binary',
            'datas': self.archivo_nomina,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % att.id,
            'target': 'self',
        }

    def action_descargar_honorarios(self):
        att = self.env['ir.attachment'].create({
            'name': self.nombre_honorarios,
            'type': 'binary',
            'datas': self.archivo_honorarios,
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d?download=true' % att.id,
            'target': 'self',
        }


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_generar_dispersion(self):
        self.ensure_one()
        grupo1, grupo2 = [], []
        sin_clabe_nomina, sin_clabe_honorarios = [], []

        # Empleados con ingreso en los últimos 30 días (para marcar en negritas)
        from datetime import date, timedelta
        corte_nuevo = date.today() - timedelta(days=30)

        for slip in self.slip_ids:
            emp = slip.employee_id
            net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
            neto = float(net_line[0].total) if net_line else 0.0

            bank = emp.bank_account_ids[:1] if emp.bank_account_ids else self.env['res.partner.bank']
            clabe = bank.acc_number if bank else ''
            banco = bank.bank_id.name if bank and bank.bank_id else ''

            # Nuevo ingreso: fecha de creación del empleado en los últimos 30 días
            nuevo = emp.create_date and emp.create_date.date() >= corte_nuevo

            row = (emp.name, banco, clabe, neto, nuevo)

            # Separar por estructura salarial del recibo (no por nombre hardcodeado)
            struct_name = (slip.struct_id.name or '').lower()
            if 'nomina' in struct_name or 'nómina' in struct_name:
                grupo1.append(row)
                if not clabe:
                    sin_clabe_nomina.append(emp.name)
            else:
                grupo2.append(row)
                if not clabe:
                    sin_clabe_honorarios.append(emp.name)

        grupo1.sort(key=lambda x: x[0])
        grupo2.sort(key=lambda x: x[0])

        fecha = '%s al %s' % (
            self.date_start.strftime('%d/%m/%Y'),
            self.date_end.strftime('%d/%m/%Y'),
        )
        sfecha = '%s_%s' % (
            self.date_start.strftime('%d%m%Y'),
            self.date_end.strftime('%d%m%Y'),
        )

        advertencia = ''
        todos_sin_clabe = sin_clabe_nomina + sin_clabe_honorarios
        if todos_sin_clabe:
            advertencia = '⚠ Sin CLABE: %s' % ', '.join(todos_sin_clabe)

        wizard = self.env['amunet.dispersion.wizard'].create({
            'nombre_nomina': 'Dispersion_Nomina_%s.xlsx' % sfecha,
            'archivo_nomina': _build_excel('Nómina', grupo1, fecha, sin_clabe_nomina),
            'nombre_honorarios': 'Dispersion_Honorarios_%s.xlsx' % sfecha,
            'archivo_honorarios': _build_excel('Honorarios', grupo2, fecha, sin_clabe_honorarios),
            'resumen': 'Nómina: %d empleados  |  Honorarios: %d empleados' % (
                len(grupo1), len(grupo2)),
            'advertencia': advertencia,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Archivos de dispersión',
            'res_model': 'amunet.dispersion.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
        }
