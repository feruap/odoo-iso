# -*- coding: utf-8 -*-
{
    "name": "Amunet Finiquito",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "author": "Amunet",
    "summary": "Estructura de salario para cálculo de finiquito según LFT (sin retenciones)",
    "depends": ["payroll", "amunet_nomina_control"],
    "data": [
        "data/finiquito_structure.xml",
        "views/hr_payslip_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
