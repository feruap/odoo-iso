"""
setup_amunet_production_data.py
Configura amunet_expiration_text y amunet_initial_ph en los 26 productos de solucion.
Idempotente: solo escribe campos que esten vacios o en 0.
"""

Product = env['product.template']

# Fuente: exportado de amunet_local (todos los productos categoria solucion)
CONFIG_MAP = {
    'SPAPB01': ('2.6 años', 7.4),   # Solución de Corrimiento AC + PBS
    'SPBAB01': ('2.6 años', 7.4),   # Solución de corrimeinto Ac
    'SPBAB02': ('2.6 años', 7.4),   # Solución de corrimeinto Ac CHEM
    'SPHBB01': ('2.6 años', 8.0),   # Solución de Corrimiento de Hemoglobina Cualitativa
    'SPLPT01': ('3 Meses',  7.4),   # Solución de Lavado (PBS/Tween)
    'SPNPS01': ('3 Meses',  9.0),   # Solución de Nanoparticulas
    'SPPBS01': ('6 Meses',  7.4),   # PBS 1X
    'SPPBS02': ('6 Meses',  7.4),   # PBS 10X
    'SPSAC01': ('6 meses',  0.0),   # Solución HCl 6 M
    'SPSAG01': ('2.6 años', 9.0),   # Solución de corrimiento Tracto Respiratorio
    'SPSDC01': ('3 Meses',  0.0),   # Solución diluyente para conjugado (AD 0)
    'SPSDC02': ('3 Meses',  0.0),   # Solución diluyente para conjugado (AD1)
    'SPSDM01': ('3 Meses',  0.0),   # Solución Diluyente β Trehalosa
    'SPSHS01': ('6 meses',  0.0),   # Solución Hidroxido de Sodio 1 M
    'SPSHS02': ('6 meses',  0.0),   # Hidróxido de sodio 20%
    'SPSPA01': ('3 Meses',  0.0),   # Pretratamiento almohadilla conjugado
    'SPSPA02': ('3 Meses',  0.0),   # Pretratamiento almohadilla muestra
    'SPSPA03': ('3 Meses',  0.0),   # Pretratamiento almohadilla muestra V2
    'SPSPB01': ('1 Meses',  7.5),   # Solución de bloqueo de BSA 7.5
    'SPSPB02': ('1 Meses',  8.5),   # Solución de bloqueo de BSA 8.5
    'SPSPB03': ('1 Meses',  0.0),   # Solución de Bloqueo Caseina
    'SPSPC03': ('3 Meses',  0.0),   # Solución Amortiguadora de Borato 0.1 M
    'SPSPC04': ('3 Meses',  7.5),   # Solución Amortiguadora de Borato 20 mM pH 7.5
    'SPSPC05': ('3 Meses',  8.5),   # Solución Amortiguadora de Borato 20 mM pH 8.5
    'SPSRB01': ('2 Meses',  0.0),   # Reactivo de Bradford
    # SPSAS01 queda sin expiration_text (vacio en local) - no se toca
}

updated = 0
skipped = 0

for code, (exp_text, ph) in CONFIG_MAP.items():
    prod = Product.search([('default_code', '=', code)], limit=1)
    if not prod:
        print(f"[SKIP] {code}: producto no encontrado")
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
        print(f"[OK] {code} | {prod.name[:50]} | {changed}")
        updated += 1
    else:
        print(f"[SKIP] {code} | ya configurado")
        skipped += 1

print(f"\nResumen: {updated} actualizados, {skipped} sin cambios/no encontrados.")
