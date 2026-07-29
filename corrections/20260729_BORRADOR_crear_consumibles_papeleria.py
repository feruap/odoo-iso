"""
BORRADOR — Consumibles / Papelería
Pendiente: definir claves COPAP con Karla antes de ejecutar.
Lista capturada: 2026-07-29

NOTA: el lápiz de grafito no tiene cantidad indicada — confirmar antes de cargar.
"""

# Categoría a crear si no existe: Consumible / Papelería
# Prefijo de clave propuesto: COPAP + número secuencial

productos = [
    # (clave,       nombre,                              qty)
    ('COPAP??', 'Lapicero rojo',                          6),
    ('COPAP??', 'Lapicero azul fino',                     5),
    ('COPAP??', 'Lapicero azul mediano',                 14),
    ('COPAP??', 'Lapicero azul punto de aguja',           5),
    ('COPAP??', 'Lapicero azul ultrafino',               16),
    ('COPAP??', 'Portaminas 0.5 mm',                      5),
    ('COPAP??', 'Lápiz de grafito',                    None),  # ⚠️ sin cantidad — confirmar
    ('COPAP??', 'Block de notas',                         3),
    ('COPAP??', 'Clip N°1',                               7),
    ('COPAP??', 'Clip N°2',                               2),
    ('COPAP??', 'USB 32 GB',                              2),
    ('COPAP??', 'Marcatextos verde',                      5),
    ('COPAP??', 'Marcatextos naranja',                    6),
    ('COPAP??', 'Marcatextos azul',                       3),
    ('COPAP??', 'Marcatextos rosa',                       4),
    ('COPAP??', 'Marcatextos amarillo',                   2),
    ('COPAP??', 'Marcatextos morado',                     2),
    ('COPAP??', 'Cinta adhesiva 12 mm x 33 m',           7),
    ('COPAP??', 'Plumones para pizarrón',                 5),
    ('COPAP??', 'Grapa Standard',                         3),
    ('COPAP??', 'Goma de migajón',                        2),
    ('COPAP??', 'Agarrapapel 19 mm',                      8),
    ('COPAP??', 'Agarrapapel 32 mm',                      8),
    ('COPAP??', 'Agarrapapel 41 mm',                     15),
    ('COPAP??', 'Puntillas 0.7 mm',                       1),
    ('COPAP??', 'Cinta color rojo',                       3),
    ('COPAP??', 'Cinta color azul',                       3),
    ('COPAP??', 'Cinta color verde',                      3),
    ('COPAP??', 'Cinta color gris',                       1),
    ('COPAP??', 'Cinta color amarillo',                   1),
    ('COPAP??', 'Cinta color rosa',                       1),
    ('COPAP??', 'Dedal de hule',                         10),
]

# Total: 32 productos (31 con cantidad definida + 1 pendiente)
print("BORRADOR — pendiente definir claves antes de ejecutar")
for clave, nombre, qty in productos:
    qty_str = str(qty) if qty is not None else '⚠️ PENDIENTE'
    print(f"  {clave}  {nombre:<40s}  qty={qty_str}")
