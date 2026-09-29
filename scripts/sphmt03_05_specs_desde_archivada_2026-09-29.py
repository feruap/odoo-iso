"""SPHMT03/04/05: pone las especificaciones de calidad en la ficha VIVA.

Pedido por Diana el 29-sep-2026 (msg 17:41) y autorizado por Mery.

EL PROBLEMA: cada una de estas tres hojas existe DOS VECES en el sistema, con la misma
clave. La ficha vieja quedo archivada y se llevo las especificaciones; la nueva esta
activa, tiene el BoM con el que se va a fabricar, y no tiene ninguna. Sin
especificaciones el producto no es analizable.

    SPHMT03  Hoja Maestra VPH        archivada 1507 -> viva 2377 (BoM 296)
    SPHMT04  Hoja Maestra Pylorinet  archivada 1508 -> viva 2378 (BoM 297)
    SPHMT05  Hoja Maestra TB-DxNet   archivada 1509 -> viva 2379 (BoM 298)

La archivada NO se toca: conserva su analisis historico y sus 3 movimientos.

DEFORMIDAD VA UNA SOLA VEZ: lo confirmo Diana. El estandar de MAVI-04 son 3 renglones
(Manchas y/o suciedad, Rasgaduras, Deformidad o deterioro). En las archivadas el
duplicado de Deformidad y el renglon 'Adecuado' ya estan desactivados, asi que se copia
lo ACTIVO y el duplicado no viaja.

POR QUE SE DESACTIVA Y NO SE BORRA: al crear una relacion de parametro, el modulo
autogenera un renglon por CADA especificacion del catalogo de ese parametro -- MAVI-04
trae tambien Letra, Sellado y demas, que a una hoja maestra no le aplican. Es el mismo
defecto que dejo 23 renglones ajenos en las hojas CM esta manana. Aqui se hace igual que
alla: los que no estan en la archivada se DESACTIVAN, no se borran, porque borrar un
renglon del catalogo rompe el historico de cualquier analisis que lo haya usado.

Idempotente: se puede correr dos veces sin duplicar ni revivir nada.
"""
Rel = env['amunet.quality.parameter.product.rel'].sudo()
Cfg = env['amunet.quality.parameter.specification.config'].sudo()
RelX = Rel.with_context(active_test=False)
CfgX = Cfg.with_context(active_test=False)

PARES = ((1507, 2377, 'SPHMT03'), (1508, 2378, 'SPHMT04'), (1509, 2379, 'SPHMT05'))

# los campos de configuracion que se copian tal cual; se excluye lo que Odoo calcula
# solo (related, compute) y lo que identifica al registro
EXCLUIR = {'id', 'product_parameter_rel_id', 'product_tmpl_id', 'parameter_id',
           'company_id', 'create_uid', 'create_date', 'write_uid', 'write_date',
           'display_name', '__last_update'}
COPIABLES = [n for n, f in Cfg._fields.items()
             if f.store and not f.related and not f.compute and n not in EXCLUIR]

def valores(cfg):
    v = {}
    for n in COPIABLES:
        f = Cfg._fields[n]
        val = cfg[n]
        if f.type == 'many2one':
            v[n] = val.id or False
        elif f.type in ('one2many', 'many2many'):
            v[n] = [(6, 0, val.ids)]
        else:
            v[n] = val
    return v

for viejo, nuevo, clave in PARES:
    print('=== %s   archivada %s -> viva %s' % (clave, viejo, nuevo))
    for rel_v in RelX.search([('product_tmpl_id', '=', viejo), ('active', '=', True)]):
        param = rel_v.parameter_id
        rel_n = RelX.search([('product_tmpl_id', '=', nuevo),
                             ('parameter_id', '=', param.id)], limit=1)
        if not rel_n:
            # el create autogenera un renglon por cada especificacion del catalogo
            rel_n = Rel.create({'product_tmpl_id': nuevo, 'parameter_id': param.id,
                                'sequence': rel_v.sequence})
            print('   %-9s relacion creada (%s)' % (param.code, rel_n.id))
        else:
            if not rel_n.active:
                rel_n.write({'active': True})
            print('   %-9s relacion ya existia (%s)' % (param.code, rel_n.id))

        buenas = CfgX.search([('product_parameter_rel_id', '=', rel_v.id),
                              ('active', '=', True)])
        ids_buenos = set(buenas.mapped('specification_id').ids)
        for cfg_v in buenas:
            spec = cfg_v.specification_id
            cfg_n = CfgX.search([('product_parameter_rel_id', '=', rel_n.id),
                                 ('specification_id', '=', spec.id)], limit=1)
            vals = valores(cfg_v)
            vals['active'] = True
            if cfg_n:
                cfg_n.write(vals)
                print('      = %-30s actualizada (cfg %s)' % (spec.name[:30], cfg_n.id))
            else:
                vals.update({'product_parameter_rel_id': rel_n.id,
                             'specification_id': spec.id})
                cfg_n = Cfg.create(vals)
                print('      + %-30s creada (cfg %s)' % (spec.name[:30], cfg_n.id))

        # lo que el autogenerado trajo de mas y la archivada no tiene: se desactiva
        for cfg_n in CfgX.search([('product_parameter_rel_id', '=', rel_n.id),
                                  ('active', '=', True)]):
            if cfg_n.specification_id.id not in ids_buenos:
                cfg_n.write({'active': False})
                print('      - %-30s desactivada, no aplica a esta hoja' % (
                    cfg_n.specification_id.name or '?')[:30])

print('\n=== como queda la ficha viva ===')
for _v, nuevo, clave in PARES:
    tot = 0
    print('   %s (tmpl %s)' % (clave, nuevo))
    for rel_n in RelX.search([('product_tmpl_id', '=', nuevo), ('active', '=', True)],
                             order='sequence, id'):
        act = CfgX.search([('product_parameter_rel_id', '=', rel_n.id), ('active', '=', True)])
        tot += len(act)
        print('      %-9s %d activas: %s' % (
            rel_n.parameter_id.code, len(act),
            ' | '.join((c.specification_id.name or '?')[:24] for c in act)))
    print('      TOTAL %d especificaciones activas' % tot)
env.cr.commit()
