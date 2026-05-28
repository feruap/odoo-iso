# Idempotente: instala amunet_packaging_planning y amunet_price_visibility
env['ir.module.module'].update_list()
targets = ['amunet_packaging_planning', 'amunet_price_visibility']
mods = env['ir.module.module'].search([('name','in',targets)])
for m in mods:
    print(f"  {m.name}: estado actual = {m.state}")
to_install = mods.filtered(lambda m: m.state == 'uninstalled')
if to_install:
    print(f"  Instalando: {to_install.mapped('name')}")
    try:
        to_install.button_immediate_install()
        env.cr.commit()
        print("  OK button_immediate_install completado")
    except Exception as e:
        print(f"  AVISO immediate_install fallo: {e}")
        to_install.button_install()
        env.cr.commit()
        print("  Marcadas to_install. Ejecutar manualmente: odoo -u <module> tras este script.")
else:
    print("  Ningun modulo nuevo por instalar")
