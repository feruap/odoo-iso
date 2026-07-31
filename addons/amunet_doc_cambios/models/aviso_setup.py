from odoo import models, api

# UIDs fijos: Alma (71) y Alondra (72)
_AVISO_PRODUCCION_UIDS = [71, 72]


class AmunetAvisoSetup(models.AbstractModel):
    _name = 'amunet.aviso.setup'
    _description = 'Inicializacion de grupo Avisos Produccion'

    @api.model
    def seed_produccion_users(self):
        """Asegura que Alma y Alondra estén en el grupo de Producción autorizada."""
        group = self.env.ref(
            'amunet_doc_cambios.group_aviso_produccion_user',
            raise_if_not_found=False,
        )
        if group:
            group.write({'user_ids': [(4, uid) for uid in _AVISO_PRODUCCION_UIDS]})
