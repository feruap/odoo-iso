"""
Actualizar criterios de los detalles de MAVI-11 en análisis 776.
(El script anterior falló antes del commit, así que los valores viejos persisten.)
"""
Detail = env['amunet.quality.test.line.detail']

Detail.browse(6545).write({'acceptance_criteria': '15-18 cm ± 0.5 cm'})
print(f"[6545] Ancho → '15-18 cm ± 0.5 cm'")

Detail.browse(6546).write({'acceptance_criteria': '15-18 cm ± 0.5 cm'})
print(f"[6546] Alto → '15-18 cm ± 0.5 cm'")

Detail.browse(6548).write({'acceptance_criteria': '2 cm ± 1 cm'})
print(f"[6548] Grosor → '2 cm ± 1 cm'")

env.cr.commit()
print("✓ Criterios actualizados.")
