for nombre in ['Mery','Stacy','Stacey','Diana','Moctezuma','Verónica']:
    usuarios = env['res.users'].search([
        ('name','ilike',nombre), ('share','=',False)
    ])
    for u in usuarios:
        print(f"{u.name} | {u.login} | {u.email or '(sin email)'}")
