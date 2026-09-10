# -*- coding: utf-8 -*-
"""Las tabletas de kiosco solo ven lo que necesitan para fabricar.

Un dispositivo de kiosco hereda sus permisos de 'Fabricante de Soluciones',
el mismo grupo que tienen Julissa y Alondra. Ese grupo arrastra Inventario,
Solicitudes de Material y demas, que ELLAS si necesitan desde su cuenta pero
la tableta compartida no.

Por eso no se tocan los grupos: se ocultan los MENUS solo para el kiosco. La
tableta conserva el acceso tecnico que la fabricacion requiere (stock y mrp
por debajo) y pierde las aplicaciones que no le tocan.
"""

from odoo import api, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    # Menus raiz que un dispositivo de kiosco NO debe ver. Se oculta el menu
    # completo, con todos sus hijos.
    KIOSCO_MENUS_OCULTOS = (
        'stock.menu_stock_root',
        'hr_holidays.menu_hr_holidays_root',
        'amunet_material_request.menu_amunet_material_request_root',
        'amunet_marketplace.menu_amunet_marketplace_root',
        'amunet_mi_produccion.menu_amunet_mi_root',
        # Aplicaciones de escritorio que no le tocan a una tableta de piso.
        # 'Apps' no les deja instalar nada (no son administradores), pero no
        # tiene por que estar a la vista en un dispositivo compartido.
        'base.menu_management',
        'contacts.menu_contacts',
        'calendar.mail_menu_calendar',
        'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
    )

    @api.model
    def _visible_menu_ids(self, debug=False):
        # El super esta cacheado por conjunto de grupos del usuario, asi que
        # lo pesado sigue resolviendose una sola vez. Lo de aqui es una resta
        # de conjuntos.
        visibles = super()._visible_menu_ids(debug=debug)
        if not self.env.user.has_group(
                'amunet_soluciones_kiosco.group_kiosco_soluciones'):
            return visibles

        ocultos = set()
        IMD = self.env['ir.model.data'].sudo()
        for xmlid in self.KIOSCO_MENUS_OCULTOS:
            raiz = IMD._xmlid_to_res_id(xmlid, raise_if_not_found=False)
            if not raiz:
                continue
            # El menu y todo lo que cuelga de el.
            ocultos.update(
                self.sudo().with_context(active_test=False)
                .search([('id', 'child_of', raiz)]).ids)

        return frozenset(visibles - ocultos)
