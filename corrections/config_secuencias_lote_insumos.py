# Configura la secuencia de lote Amunet (prefijo = clave sin las 2 primeras
# letras + %(month)s%(y)s, padding 2) en los insumos/equipos que reciben lote y
# hoy tienen la secuencia GENERICA ("Serial Numbers") o NULA -> por eso sus lotes
# salian "0000001". Grupos: equipos EQ*, reactivos MPREC*/MPRCC*, consumibles CO*,
# hisopos STHIS*. NO toca DM* (terminados usan folio de MO) ni productos que ya
# tienen su prefijo. Solo afecta lotes FUTUROS. Solicitado por Fernando 2026-07-22.
GROUPS = ('EQ', 'MPREC', 'MPRCC', 'CO', 'STHIS')
Tmpl = env['product.template'].sudo()

prods = Tmpl.search([('tracking', '=', 'lot')])
def needs_fix(t):
    if not (t.default_code and t.default_code.startswith(GROUPS)):
        return False
    seq = t.lot_sequence_id
    # sin secuencia, o secuencia sin prefijo (generica), o "Serial Numbers"
    if not seq:
        return True
    pref = (seq.prefix or '').strip()
    if not pref:
        return True
    if 'serial' in (seq.name or '').lower():
        return True
    return False

target = prods.filtered(needs_fix)
print('Productos a configurar:', len(target))
por_grupo = {}
for t in target:
    base = t.default_code[2:]  # clave sin las 2 primeras letras
    t.amunet_lot_prefix = base  # dispara el inverse -> crea/asigna la secuencia
    g = t.default_code[:2] if not t.default_code.startswith('MPR') else t.default_code[:5]
    por_grupo[g] = por_grupo.get(g, 0) + 1

env.cr.commit()
print('Por grupo:', por_grupo)

# Prueba: nombre de lote que saldria ahora para unos ejemplos
for code in ['EQEPV01', 'MPREC27', 'MPRCC01', 'COTUB08', 'STHIS07']:
    p = env['product.product'].search([('default_code', '=', code)], limit=1)
    if p:
        try:
            names = p._amunet_next_lot_names(1)
            print('  %s -> proximo lote: %s' % (code, names))
        except Exception as e:
            print('  %s -> ERROR: %s' % (code, e))
print('LISTO')
