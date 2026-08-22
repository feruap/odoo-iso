import base64
import io
from odoo import models
from odoo.exceptions import UserError

# IDs de empleados que van en la lista de Nómina (más robusto que comparar nombres)
GRUPO1_IDS = {
    193,  # Stacy Abigail Palma Ramos
    195,  # Verónica Ortiz Moncada
    196,  # Alma Delia Bueno Garista
    197,  # Alondra Guadalupe Sánchez Martínez
    200,  # Verónica Natalia Perez Ruiz
    202,  # Patricia García Soto
    203,  # Diana Flores Vera
    209,  # Edgar Michel Salamanca Aguilar
}


class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    def action_generar_dispersion(self):
        try:
            import xlsxwriter
        except ImportError:
            raise UserError('Falta la librería xlsxwriter. Avisa a desarrollo.')

        grupo1, grupo2 = [], []

        for slip in self.slip_ids:
            emp = slip.employee_id
            net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
            neto = net_line[0].total if net_line else 0.0

            bank = self.env['res.partner.bank'].search(
                [('partner_id', '=', emp.work_contact_id.id)], limit=1
            )
            clabe = bank.acc_number if bank else ''
            banco = bank.bank_id.name if bank and bank.bank_id else ''

            row = (emp.name, banco, clabe, float(neto))
            if emp.id in GRUPO1_IDS:
                grupo1.append(row)
            else:
                grupo2.append(row)

        grupo1.sort(key=lambda x: x[0])
        grupo2.sort(key=lambda x: x[0])

        fecha = '%s al %s' % (
            self.date_start.strftime('%d/%m/%Y'),
            self.date_end.strftime('%d/%m/%Y'),
        )

        att_ids = []
        for label, filas in [('Nomina', grupo1), ('Honorarios', grupo2)]:
            buf = io.BytesIO()
            wb = xlsxwriter.Workbook(buf, {'in_memory': True})
            ws = wb.add_worksheet('Lista 1 - Nomina')
            ws.write(0, 4, 'XLSXWRITER-V2')  # marca de version — borrar despues

            ws.set_column(0, 0, 38)
            ws.set_column(1, 1, 18)
            ws.set_column(2, 2, 22)
            ws.set_column(3, 3, 12)

            fmt_titulo = wb.add_format({'bold': True, 'font_size': 12})
            fmt_header = wb.add_format({'bold': True})
            fmt_texto = wb.add_format({'num_format': '@'})
            fmt_bold_texto = wb.add_format({'bold': True, 'num_format': '@'})

            ws.write(0, 0, 'DISPERSIÓN — %s — %s' % (label.upper(), fecha), fmt_titulo)
            for col, encabezado in enumerate(['EMPLEADO', 'BANCO', 'CLABE', 'MONTO']):
                ws.write(1, col, encabezado, fmt_header)

            for idx, (nombre, banco_n, clabe, monto) in enumerate(filas):
                fila = idx + 2
                ws.write(fila, 0, nombre)
                ws.write(fila, 1, banco_n)
                ws.write_string(fila, 2, clabe, fmt_texto)
                ws.write_number(fila, 3, monto)

            total = sum(r[3] for r in filas)
            fila_total = len(filas) + 2
            ws.write(fila_total, 2, 'TOTAL', fmt_bold_texto)
            ws.write_number(fila_total, 3, total, fmt_header)

            wb.close()
            buf.seek(0)

            nombre_archivo = 'Dispersion_%s_%s_%s.xlsx' % (
                label,
                self.date_start.strftime('%d%m%Y'),
                self.date_end.strftime('%d%m%Y'),
            )
            att = self.env['ir.attachment'].create({
                'name': nombre_archivo,
                'type': 'binary',
                'datas': base64.b64encode(buf.read()).decode(),
                'res_model': 'hr.payslip.run',
                'res_id': self.id,
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            att_ids.append(att.id)

        return {
            'type': 'ir.actions.act_window',
            'name': 'Archivos de dispersión',
            'res_model': 'ir.attachment',
            'view_mode': 'list',
            'domain': [('id', 'in', att_ids)],
            'target': 'new',
        }
