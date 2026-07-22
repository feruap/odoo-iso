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


_MSG_NO_ALTA_AGENTE = (
    "Creación de producto bloqueada para procesos automáticos.\n\n"
    "Un proceso automático o agente (superusuario) NO puede crear productos "
    "'al vuelo' ni al cargar/importar órdenes de compra. El alta de un producto "
    "es un acto autorizado: se hace en Inventario > Productos (Karla, Vero o "
    "Mery) con su clave y categoría. Si Fernando solicita un alta, debe hacerse "
    "de forma explícita y autorizada (contexto 'amunet_alta_autorizada')."
)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def name_create(self, name):
        # Bloquea el "crear al vuelo" (quick create) en CUALQUIER campo/vista.
        # La creacion formal (con todos sus datos) sigue disponible en la app
        # Productos para quien tenga permiso de alta.
        raise UserError(_(_MSG_NO_ALTA_AL_VUELO))

    @api.model_create_multi
    def create(self, vals_list):
        # Candado: un proceso automatico / agente (superusuario) NO puede crear
        # productos al vuelo ni al cargar compras. Los usuarios reales con
        # permiso de alta (grupo Create: Karla/Vero/Mery) NO son superusuario,
        # asi que siguen pudiendo desde la app Productos.
        # - Exento durante instalacion/actualizacion de modulos (registry no
        #   lista) para no romper datos semilla de los addons.
        # - Exento si se pide un alta EXPLICITA y autorizada (flag de contexto),
        #   que es como el agente da de alta cuando Fernando lo solicita.
        if (self.env.registry.ready
                and not self.env.context.get('amunet_alta_autorizada')):
            # 1) Procesos automaticos / agentes (superusuario): siempre
            #    bloqueados sin autorizacion explicita (aunque __system__
            #    figure en el grupo Create).
            if self.env.su:
                raise UserError(_(_MSG_NO_ALTA_AGENTE))
            # 2) Solo el grupo Create (Karla/Vero/Mery, product manager) puede
            #    dar de alta. Cierra el residual: importaciones de OC u otros
            #    usuarios NO pueden crear productos.
            if not self.env.user.has_group('product.group_product_manager'):
                raise UserError(_(_MSG_NO_ALTA_AL_VUELO))
        return super().create(vals_list)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def name_create(self, name):
        raise UserError(_(_MSG_NO_ALTA_AL_VUELO))
