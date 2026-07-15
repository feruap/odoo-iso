from . import models


def post_init_hook(env):
    """Asigna usuarios a los grupos del módulo y activa PDF en manuales aprobados."""
    def _add(group_xmlid, logins):
        group = env.ref(group_xmlid, raise_if_not_found=False)
        if not group:
            return
        for login in logins:
            user = env['res.users'].sudo().search(
                [('login', '=', login), ('active', '=', True)], limit=1)
            if user:
                group.sudo().write({'users': [(4, user.id)]})

    _add('amunet_documentacion_compartida.group_doc_revisor', [
        'ensayo@amunet.com.mx',            # Jorge
        's.controldecalidad@amunet.com.mx', # Diana
        'analista1cc@amunet.com.mx',        # Gabriela
        'analista2cc@amunet.com.mx',        # Rodrigo
    ])
    _add('amunet_documentacion_compartida.group_doc_validacion', [
        'ensayo@amunet.com.mx',            # Jorge
        'fernando.ruiz@amunet.com.mx',     # Fernando
        'desarrollo@amunet.com.mx',        # Mery
    ])
    _add('amunet_documentacion_compartida.group_doc_compartida_user', [
        'documentacion@amunet.com.mx',     # Stacy
        'desarrollo@amunet.com.mx',        # Mery
        'fernando.ruiz@amunet.com.mx',     # Fernando
    ])

    # Manuales ya aprobados quedan disponibles para visores desde el arranque
    env['amunet.doc.compartida'].sudo().search(
        [('state', '=', 'aprobado')]
    ).write({'pdf_disponible': True})
