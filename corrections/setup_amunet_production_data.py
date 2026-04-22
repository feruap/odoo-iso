"""
setup_amunet_production_data.py
Configura los campos amunet_expiration_text y amunet_initial_ph en productos de solucion
que ya tienen qc=True y BoM pero les falta la configuracion de caducidad/pH.
Solo actualiza campos vacios (idempotente).
Aplica UNICAMENTE valores inferibles de forma segura (nombre del producto o familia conocida).
"""
import re

Product = env['product.template']

# Mapa de configuracion por default_code: (expiration_text, initial_ph)
# Valores derivados de: nombres de productos, familia (ej. SPSPC05 tiene '3 Meses'/8.5)
CONFIG_MAP = {
    'SPSPC03': ('3 Meses', 0.0),    # Borato 0.1 M - familia Borato, pH no especificado en nombre
    'SPSPC04': ('3 Meses', 7.5),    # Borato 20 mM pH 7.5 - pH explicito en nombre, familia Borato
    'SPSPB01': ('1 Meses', 7.5),    # Bloqueo BSA 7.5 - pH en nombre, mismo tiempo que SPSPB02
    'SPLPT01': ('3 Meses', 7.4),    # Solucion Lavado PBS/Tween - base PBS, pH 7.4 estandar
    'SPSPA01': ('3 Meses', 0.0),    # Pretratamiento conjugado
    'SPSPA02': ('3 Meses', 0.0),    # Pretratamiento muestra
    'SPSPA03': ('3 Meses', 0.0),    # Pretratamiento muestra
    'SPSDC01': ('3 Meses', 0.0),    # Diluyente conjugado AD0
    'SPSDC02': ('3 Meses', 0.0),    # Diluyente conjugado AD1
    'SPSDM01': ('3 Meses', 0.0),    # Diluyente Trehalosa
    'SPSPB03': ('1 Meses', 0.0),    # Bloqueo Caseina
}

updated = 0
skipped = 0

for code, (exp_text, ph) in CONFIG_MAP.items():
    prod = Product.search([('default_code', '=', code)], limit=1)
    if not prod:
        print(f"[SKIP] {code}: no encontrado")
        skipped += 1
        continue

    changed = {}
    if not prod.amunet_expiration_text and exp_text:
        changed['amunet_expiration_text'] = exp_text
    if prod.amunet_initial_ph == 0.0 and ph > 0:
        changed['amunet_initial_ph'] = ph

    if changed:
        prod.write(changed)
        env.cr.commit()
        print(f"[OK] {code} | {prod.name[:50]} | actualizado: {changed}")
        updated += 1
    else:
        print(f"[OK] {code} | ya configurado, sin cambios")
        skipped += 1

print(f"\nResumen: {updated} actualizados, {skipped} sin cambios/no encontrados.")
