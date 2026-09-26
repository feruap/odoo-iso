"""
LIMPIEZA DE WIZARDS COLGADOS — ANEXO DE ANÁLISIS (producción)
==============================================================
Problema: el analista abrió el asistente de captura del Anexo, cerró la
pestaña sin guardar ni cancelar, y el registro temporal quedó en la base
de datos. Al intentar volver a abrir el anexo, Odoo detecta ese registro
huérfano y lanza el error de restricción de integridad.

Solución: eliminar todos los registros de wizard de anexo que lleven más
de 1 hora sin actividad (parámetro UMBRAL_HORAS). TransientModel: son
datos puramente temporales; no hay pérdida de información regulatoria.

Solicitado por: Diana Flores — Control de Calidad, 2026-09-24
"""

from datetime import datetime, timedelta

UMBRAL_HORAS = 1  # elimina wizards creados hace más de N horas

WizardLine = env['amunet.quality.anexo.wizard.line']
Wizard     = env['amunet.quality.anexo.wizard']

corte = datetime.utcnow() - timedelta(hours=UMBRAL_HORAS)

# Buscar wizards viejos
viejos = Wizard.search([('create_date', '<', corte)])
print(f"Wizards de anexo con más de {UMBRAL_HORAS}h: {len(viejos)}")

if not viejos:
    print("Nada que limpiar.")
else:
    for w in viejos:
        lineas = WizardLine.search([('wizard_id', '=', w.id)])
        print(f"  Wizard id={w.id}  check_id={w.check_id.id} ({w.check_id.name})  "
              f"creado={w.create_date}  líneas={len(lineas)}")
        lineas.unlink()   # primero las líneas
        w.unlink()        # luego el wizard

    env.cr.commit()
    print(f"\n✓ Se eliminaron {len(viejos)} wizard(s) huérfano(s). El analista puede")
    print("  volver a abrir el anexo del análisis sin error.")
