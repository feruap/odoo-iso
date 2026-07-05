# -*- coding: utf-8 -*-
{
    "name": "Amunet Control de Nomina (anti-fraude)",
    "version": "19.0.1.0.0",
    "category": "Human Resources",
    "author": "Amunet",
    "summary": "Doble firma para cambios de cuenta bancaria, deteccion de CLABE duplicada y segregacion de funciones",
    "depends": ["hr", "payroll", "amunet_quality"],
    "data": [
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/bank_change_request_views.xml",
        "views/hr_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
