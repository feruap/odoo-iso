import logging

_logger = logging.getLogger(__name__)

DESCRIPTIONS = {
    # Colorimétricas
    'SPHMC07': 'Prueba rápida para la detección de Hemoglobina glicada en muestras de sangre total o capilar',
    'SPHMC09': 'Prueba rápida para la detección de 25 Hidroxivitamina D [25(OH)D] en muestras de sangre total o capilar',
    'SPHMC26': 'Prueba rápida para la detección de Hormona antimülleriana (AMH) en muestras de sangre, suero o plasma',
    'SPHMC67': 'Prueba rápida para la detección de Alcohol en muestras salivales',
    'SPHMC68': 'Prueba rápida para la determinación de pH vaginal en muestras vaginales',
    'SPHMT02': 'Prueba rápida para la detección de infecciones en vías urinarias (Leucocitos, proteínas, sangre y nitritos) en muestras de orina',
    # Cualitativas competitivas
    'SPHMC10': 'Prueba rápida para la detección de Tetrahidrocannabinol (THC/Marihuana) en muestras de sangre, suero, plasma, orina y saliva',
    'SPHMC11': 'Prueba rápida para la detección de Anfetamina en muestras de sangre, suero, plasma, orina y saliva',
    'SPHMC12': 'Prueba rápida para la detección de Cocaína en muestras de sangre, suero, plasma, orina y saliva',
    'SPHMC13': 'Prueba rápida para la detección de Metanfetamina en muestras de sangre, suero, plasma, orina y saliva',
    'SPHMC14': 'Prueba rápida para la detección de Opiáceos en muestras de sangre, suero, plasma, orina y saliva',
    'SPHMC53': 'Prueba rápida para la detección de Antidoping 2 parámetros, combinación de drogas (THC, COC, AMP, OPI y MET) en muestras de sangre, suero, plasma, orina y/o saliva',
    'SPHMC54': 'Prueba rápida para la detección de Antidoping 3 parámetros, combinación de drogas (THC, COC y AMP) en muestras de sangre, suero, plasma, orina y/o saliva',
    # Otras cualitativas sin descripción
    'SPHMC16': 'Prueba rápida para la detección de Albúmina semicuantitativa en muestras de orina',
    'SPHMC18': 'Prueba rápida para la detección de Anticuerpos anti-Dengue (IgG e IgM) en muestras de sangre, suero o plasma',
    'SPHMC19': 'Prueba rápida para la detección de Antígeno NS1 del virus del Dengue en muestras de sangre, suero o plasma',
    'SPHMC25': 'Prueba rápida para la detección de Ferritina en muestras de sangre, suero o plasma',
    'SPHMC34': 'Prueba rápida para la detección de Antígeno carbohidratado CA 15-3 en muestras de sangre, suero o plasma',
    'SPHMC38': 'Prueba rápida para la detección de Antígeno prostático específico (PSA) semicuantitativa en muestras de sangre, suero o plasma',
    'SPHMC52': 'Prueba rápida para la detección de Hormona estimulante de la tiroides (TSH) semicuantitativa en muestras de sangre, suero o plasma',
    'SPHMC63': 'Prueba rápida para la detección de Fentanilo en muestras de sangre, suero, plasma, orina y/o saliva',
}


def migrate(cr, version):
    """Migración 3.24.0: carga descripciones (uso previsto) en hojas SPHM que las tenían vacías.

    Solo actualiza hojas cuya descripción sea NULL o vacía; no sobreescribe
    descripciones que alguien haya capturado manualmente.
    """
    updated = 0
    for code, texto in DESCRIPTIONS.items():
        jsonb = '{{"en_US": "<p>{0}</p>", "es_MX": "<p>{0}</p>"}}'.format(texto)
        cr.execute("""
            UPDATE product_template
            SET description = %s::jsonb,
                write_date  = NOW()
            WHERE default_code = %s
              AND (description IS NULL OR description::text IN ('null', '{}', '""'))
        """, (jsonb, code))
        updated += cr.rowcount

    _logger.info(
        "Migración 3.24.0 — Descripciones de uso previsto: %d hojas actualizadas de %d",
        updated, len(DESCRIPTIONS),
    )
