from odoo import models, api

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre',
}


class ReportCcAnual(models.AbstractModel):
    _name = 'report.amunet_cc_general.report_cc_anual_template'
    _description = 'Registro Anual de Controles de Cambio'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['amunet.cc.general'].browse(docids).sorted(
            key=lambda r: r.fecha_solicitud or r.create_date.date()
        )

        years = {}
        for cc in docs:
            fecha = cc.fecha_solicitud or cc.create_date.date()
            year = fecha.year
            month = fecha.month
            if year not in years:
                years[year] = {m: [] for m in range(1, 13)}
            years[year][month].append(cc)

        docs_grouped_by_year = []
        for year in sorted(years.keys()):
            months = []
            for m in range(1, 13):
                months.append({
                    'nombre': MESES[m],
                    'records': years[year][m],
                })
            total = sum(len(m['records']) for m in months)
            docs_grouped_by_year.append({
                'year': year,
                'months': months,
                'total': total,
            })

        return {
            'doc_ids': docids,
            'doc_model': 'amunet.cc.general',
            'docs': docs,
            'docs_grouped_by_year': docs_grouped_by_year,
        }
