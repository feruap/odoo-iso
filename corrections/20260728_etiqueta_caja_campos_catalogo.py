# Carga los campos de etiqueta de caja (subtipo, contenedor, accesorio, registro
# sanitario, nombre en etiqueta) en los productos, migrados desde el catalogo de
# etiquetas validado en staging. Idempotente: escribe por default_code.
# NO toca precios. Sifilinet (DIAM-002) queda como subtipo P con su RS.
DATA = [['DIAM-002', 'P', '', '', '1596R2024 SSA', 'SIFILINET'], ['DIAM-023', 'S', '', '', '', 'COVID19 IgG/IgM'], ['DLVPH01', 'M', '', '', '2328R2024 SSA', 'VPH-NET'], ['DMADB01', 'H', '(auto-contenida)', '', '1400R2024 SSA', 'ANTIDOPING SALIVA 5P\n(THC, AMP, COC, OPI, MET)'], ['DMCHA01', 'S', '', '', '', 'COMBO ENTAMOEBA'], ['DMCRD01', 'H', 'tubos de extracción c/buffer', 'hisopos', '1820R2025 SSA', 'COMBO RESPIRATORIO\n(Influenza A+B, SARS-CoV-2, RSV)'], ['DMDMD01', 'S', '', '', '', 'DÍMERO-D'], ['DMFFN01', 'H', 'tubos colectores c/buffer', 'hisopos', '', 'FIBRONECTINA FETAL'], ['DMFRT02', 'P', '', '', '0183R2024 SSA', 'FERRINET\n(Ferritina)'], ['DMGON01', 'H', 'tubos colectores', '', '2328R2024 SSA', 'GONORREA NET'], ['DMHBA01', 'S', '', '', '', 'HbA1c / HEMOGLOBINA\n(Cualitativa)'], ['DMHCG01', 'P', '', '', '0131R2024 SSA', 'HCG-NET'], ['DMHPY01', 'S', '', '', '', 'H. PYLORI NET'], ['DMIGE01', 'S', '', '', '0131R2024 SSA', 'IgE NET'], ['DMIVU01', 'H', 'contenedores de muestra', '', '', 'INFECCIÓN VÍAS URINARIAS\n(orina)'], ['DMMCT01', 'S', '', '', '1151R2024 SSA', 'CARDIAC COMBO'], ['DMPHV01', 'H', '', 'hisopos', '1151R2024 SSA', 'pH VAGINAL'], ['DMPRO01', 'S', '', '', '', 'NT-proBNP NET'], ['DMPSA02', 'P', '', '', '2364R2024 SSA', 'PROSTATINET\n(PSA)'], ['DMRAV01', 'H', 'tubos c/solución de corrimiento', 'goteros', '2789R2024 SSA', 'ROTADENET\n(Rotavirus)'], ['DMTET01', 'S', '', '', '', 'TÉTANOS NET'], ['DMTIF01', 'S', '', '', '', 'TIFOIDEA IgG/IgM'], ['DMTRF01', 'H', 'tubos colectores c/buffer', '', '', 'FOB / TRANSFERRINA FECAL'], ['DMVID01', 'P', '', '', '0252R2024 SSA', 'VITAMINET D'], ['DMVIH02', 'S', '', '', '', 'VIH 4ta GENERACIÓN\n(VIH 1.2 y p24)']]
tmpl_obj = env['product.template'].sudo()
ok=0; faltan=[]
for code, sub, cont, acc, reg, nom in DATA:
    t = tmpl_obj.search([('default_code','=',code)], limit=1)
    if not t:
        faltan.append(code); continue
    vals={'etiqueta_subtipo':sub or False,
          'etiqueta_contenedor':cont or False,
          'etiqueta_accesorio':acc or False,
          'registro_sanitario':reg or False}
    if nom: vals['nombre_etiqueta']=nom
    t.write(vals)
    ok+=1
env.cr.commit()
print('Productos actualizados:', ok)
print('No encontrados en prod:', faltan)
