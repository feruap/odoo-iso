def migrate(cr, version):
    cr.execute("""
        INSERT INTO res_groups_users_rel (gid, uid)
        SELECT imd.res_id, ru.id
        FROM ir_model_data imd, res_users ru
        WHERE imd.module = 'amunet_documentos'
          AND imd.name = 'group_prueba_rapida_editor'
          AND imd.model = 'res.groups'
          AND ru.login = 'documentacion@amunet.com.mx'
        ON CONFLICT DO NOTHING
    """)
