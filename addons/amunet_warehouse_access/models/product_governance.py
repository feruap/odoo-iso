# -*- coding: utf-8 -*-
from odoo import models, api, _
from odoo.exceptions import UserError

# Mensaje unico para no duplicar texto
_MSG_NO_ALTA_AL_VUELO = (
    "No se puede crear un producto 'al vuelo' aquí.\n\n"
    "Para evitar duplicados y productos mal codificados, el alta de un producto "
    "nuevo se hace primero en Inventario > Productos (solo Karla, Vero o Mery), "
    "con su código y categoría correctos. Luego selecciónalo en este campo."
)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def name_create(self, name):
        # Bloquea el "crear al vuelo" (quick create) en CUALQUIER campo/vista.
        # La creacion formal (con todos sus datos) sigue disponible en la app
        # Productos para quien tenga permiso de alta.
        raise UserError(_(_MSG_NO_ALTA_AL_VUELO))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_create(self, name):
        raise UserError(_(_MSG_NO_ALTA_AL_VUELO))
