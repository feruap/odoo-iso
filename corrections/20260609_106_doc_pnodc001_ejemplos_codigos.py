from markupsafe import Markup

# ── Actividad 1: código de documento ──────────────────────────────────────────
act1 = Markup('''
<p>Asignar código al documento del Sistema de Gestión de Calidad con la siguiente estructura:</p>

<table border="0" style="border-collapse:collapse;margin:12px 0;">
  <tr>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 18px;text-align:center;font-size:1.3em;font-weight:bold;letter-spacing:2px;">
      TIPO
    </td>
    <td style="padding:0 6px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 18px;text-align:center;font-size:1.3em;font-weight:bold;letter-spacing:2px;">
      ÁREA
    </td>
    <td style="padding:0 6px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 18px;text-align:center;font-size:1.3em;font-weight:bold;letter-spacing:2px;">
      000
    </td>
  </tr>
  <tr>
    <td style="text-align:center;font-size:0.85em;color:#555;padding-top:4px;">(1) Tipo de documento</td>
    <td></td>
    <td style="text-align:center;font-size:0.85em;color:#555;padding-top:4px;">(2) Área</td>
    <td></td>
    <td style="text-align:center;font-size:0.85em;color:#555;padding-top:4px;">(3) Consecutivo</td>
  </tr>
</table>

<p><strong>Ejemplo:</strong></p>
<table border="0" style="border-collapse:collapse;margin:8px 0;">
  <tr>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 18px;text-align:center;font-size:1.3em;font-weight:bold;letter-spacing:2px;">PNO</td>
    <td style="padding:0 6px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 18px;text-align:center;font-size:1.3em;font-weight:bold;letter-spacing:2px;">GE</td>
    <td style="padding:0 6px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 18px;text-align:center;font-size:1.3em;font-weight:bold;letter-spacing:2px;">001</td>
  </tr>
  <tr>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Procedimiento<br/>Normalizado de<br/>Operación</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Gestión</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Primero del área</td>
  </tr>
</table>

<p><strong>Donde:</strong></p>
<ul>
  <li><strong>(1) Tipo de documento</strong> — ver tabla de tipos</li>
  <li><strong>(2) Área</strong> — ver tabla de áreas</li>
  <li><strong>(3) Consecutivo</strong> — número consecutivo, inicia en 001 por área, incrementando de forma progresiva</li>
</ul>

<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;margin:10px 0;">
  <tr><th colspan="2" style="padding:6px;background:#e3f2fd;text-align:left;">(1) Tipos de documento</th></tr>
  <tr><th style="padding:5px;background:#f5f5f5;">Documento</th><th style="padding:5px;background:#f5f5f5;">Clave</th></tr>
  <tr><td style="padding:5px;">Manual</td><td style="padding:5px;text-align:center;"><strong>MAN</strong></td></tr>
  <tr><td style="padding:5px;">Procedimiento Normalizado de Operación</td><td style="padding:5px;text-align:center;"><strong>PNO</strong></td></tr>
  <tr><td style="padding:5px;">Procedimiento</td><td style="padding:5px;text-align:center;"><strong>PRO</strong></td></tr>
  <tr><td style="padding:5px;">Instructivo</td><td style="padding:5px;text-align:center;"><strong>INT</strong></td></tr>
  <tr><td style="padding:5px;">Política</td><td style="padding:5px;text-align:center;"><strong>P</strong></td></tr>
  <tr><td style="padding:5px;">Organigrama</td><td style="padding:5px;text-align:center;"><strong>ORG</strong></td></tr>
  <tr><td style="padding:5px;">Lista Maestra</td><td style="padding:5px;text-align:center;"><strong>LMA</strong></td></tr>
</table>

<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;margin:10px 0;">
  <tr><th colspan="2" style="padding:6px;background:#e3f2fd;text-align:left;">(2) Áreas</th></tr>
  <tr><th style="padding:5px;background:#f5f5f5;">Área</th><th style="padding:5px;background:#f5f5f5;">Clave</th></tr>
  <tr><td style="padding:5px;">Dirección</td><td style="padding:5px;text-align:center;"><strong>DG</strong></td></tr>
  <tr><td style="padding:5px;">Administración</td><td style="padding:5px;text-align:center;"><strong>AD</strong></td></tr>
  <tr><td style="padding:5px;">Recursos Humanos</td><td style="padding:5px;text-align:center;"><strong>RH</strong></td></tr>
  <tr><td style="padding:5px;">Documentación</td><td style="padding:5px;text-align:center;"><strong>DC</strong></td></tr>
  <tr><td style="padding:5px;">Almacén</td><td style="padding:5px;text-align:center;"><strong>AL</strong></td></tr>
  <tr><td style="padding:5px;">Producción</td><td style="padding:5px;text-align:center;"><strong>PR</strong></td></tr>
  <tr><td style="padding:5px;">Asuntos Regulatorios</td><td style="padding:5px;text-align:center;"><strong>AR</strong></td></tr>
  <tr><td style="padding:5px;">Control de Calidad</td><td style="padding:5px;text-align:center;"><strong>CC</strong></td></tr>
  <tr><td style="padding:5px;">Gestión</td><td style="padding:5px;text-align:center;"><strong>GE</strong></td></tr>
  <tr><td style="padding:5px;">Mantenimiento</td><td style="padding:5px;text-align:center;"><strong>MA</strong></td></tr>
  <tr><td style="padding:5px;">Tecnovigilancia</td><td style="padding:5px;text-align:center;"><strong>TV</strong></td></tr>
  <tr><td style="padding:5px;">Estabilidad</td><td style="padding:5px;text-align:center;"><strong>EST</strong></td></tr>
</table>

<p style="background:#fff8e1;border-left:3px solid #f9a825;padding:8px 12px;margin:8px 0;">
<strong>NOTA:</strong> Los documentos de origen externo (pre-impresos, legislativos o de otras empresas)
NO son codificables; su control no corresponde al área de Calidad.
Cuando un documento externo es actualizado o pierde vigencia, debe sustituirse por la edición vigente.
</p>
''')

# ── Actividad 2: código de formato derivado ───────────────────────────────────
act2 = Markup('''
<p>Asignar código al formato derivado del documento del Sistema de Gestión de la Calidad, cuando aplique, con la siguiente estructura:</p>

<table border="0" style="border-collapse:collapse;margin:12px 0;">
  <tr>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">F</td>
    <td style="padding:0 5px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">ÁREA</td>
    <td style="padding:0 5px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">000</td>
    <td style="padding:0 5px;font-size:1.4em;color:#555;">/</td>
    <td style="border:2px solid #1565c0;background:#e3f2fd;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">000</td>
  </tr>
  <tr>
    <td style="text-align:center;font-size:0.82em;color:#555;padding-top:4px;">(1) Formato</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#555;padding-top:4px;">(2) Área</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#555;padding-top:4px;">(3) N° documento<br/>del que deriva</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#555;padding-top:4px;">(4) N° consecutivo<br/>del formato</td>
  </tr>
</table>

<p><strong>Ejemplo:</strong></p>
<table border="0" style="border-collapse:collapse;margin:8px 0;">
  <tr>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">F</td>
    <td style="padding:0 5px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">GE</td>
    <td style="padding:0 5px;font-size:1.4em;color:#555;">&#8209;</td>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">001</td>
    <td style="padding:0 5px;font-size:1.4em;color:#555;">/</td>
    <td style="border:2px solid #2e7d32;background:#e8f5e9;padding:10px 14px;text-align:center;font-size:1.3em;font-weight:bold;">001</td>
  </tr>
  <tr>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Formato</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Gestión</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Deriva del<br/>PNOGE-001</td>
    <td></td>
    <td style="text-align:center;font-size:0.82em;color:#2e7d32;padding-top:4px;">Primer formato<br/>de ese PNO</td>
  </tr>
</table>

<p><strong>Donde:</strong></p>
<ul>
  <li><strong>(1) F</strong> — siempre "F" para identificar que es un Formato</li>
  <li><strong>(2) Área</strong> — clave del área, igual que en los documentos (ver tabla de áreas en Actividad 1)</li>
  <li><strong>(3) Número del documento</strong> — número consecutivo del documento del cual es derivado el formato</li>
  <li><strong>(4) Número del formato</strong> — número consecutivo del formato, inicia en 001, incrementando de forma progresiva</li>
</ul>
''')

ActModel = env['amunet.documento.actividad']
doc_obj = env['amunet.documento'].search([('codigo', '=', 'PNODC-001')], limit=1)
acts = {a.sequence: a for a in ActModel.search([('documento_id', '=', doc_obj.id)])}

acts[1].write({'descripcion': act1})
acts[2].write({'descripcion': act2})
env.cr.commit()
print('OK — actividades 1 y 2 de PNODC-001 con ejemplos visuales de codificación')
