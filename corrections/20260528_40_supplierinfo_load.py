# Idempotente: carga supplierinfo Tonghzhou (SPHM) y Cangzhou (MPCAR)
from datetime import datetime, date

tonghzhou = env["res.partner"].search([("name","ilike","Tongzhou")], limit=1)
cangzhou = env["res.partner"].search([("name","ilike","Cangzhou ShengFeng")], limit=1)
usd = env.ref("base.USD")
pieza = env["uom.uom"].search([("name","=","Pieza de hoja maestra")], limit=1)

SPHM_DATA = [
 {
  "sphm_codigo": "SPHMC73",
  "catalog_no": "C006-4025",
  "ref_tonghzhou": "CFC-425",
  "analito": "H-FABP + cTnI Combo",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 78.0,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC74",
  "catalog_no": "C006-4025",
  "ref_tonghzhou": "CFC-425",
  "analito": "H-FABP + cTnI Combo",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 78.0,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC17",
  "catalog_no": "C007-4035",
  "ref_tonghzhou": "",
  "analito": "Myoglobin/CK-MB/Troponin I Combo",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 79.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC11",
  "catalog_no": "D002-1021",
  "ref_tonghzhou": "DAM-121",
  "analito": "Amphetamine AMP1000 (dipstick)",
  "muestra": "Urine",
  "formato": "dipstick (tubo)",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-12-17",
  "notas": "Tira en tubo sin cassette"
 },
 {
  "sphm_codigo": "SPHMC12",
  "catalog_no": "D006-1021",
  "ref_tonghzhou": "DCO-121",
  "analito": "Cocaine COC300 (dipstick)",
  "muestra": "Urine",
  "formato": "dipstick (tubo)",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC63",
  "catalog_no": "D010-1021",
  "ref_tonghzhou": "DFY-121",
  "analito": "Fentanyl FYL10 (dipstick)",
  "muestra": "Urine",
  "formato": "dipstick (tubo)",
  "tests_por_hoja": 75,
  "precio_usd": 11.0,
  "fecha_pfi": "2025-06-06",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC13",
  "catalog_no": "D013-1021",
  "ref_tonghzhou": "DME-121",
  "analito": "Methamphetamine MET1000 (dipstick)",
  "muestra": "Urine",
  "formato": "dipstick (tubo)",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC14",
  "catalog_no": "D017-1021",
  "ref_tonghzhou": "DOP-121",
  "analito": "Opiates OPI2000 (dipstick)",
  "muestra": "Urine",
  "formato": "dipstick (tubo)",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC10",
  "catalog_no": "D022-1021",
  "ref_tonghzhou": "DTH-121",
  "analito": "Marijuana THC50 (dipstick)",
  "muestra": "Urine",
  "formato": "dipstick (tubo)",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC11",
  "catalog_no": "D002-1022",
  "ref_tonghzhou": "",
  "analito": "Amphetamine AMP1000 cassette",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-09-19",
  "notas": "Misma hoja que dipstick, distinto formato"
 },
 {
  "sphm_codigo": "SPHMC12",
  "catalog_no": "D006-1022",
  "ref_tonghzhou": "",
  "analito": "Cocaine COC300 cassette",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 11.0,
  "fecha_pfi": "2025-09-19",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC13",
  "catalog_no": "D013-1022",
  "ref_tonghzhou": "",
  "analito": "Methamphetamine MET1000 cassette",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-09-19",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC14",
  "catalog_no": "D017-1022",
  "ref_tonghzhou": "",
  "analito": "Opiates OPI2000 cassette",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 9.5,
  "fecha_pfi": "2025-09-19",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC10",
  "catalog_no": "D022-1022",
  "ref_tonghzhou": "",
  "analito": "Marijuana THC50 cassette",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 11.0,
  "fecha_pfi": "2025-09-19",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC10",
  "catalog_no": "D000-1055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel orina (OPI/COC/AMP/MET/THC), 10T/hoja",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 10,
  "precio_usd": 48.0,
  "fecha_pfi": "2025-09-15",
  "notas": "INFORMATIVO: Tonghzhou tambien ofrece este panel consolidado, pero Amunet arma el producto desde las 5 hojas individuales (no compra esta hoja consolidada)."
 },
 {
  "sphm_codigo": "SPHMC11",
  "catalog_no": "D000-1055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel orina (OPI/COC/AMP/MET/THC), 10T/hoja",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 10,
  "precio_usd": 48.0,
  "fecha_pfi": "2025-09-15",
  "notas": "INFORMATIVO: Tonghzhou tambien ofrece este panel consolidado, pero Amunet arma el producto desde las 5 hojas individuales (no compra esta hoja consolidada)."
 },
 {
  "sphm_codigo": "SPHMC12",
  "catalog_no": "D000-1055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel orina (OPI/COC/AMP/MET/THC), 10T/hoja",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 10,
  "precio_usd": 48.0,
  "fecha_pfi": "2025-09-15",
  "notas": "INFORMATIVO: Tonghzhou tambien ofrece este panel consolidado, pero Amunet arma el producto desde las 5 hojas individuales (no compra esta hoja consolidada)."
 },
 {
  "sphm_codigo": "SPHMC13",
  "catalog_no": "D000-1055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel orina (OPI/COC/AMP/MET/THC), 10T/hoja",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 10,
  "precio_usd": 48.0,
  "fecha_pfi": "2025-09-15",
  "notas": "INFORMATIVO: Tonghzhou tambien ofrece este panel consolidado, pero Amunet arma el producto desde las 5 hojas individuales (no compra esta hoja consolidada)."
 },
 {
  "sphm_codigo": "SPHMC14",
  "catalog_no": "D000-1055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel orina (OPI/COC/AMP/MET/THC), 10T/hoja",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 10,
  "precio_usd": 48.0,
  "fecha_pfi": "2025-09-15",
  "notas": "INFORMATIVO: Tonghzhou tambien ofrece este panel consolidado, pero Amunet arma el producto desde las 5 hojas individuales (no compra esta hoja consolidada)."
 },
 {
  "sphm_codigo": "SPHMC75",
  "catalog_no": "D000-4055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel sangre (OPI/MET/THC/COC/AMP)",
  "muestra": "Whole Blood",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 75.0,
  "fecha_pfi": "2025-08-15",
  "notas": "Panel sangre = combo 2P+3P sangre"
 },
 {
  "sphm_codigo": "SPHMC76",
  "catalog_no": "D000-4055",
  "ref_tonghzhou": "",
  "analito": "Multi-drug 5 panel sangre (OPI/MET/THC/COC/AMP)",
  "muestra": "Whole Blood",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 75.0,
  "fecha_pfi": "2025-08-15",
  "notas": "Panel sangre = combo 2P+3P sangre"
 },
 {
  "sphm_codigo": "SPHMC53",
  "catalog_no": "D000-8053-A",
  "ref_tonghzhou": "",
  "analito": "Multi-Drug 5 panel saliva, 35T/hoja",
  "muestra": "Oral Fluid",
  "formato": "cassette+colector",
  "tests_por_hoja": 35,
  "precio_usd": 50.0,
  "fecha_pfi": "2026-03-23",
  "notas": "Panel saliva = combo 2P+3P saliva"
 },
 {
  "sphm_codigo": "SPHMC54",
  "catalog_no": "D000-8053-A",
  "ref_tonghzhou": "",
  "analito": "Multi-Drug 5 panel saliva, 35T/hoja",
  "muestra": "Oral Fluid",
  "formato": "cassette+colector",
  "tests_por_hoja": 35,
  "precio_usd": 50.0,
  "fecha_pfi": "2026-03-23",
  "notas": "Panel saliva = combo 2P+3P saliva"
 },
 {
  "sphm_codigo": "SPHMC65",
  "catalog_no": "F001-4022",
  "ref_tonghzhou": "FHC-422",
  "analito": "Pregnancy hCG (WB/S/P) - venta sangre",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 18.0,
  "fecha_pfi": "2025-06-06",
  "notas": "Sangre. Se vende como \"Embarazo en sangre\""
 },
 {
  "sphm_codigo": "SPHMC21",
  "catalog_no": "F001-U2022",
  "ref_tonghzhou": "FHC-U222",
  "analito": "Pregnancy hCG Enhanced (S/P/U) - multimuestra",
  "muestra": "S/P/U",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 2.8,
  "fecha_pfi": "2026-03-03",
  "notas": "Multimuestra (suero/plasma/orina, NO sangre)"
 },
 {
  "sphm_codigo": "SPHMC26",
  "catalog_no": "F004-4022",
  "ref_tonghzhou": "FAMH-422",
  "analito": "AMH",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 120.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC47",
  "catalog_no": "F005-5022",
  "ref_tonghzhou": "FFF-522",
  "analito": "Fetal Fibronectin (fFN)",
  "muestra": "Vaginal Sec",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 90.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC66",
  "catalog_no": "I001-5022",
  "ref_tonghzhou": "ICA-522",
  "analito": "Candida albicans",
  "muestra": "Swab",
  "formato": "cassette+swab+tubo",
  "tests_por_hoja": 75,
  "precio_usd": 28.0,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC71",
  "catalog_no": "I002-5022",
  "ref_tonghzhou": "IGO-522",
  "analito": "Gonorrhea",
  "muestra": "Swab",
  "formato": "cassette+swab",
  "tests_por_hoja": 75,
  "precio_usd": 28.0,
  "fecha_pfi": "2025-08-11",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC51",
  "catalog_no": "I004-5022",
  "ref_tonghzhou": "ISB-522",
  "analito": "Strep B",
  "muestra": "Swab",
  "formato": "cassette+swab+tubo",
  "tests_por_hoja": 75,
  "precio_usd": 45.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC29",
  "catalog_no": "I013-6022",
  "ref_tonghzhou": "IGL-622",
  "analito": "Giardia Lamblia",
  "muestra": "Feces",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 70.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC44",
  "catalog_no": "I017-6022",
  "ref_tonghzhou": "",
  "analito": "Campylobacter",
  "muestra": "Feces",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 85.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC40",
  "catalog_no": "I021-4022",
  "ref_tonghzhou": "IHP-422",
  "analito": "H. pylori Antigen sangre",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 20.0,
  "fecha_pfi": "2025-12-17",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC46",
  "catalog_no": "I021-6022",
  "ref_tonghzhou": "IHP-622",
  "analito": "H. pylori Antigen heces",
  "muestra": "Feces",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 50.0,
  "fecha_pfi": "2025-08-15",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC57",
  "catalog_no": "I045-5022",
  "ref_tonghzhou": "IST-522",
  "analito": "Strep A",
  "muestra": "Swab",
  "formato": "cassette+swab",
  "tests_por_hoja": 75,
  "precio_usd": 28.0,
  "fecha_pfi": "2025-12-29",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC58",
  "catalog_no": "I047-1022",
  "ref_tonghzhou": "ISP-122",
  "analito": "Streptococcus pneumoniae Antigen",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 65.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC30",
  "catalog_no": "I049-4022",
  "ref_tonghzhou": "IMO-422",
  "analito": "MONO (Mononucleosis)",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 25.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC15",
  "catalog_no": "I051-5022",
  "ref_tonghzhou": "",
  "analito": "Influenza A+B",
  "muestra": "Swab/Nasal Aspirate",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 100.0,
  "fecha_pfi": "2025-12-29",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC41",
  "catalog_no": "I059-4022",
  "ref_tonghzhou": "ITE-422",
  "analito": "Tetanus",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 80.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC08",
  "catalog_no": "I098-5022",
  "ref_tonghzhou": "ICH-522",
  "analito": "Chlamydia",
  "muestra": "Swab/Urine",
  "formato": "cassette+swab+tubo",
  "tests_por_hoja": 75,
  "precio_usd": 21.0,
  "fecha_pfi": "2025-08-15",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC06",
  "catalog_no": "I099-4022",
  "ref_tonghzhou": "IHI-422",
  "analito": "HIV 1.2",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 20.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC02",
  "catalog_no": "I119-4022",
  "ref_tonghzhou": "ICOV-402",
  "analito": "COVID-19 IgG/IgM",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 100.0,
  "fecha_pfi": "2026-03-03",
  "notas": "Anticuerpos. SPHMC01 Covinet Ag es otra prueba"
 },
 {
  "sphm_codigo": "SPHMC60",
  "catalog_no": "I144-6022",
  "ref_tonghzhou": "ISHF-622",
  "analito": "Shigella Flexneri Antigen",
  "muestra": "Feces",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 45.0,
  "fecha_pfi": "2025-06-06",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC03",
  "catalog_no": "I160-4022",
  "ref_tonghzhou": "ICHM-422",
  "analito": "Chlamydia IgM",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 78.0,
  "fecha_pfi": "2025-08-11",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC25",
  "catalog_no": "O001-T4022",
  "ref_tonghzhou": "OFE-T422",
  "analito": "Ferritin Semi-Quantitative",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 55.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC37",
  "catalog_no": "O003-4022",
  "ref_tonghzhou": "OTS-422",
  "analito": "TSH",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 40.0,
  "fecha_pfi": "2026-03-03",
  "notas": "TSH cualitativa (produccion CORTA only). SPHMC52 semicuanti es produccion larga, no Tonghzhou."
 },
 {
  "sphm_codigo": "SPHMC09",
  "catalog_no": "O004-4022",
  "ref_tonghzhou": "OVD-422",
  "analito": "Vitamin D",
  "muestra": "Whole Blood",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 63.0,
  "fecha_pfi": "2025-08-11",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC50",
  "catalog_no": "O011-4022",
  "ref_tonghzhou": "OIGE-422",
  "analito": "IgE",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 65.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC16",
  "catalog_no": "O013-1022",
  "ref_tonghzhou": "OMAL-122",
  "analito": "Micro-Albumin Semi-Quantitative",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 22.0,
  "fecha_pfi": "2026-03-03",
  "notas": "Albumina semicuanti"
 },
 {
  "sphm_codigo": "SPHMC04",
  "catalog_no": "O014-1022",
  "ref_tonghzhou": "OMIA-122",
  "analito": "Micro-Albumin Qualitative",
  "muestra": "Urine",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 20.0,
  "fecha_pfi": "2025-08-15",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC36",
  "catalog_no": "T001-4022",
  "ref_tonghzhou": "TAF-422",
  "analito": "AFP (Alfa-fetoproteina)",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 18.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 },
 {
  "sphm_codigo": "SPHMC34",
  "catalog_no": "T004-4022",
  "ref_tonghzhou": "T153-422",
  "analito": "CA 15-3",
  "muestra": "WB/S/P",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 110.0,
  "fecha_pfi": "2025-12-17",
  "notas": "CONFIRMADO via PFI Z0005035A: CA15-3 Rapid Test Cassette"
 },
 {
  "sphm_codigo": "SPHMC64",
  "catalog_no": "T008-6025",
  "ref_tonghzhou": "TTFC-625",
  "analito": "Transferrin and FOB Combo",
  "muestra": "Feces",
  "formato": "cassette",
  "tests_por_hoja": 75,
  "precio_usd": 30.0,
  "fecha_pfi": "2026-03-03",
  "notas": ""
 }
]

MPCAR_DATA = [
 {
  "mpcar": "MPCAR02",
  "sphm": "SPHMC02",
  "ref": "ICOV-402",
  "price": 0.04,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR03",
  "sphm": "SPHMC03",
  "ref": "ICHM-422",
  "price": 0.04,
  "date": "2025-08-11"
 },
 {
  "mpcar": "MPCAR04",
  "sphm": "SPHMC04",
  "ref": "OMIA-122",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR06",
  "sphm": "SPHMC06",
  "ref": "IHI-422",
  "price": 0.04,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR08",
  "sphm": "SPHMC08",
  "ref": "ICH-522",
  "price": 0.04,
  "date": "2025-08-15"
 },
 {
  "mpcar": "MPCAR09",
  "sphm": "SPHMC09",
  "ref": "OVD-422",
  "price": 0.04,
  "date": "2025-08-11"
 },
 {
  "mpcar": "MPCAR10",
  "sphm": "SPHMC10",
  "ref": "DTH-121",
  "price": null,
  "date": null
 },
 {
  "mpcar": "MPCAR11",
  "sphm": "SPHMC11",
  "ref": "DAM-121",
  "price": null,
  "date": null
 },
 {
  "mpcar": "MPCAR12",
  "sphm": "SPHMC12",
  "ref": "DCO-121",
  "price": null,
  "date": null
 },
 {
  "mpcar": "MPCAR13",
  "sphm": "SPHMC13",
  "ref": "DME-121",
  "price": null,
  "date": null
 },
 {
  "mpcar": "MPCAR14",
  "sphm": "SPHMC14",
  "ref": "DOP-121",
  "price": null,
  "date": null
 },
 {
  "mpcar": "MPCAR16",
  "sphm": "SPHMC16",
  "ref": "OMAL-122",
  "price": 0.04,
  "date": "2025-08-15"
 },
 {
  "mpcar": "MPCAR21",
  "sphm": "SPHMC21",
  "ref": "FHC-U222",
  "price": 0.04,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR25",
  "sphm": "SPHMC25",
  "ref": "OFE-T422",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR26",
  "sphm": "SPHMC26",
  "ref": "FAMH-422",
  "price": 0.04,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR29",
  "sphm": "SPHMC29",
  "ref": "IGL-622",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR30",
  "sphm": "SPHMC30",
  "ref": "IMO-422",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR34",
  "sphm": "SPHMC34",
  "ref": "T153-422",
  "price": 0.03,
  "date": "2025-12-17"
 },
 {
  "mpcar": "MPCAR36",
  "sphm": "SPHMC36",
  "ref": "TAF-422",
  "price": 0.04,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR37",
  "sphm": "SPHMC37",
  "ref": "OTS-422",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR40",
  "sphm": "SPHMC40",
  "ref": "IHP-422",
  "price": 0.04,
  "date": "2025-12-17"
 },
 {
  "mpcar": "MPCAR41",
  "sphm": "SPHMC41",
  "ref": "ITE-422",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR46",
  "sphm": "SPHMC46",
  "ref": "IHP-622",
  "price": 0.04,
  "date": "2025-08-15"
 },
 {
  "mpcar": "MPCAR47",
  "sphm": "SPHMC47",
  "ref": "FFF-522",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR50",
  "sphm": "SPHMC50",
  "ref": "OIGE-422",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR51",
  "sphm": "SPHMC51",
  "ref": "ISB-522",
  "price": 0.025,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR57",
  "sphm": "SPHMC57",
  "ref": "IST-522",
  "price": 0.03,
  "date": "2025-12-29"
 },
 {
  "mpcar": "MPCAR58",
  "sphm": "SPHMC58",
  "ref": "ISP-122",
  "price": 0.025,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR60",
  "sphm": "SPHMC60",
  "ref": "ISHF-622",
  "price": 0.04,
  "date": "2025-06-06"
 },
 {
  "mpcar": "MPCAR63",
  "sphm": "SPHMC63",
  "ref": "DFY-121",
  "price": null,
  "date": null
 },
 {
  "mpcar": "MPCAR64",
  "sphm": "SPHMC64",
  "ref": "TTFC-625",
  "price": 0.03,
  "date": "2026-03-05"
 },
 {
  "mpcar": "MPCAR65",
  "sphm": "SPHMC65",
  "ref": "FHC-422",
  "price": 0.04,
  "date": "2025-06-06"
 },
 {
  "mpcar": "MPCAR66",
  "sphm": "SPHMC66",
  "ref": "ICA-522",
  "price": 0.04,
  "date": "2025-12-17"
 },
 {
  "mpcar": "MPCAR71",
  "sphm": "SPHMC71",
  "ref": "IGO-522",
  "price": 0.04,
  "date": "2025-08-11"
 },
 {
  "mpcar": "MPCAR73",
  "sphm": "SPHMC73",
  "ref": "CFC-425",
  "price": 0.04,
  "date": "2025-12-17"
 },
 {
  "mpcar": "MPCAR74",
  "sphm": "SPHMC74",
  "ref": "CFC-425",
  "price": 0.04,
  "date": "2025-12-17"
 }
]


# Asegurar pieza en uom_ids de cada SPHM
sphm_codes = sorted({r["sphm_codigo"] for r in SPHM_DATA})
ucount=0
for code in sphm_codes:
    h = env["product.template"].search([("default_code","=",code)], limit=1)
    if not h: continue
    if pieza and pieza not in h.uom_ids:
        h.uom_ids = [(4, pieza.id)]; ucount+=1
env.cr.commit()
print(f"  pieza agregada a uom_ids de {ucount} SPHMs")

# SPHM <- Tonghzhou
sphm_creados=0; sphm_existen=0; sphm_skip=0
for r in SPHM_DATA:
    h = env["product.template"].search([("default_code","=",r["sphm_codigo"])], limit=1)
    if not h or not tonghzhou: sphm_skip+=1; continue
    dup = env["product.supplierinfo"].search([
        ("product_tmpl_id","=",h.id),("partner_id","=",tonghzhou.id),
        ("product_code","=",r["catalog_no"]),
    ], limit=1)
    if dup: sphm_existen+=1; continue
    name_parts=[]
    if r["ref_tonghzhou"]: name_parts.append(r["ref_tonghzhou"])
    name_parts.append(r["analito"])
    if r["muestra"]: name_parts.append(f"({r['muestra']})")
    name_parts.append(f"[{r['tests_por_hoja']}T/hoja]")
    if r["formato"] and r["formato"]!="cassette": name_parts.append(f"[{r['formato']}]")
    vals = {
        "product_tmpl_id":h.id,"partner_id":tonghzhou.id,
        "product_code":r["catalog_no"],
        "product_name":" ".join(name_parts)[:128],
        "min_qty":1.0,
        "price":r["precio_usd"] or 0.0,
        "currency_id":usd.id,
    }
    if pieza: vals["product_uom_id"] = pieza.id
    if r["fecha_pfi"]:
        vals["date_start"] = datetime.strptime(r["fecha_pfi"], "%Y-%m-%d").date()
    env["product.supplierinfo"].create(vals)
    sphm_creados+=1
env.cr.commit()
print(f"  SPHM supplierinfo: creados={sphm_creados} existen={sphm_existen} skip={sphm_skip}")

# MPCAR <- Tonghzhou (cassettes via ACCE-00)
mpcar_creados=0; mpcar_existen=0; mpcar_skip=0
for r in MPCAR_DATA:
    mp = env["product.template"].search([("default_code","=",r["mpcar"])], limit=1)
    if not mp or not tonghzhou: mpcar_skip+=1; continue
    dup = env["product.supplierinfo"].search([
        ("product_tmpl_id","=",mp.id),("partner_id","=",tonghzhou.id),
        ("product_code","=","ACCE-00"),
        ("product_name","=like",f"Cassette for {r['ref']}%"),
    ], limit=1)
    if dup: mpcar_existen+=1; continue
    vals = {
        "product_tmpl_id":mp.id,"partner_id":tonghzhou.id,
        "product_code":"ACCE-00",
        "product_name":f"Cassette for {r['ref']} (impreso, ligado a SPHM {r['sphm']})",
        "min_qty":1.0,
    }
    if r["price"]:
        vals["price"]=r["price"]; vals["currency_id"]=usd.id
        vals["date_start"]=datetime.strptime(r["date"],"%Y-%m-%d").date()
    env["product.supplierinfo"].create(vals)
    mpcar_creados+=1
env.cr.commit()
print(f"  MPCAR supplierinfo: creados={mpcar_creados} existen={mpcar_existen} skip={mpcar_skip}")
