import json
import logging

_logger = logging.getLogger(__name__)

DESCRIPTIONS = {
    'SPHMC01': 'Prueba rápida para la detección de Antígenos anti-SARS-CoV-2 en muestras nasales y/o salivales',
    'SPHMC02': 'Prueba rápida para la detección de Anticuerpos de SARS-CoV-2 en sangre, suero y/o plasma',
    'SPHMC03': 'Prueba rápida para la detección de Anticuerpos IgM contra Chlamydia trachomatis en sangre, suero y/o plasma',
    'SPHMC04': 'Prueba rápida para la detección de Albúmina en muestras de orina',
    'SPHMC05': 'Prueba rápida para la detección de Anticuerpos IgG anti-Trypanosoma cruzi (Chagas) en sangre, suero y/o plasma',
    'SPHMC06': 'Prueba rápida para la detección de Anticuerpos contra VIH tipo 1 y 2 en sangre, suero y/o plasma',
    'SPHMC08': 'Prueba rápida para la detección de Antígeno de Chlamydia trachomatis en muestras cervicales u orina masculina',
    'SPHMC15': 'Prueba rápida para la detección de Antígenos de Influenza tipo A y tipo B en muestras nasales y salivales',
    'SPHMC17': 'Prueba rápida para la detección de Proteínas Mioglobina, CK-MB y Troponina cardíaca I (cTnI) en sangre, suero o plasma',
    'SPHMC20': 'Prueba rápida para la detección de Virus sincitial respiratorio (RSV) en muestras nasales y salivales',
    'SPHMC21': 'Prueba rápida para la detección de Gonadotropina Coriónica humana (hCG) en orina, suero o plasma',
    'SPHMC22': 'Prueba rápida para la detección de Anticuerpos contra Treponema pallidum (Sífilis) en sangre, suero o plasma',
    'SPHMC23': 'Prueba rápida para la detección de Antígeno p24 del virus de la inmunodeficiencia humana en sangre, suero o plasma',
    'SPHMC24': 'Prueba rápida para la detección de Antígeno prostático específico (PSA) en sangre, suero o plasma',
    'SPHMC27': 'Prueba rápida para la detección de Antígenos de Rotavirus y Adenovirus en heces',
    'SPHMC28': 'Prueba rápida para la detección de Anticuerpos anti-Tuberculosis (IgG, IgM e IgA) en sangre, suero o plasma',
    'SPHMC29': 'Prueba rápida para la detección de Antígeno de Giardia lamblia en heces',
    'SPHMC30': 'Prueba rápida para la detección de Anticuerpos heterófilos IgM contra Mononucleosis infecciosa en sangre, suero o plasma',
    'SPHMC31': 'Prueba rápida para la detección de Antígenos de Entamoeba histolytica, Giardia lamblia y Cryptosporidium en heces',
    'SPHMC32': 'Prueba rápida para la detección de Antígenos de Mycoplasma pneumoniae en muestras de orina',
    'SPHMC33': 'Prueba rápida para la detección de Proteína CA125 en sangre, suero o plasma',
    'SPHMC35': 'Prueba rápida para la detección de Sustancia CA 19-9 en sangre, suero o plasma',
    'SPHMC36': 'Prueba rápida para la detección de Alfa-fetoproteína (AFP) en sangre, suero o plasma',
    'SPHMC37': 'Prueba rápida para la detección de Hormona estimulante de la tiroides (TSH) en sangre, suero o plasma',
    'SPHMC39': 'Prueba rápida para la detección de Dímero D en sangre, suero o plasma',
    'SPHMC40': 'Prueba rápida para la detección de Anticuerpos contra Helicobacter pylori en sangre, suero o plasma',
    'SPHMC41': 'Prueba rápida para la detección de Anticuerpos contra la toxina del tétanos en sangre, suero o plasma',
    'SPHMC42': 'Prueba rápida para la detección de Factor reumatoide en suero o plasma',
    'SPHMC43': 'Prueba rápida para la detección de Anticuerpos IgG e IgM contra Salmonella typhi (Tifoidea) en sangre, suero o plasma',
    'SPHMC44': 'Prueba rápida para la detección de Antígeno de Campylobacter spp. en heces',
    'SPHMC45': 'Prueba rápida para la detección de Antígenos de Salmonella typhi en heces',
    'SPHMC46': 'Prueba rápida para la detección de Antígenos de Helicobacter pylori en heces',
    'SPHMC47': 'Prueba rápida para la detección de Fibronectina fetal en muestras cervicales',
    'SPHMC48': 'Prueba rápida para la detección de Antígenos de Entamoeba histolytica en heces',
    'SPHMC49': 'Prueba rápida para la detección de Anticuerpos IgG e IgM contra Toxoplasma gondii, Rubéola, Citomegalovirus y Herpes simple 1 y/o 2 (ToRCH) en sangre, suero o plasma',
    'SPHMC50': 'Prueba rápida para la detección de Inmunoglobulina E (IgE) en sangre, suero o plasma',
    'SPHMC51': 'Prueba rápida para la detección de Antígenos de Streptococcus B en muestras orofaríngeas',
    'SPHMC55': 'Prueba rápida para la detección de Calprotectina en heces',
    'SPHMC56': 'Prueba rápida para la detección de Anticuerpos IgG e IgM contra el virus de Chikungunya en sangre, suero o plasma',
    'SPHMC57': 'Prueba rápida para la detección de Antígenos de Streptococcus pyogenes (estreptococo A) en saliva u orofaringe',
    'SPHMC58': 'Prueba rápida para la detección de Antígenos de Streptococcus pneumoniae en muestras de orina',
    'SPHMC59': 'Prueba rápida para la detección de Péptido natriurético tipo B pro-N-terminal (NT-proBNP) en sangre, suero o plasma',
    'SPHMC60': 'Prueba rápida para la detección de Antígenos de Shigella Flexneri en heces',
    'SPHMC61': 'Prueba rápida para la detección de Antígenos del virus del Zika (NS1) en sangre, suero o plasma',
    'SPHMC62': 'Prueba rápida para la detección de Anticuerpos IgG e IgM contra el virus del Zika en sangre, suero o plasma',
    'SPHMC64': 'Prueba rápida para la detección de Transferrina y sangre oculta en heces (FOB)',
    'SPHMC65': 'Prueba rápida para la detección de Gonadotropina Coriónica humana (hCG) en sangre, suero o plasma',
    'SPHMC66': 'Prueba rápida para la detección de Antígenos de Candida albicans en muestras cervicales',
    'SPHMC69': 'Prueba rápida para la detección de Anticuerpos IgG contra Toxoplasma gondii, Rubéola, Citomegalovirus y Herpes simple 1 y/o 2 (ToRCH IgG) en sangre, suero o plasma',
    'SPHMC70': 'Prueba rápida para la detección de Anticuerpos IgM contra Toxoplasma gondii, Rubéola, Citomegalovirus y Herpes simple 1 y/o 2 (ToRCH IgM) en sangre, suero o plasma',
    'SPHMC71': 'Prueba rápida para la detección de Neisseria gonorrhoeae (Gonorrea) en sangre, suero o plasma',
    'SPHMC72': 'Prueba rápida para la detección de Antígenos de Cryptococcus en heces',
    'SPHMC73': 'Prueba rápida para la detección de Proteína acarreadora de ácidos grasos (FABP) en sangre, suero o plasma',
    'SPHMC74': 'Prueba rápida para la detección de Troponina I (cTnI) en sangre, suero o plasma',
    'SPHMT01': 'Prueba rápida para la detección de ADN amplificado marcado con FIT y FAM (Biotina) en muestras de ADN amplificado',
    'SPHMT03': 'Prueba rápida para la detección de ADN amplificado de Virus del Papiloma Humano (VPH) marcado con FIT y FAM en muestras de ADN amplificado',
    'SPHMT04': 'Prueba rápida para la detección de ADN amplificado de Helicobacter pylori (Pylorinet) marcado con FIT y FAM en muestras de ADN amplificado',
    'SPHMT05': 'Prueba rápida para la detección de ADN amplificado de Mycobacterium tuberculosis (TB-DxNet) marcado con FIT y FAM en muestras de ADN amplificado',
    'SPHMT06': 'Prueba rápida para la detección de Hormona Gonadotropina Coriónica (hCG) en muestras de orina',
}


def migrate(cr, version):
    """Migración 3.16.0: descripción (uso previsto) para las 59 hojas maestras SPHM/SPHMT."""
    updated = 0
    for code, desc in DESCRIPTIONS.items():
        json_val = json.dumps({'en_US': f'<p>{desc}</p>', 'es_MX': f'<p>{desc}</p>'}, ensure_ascii=False)
        cr.execute(
            "UPDATE product_template SET description = %s::jsonb, write_date = NOW() WHERE default_code = %s",
            (json_val, code),
        )
        updated += cr.rowcount

    # Propagar a checks en borrador/progreso que aún no tienen descripción
    codes = list(DESCRIPTIONS.keys())
    cr.execute("""
        UPDATE amunet_quality_check qc
        SET product_description = pt.description, write_date = NOW()
        FROM product_product pp
        JOIN product_template pt ON pt.id = pp.product_tmpl_id
        WHERE qc.product_id = pp.id
          AND pt.default_code = ANY(%s)
          AND qc.state IN ('draft', 'in_progress')
          AND (qc.product_description IS NULL OR qc.product_description::text = '')
    """, (codes,))
    checks = cr.rowcount

    _logger.info(
        "Migración 3.16.0 completa — descripciones actualizadas: %d productos, %d checks en progreso",
        updated, checks,
    )
