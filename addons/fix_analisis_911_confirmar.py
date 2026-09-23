Check = env['amunet.quality.check']
check = Check.browse(911)
print(f"Antes: state={check.state}, sampling_confirmed={check.sampling_confirmed}")

check.sudo().write({
    'sampling_confirmed': True,
    'state': 'in_progress',
    'qty_sampling': 5.0,
})
env.cr.commit()
print(f"Después: state={check.state}, sampling_confirmed={check.sampling_confirmed}")
print("✓ Análisis 911 listo para puntos de control y reporte.")
