# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Texto multilínea que se imprime tal cual en la sección "Contiene:"
    # de la etiqueta regulatoria de caja. Una línea por ítem, por
    # ejemplo:
    #   -10 Pruebas rápidas de COVID19 IgG/IgM
    #   -10 Goteros
    #   -10 Lancetas
    #   -10 Almohadillas con alcohol
    #   -Solución de corrimiento (buffer)
    #   -Instructivo de uso
    caja_contiene = fields.Text(
        string='Contenido de la caja (etiqueta)',
        help='Lista de items que aparece bajo "Contiene:" en la etiqueta '
             'regulatoria de la caja. Una linea por item. Se imprime tal '
             'cual; respeta el orden y los guiones.',
    )

    # Nombre corto que aparecera en la etiqueta de caja, distinto del
    # nombre largo regulatorio que vive en `name`. Si esta vacio, el
    # reporte cae al `name` del producto. Util para casos como:
    # name      = "Prueba rápida de AFP (Alfa-fetoproteína)"
    # nombre_etiqueta = "AFP"
    nombre_etiqueta = fields.Char(
        string='Nombre en etiqueta',
        help='Nombre corto/comercial que aparece en la etiqueta de caja. '
             'Si se deja vacio, en la etiqueta sale el nombre largo del '
             'producto (campo name).',
    )

    # ── Datos del catalogo de etiquetas (migrados desde Catalogo_final.xlsx) ──
    # Definen que plantilla PPTX usar y que datos extra lleva segun el subtipo.
    etiqueta_subtipo = fields.Selection(
        selection=[('S', 'S'), ('H', 'H'), ('P', 'P'), ('M', 'M')],
        string='Subtipo de etiqueta',
        help='Determina la plantilla PPTX (PLANTILLA_S/H/P/M) de la etiqueta de '
             'caja. H = lleva contenedor + accesorio; P = lleva registro sanitario.',
    )
    etiqueta_contenedor = fields.Char(
        string='Contenedor (etiqueta subtipo H)',
        help='Texto del contenedor en la etiqueta (solo subtipo H). '
             'Ej: "tubos de extraccion c/buffer".',
    )
    etiqueta_accesorio = fields.Char(
        string='Accesorio (etiqueta subtipo H)',
        help='Texto del accesorio en la etiqueta (solo subtipo H). Ej: "hisopos".',
    )
    registro_sanitario = fields.Char(
        string='Registro Sanitario',
        help='Numero de registro sanitario Cofepris; va en la etiqueta (subtipo P). '
             'Ej: "1820R2025 SSA".',
    )

    # Helper para condiciones de vista: True si el usuario actual es
    # Admin del modulo Etiquetas. Permite mostrar el campo en solo
    # lectura al Usuario y editable al Admin sin tener que llamar
    # user_has_groups() en attrs (no soportado en Odoo 19).
    is_label_manager_for_user = fields.Boolean(
        compute='_compute_is_label_manager_for_user',
        help='True si el usuario tiene el grupo Etiquetas / Administrador. '
             'Se usa solo para condiciones de UI.',
    )

    @api.depends_context('uid')
    def _compute_is_label_manager_for_user(self):
        is_mgr = self.env.user.has_group(
            'amunet_label.group_label_manager')
        for rec in self:
            rec.is_label_manager_for_user = is_mgr
