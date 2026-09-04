"""
Fix final análisis 776 — hielera chica:
1. Corregir min/max de los detalles MAVI-11 (Ancho, Alto, Grosor)
2. Eliminar línea VAMA-023 y su detalle del análisis
"""
Line   = env['amunet.quality.test.line']
Detail = env['amunet.quality.test.line.detail']

# ── 1. Corregir rangos numéricos ─────────────────────────────────────────────
# Ancho: 15-18 cm ± 0.5 → min=14.5, max=18.5
Detail.browse(6545).write({'min_value': 14.5, 'max_value': 18.5})
print("[6545] Ancho: min=14.5  max=18.5")

# Alto: 15-18 cm ± 0.5 → min=14.5, max=18.5
Detail.browse(6546).write({'min_value': 14.5, 'max_value': 18.5})
print("[6546] Alto:  min=14.5  max=18.5")

# Grosor: 2 cm ± 1 → min=1.0, max=3.0
Detail.browse(6548).write({'min_value': 1.0, 'max_value': 3.0})
print("[6548] Grosor: min=1.0   max=3.0")

# ── 2. Eliminar línea VAMA-023 y su detalle ──────────────────────────────────
print("\n── Eliminando línea VAMA-023 ──")
try:
    det_vama = Detail.browse(6544)
    det_vama.unlink()
    print("  Detalle [6544] eliminado")
except Exception as e:
    print(f"  No se pudo eliminar detalle [6544]: {e}")

try:
    linea_vama = Line.browse(2289)
    linea_vama.unlink()
    print("  Línea [2289] VAMA-023 eliminada")
except Exception as e:
    print(f"  No se pudo eliminar línea [2289]: {e}")

env.cr.commit()

# ── Verificación ──────────────────────────────────────────────────────────────
print("\n── Estado final ──")
QCheck = env['amunet.quality.check']
c = QCheck.browse(776)
for line in c.test_line_ids:
    print(f"Línea [{line.id}] {line.parameter_id.code} | verdict={line.verdict}")
    for det in line.detail_line_ids:
        print(f"  [{det.id}] '{det.name}' | min={det.min_value} max={det.max_value} | criterio: '{det.acceptance_criteria}'")
print("\n✓ Listo.")
