# Leer datos de EQBAD01 desde producción y mostrarlos para replicar en staging
import subprocess, json

# Buscar en staging primero (por si ya existe)
existe = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'EQBAD01')
], limit=1)
if existe:
    print(f"Ya existe en staging: id={existe.id} | {existe.name}")
else:
    print("No existe en staging aún.")
