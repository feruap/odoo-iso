-- ============================================================
-- CORRECCIÓN: Denominación genérica en campo description de PT
-- Base de datos: amunet_prod
-- Fecha: 2026-09-21
-- Fuente: clasificacion de pruebas.xlsx (Diana Flores, Calidad)
--
-- Actualiza el campo description en product_template con la
-- denominación genérica oficial para cada PT.
-- Solo aplica si el campo está vacío/nulo (no pisa datos manuales).
-- ============================================================

BEGIN;

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de alfa-fetoproteína (AFP) en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de alfa-fetoproteína (AFP) en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMAFP01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de albúmina en muestras de orina.", "es_MX": "Prueba rápida para la detección cualitativa de albúmina en muestras de orina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DRAM-002' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa de albumina en muestras de orina", "es_MX": "Prueba rápida para la detección semicuantitativa de albumina en muestras de orina"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DRAM-001' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa de alcohol en saliva", "es_MX": "Prueba rápida para la detección semicuantitativa de alcohol en saliva"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMALC01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa de la hormona antimülleriana en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección semicuantitativa de la hormona antimülleriana en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMAMH01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa y diferencial de marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI) y metanfetamina (MET) en muestras de orina.", "es_MX": "Prueba rápida para la detección cualitativa y diferencial de marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI) y metanfetamina (MET) en muestras de orina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMADO02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa y diferencial de marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI) y metanfetamina (MET) en muestras de saliva.", "es_MX": "Prueba rápida para la detección cualitativa y diferencial de marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI) y metanfetamina (MET) en muestras de saliva."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMADB01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígeno CA 125 en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de antígeno CA 125 en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCAO01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno CA 15-3 en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa del antígeno CA 15-3 en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCAM01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno CA 19-9 en muestras de sangre total / capilar, suero plasma", "es_MX": "Prueba rápida para la detección cualitativa del antígeno CA 19-9 en muestras de sangre total / capilar, suero plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCAP01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de calprotectina en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de calprotectina en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCAL01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de Campylobacter en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de Campylobacter en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCBR01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígeno de Candida albicans en muestras de exudado vaginal.", "es_MX": "Prueba rápida para la detección cualitativa de antígeno de Candida albicans en muestras de exudado vaginal."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCAN01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de la proteína de unión de ácidos grasos de tipo cardiaco (H-FABP) y Troponina I (cTnI) en muestras de Sangre total/capilar, Suero o Plasma.", "es_MX": "Prueba rápida para la detección cualitativa de la proteína de unión de ácidos grasos de tipo cardiaco (H-FABP) y Troponina I (cTnI) en muestras de Sangre total/capilar, Suero o Plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMIAM01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpo IgG anti-Trypanosoma cruzi en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpo IgG anti-Trypanosoma cruzi en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCHA01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos IgG e IgM contra el virus de chikungunya en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos IgG e IgM contra el virus de chikungunya en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCHI01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Entamoeba histolystica y Giardia lamblia en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Entamoeba histolystica y Giardia lamblia en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMENG01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Entamoeba histolytica y Salmonella typhi en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Entamoeba histolytica y Salmonella typhi en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMESC01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos contra Treponema pallidum y VIH tipo 1 y 2 en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos contra Treponema pallidum y VIH tipo 1 y 2 en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMSVI01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de los antígenos del SARS-CoV-2 e Influenza A y B en muestras nasofaríngeas.", "es_MX": "Prueba rápida para la detección cualitativa de los antígenos del SARS-CoV-2 e Influenza A y B en muestras nasofaríngeas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DIAM-024' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos IgG e IgM contra la proteína N y S del SARS-CoV-2.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos IgG e IgM contra la proteína N y S del SARS-CoV-2."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DIAM-023' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos IgG e IgM anti-Dengue en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos IgG e IgM anti-Dengue en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMDEN02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de Dímero – D en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de Dímero – D en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMDMD01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de hormona gonadotropina coriónica en muestras de orina humana.", "es_MX": "Prueba rápida para la detección cualitativa de hormona gonadotropina coriónica en muestras de orina humana."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMHCG03' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de la hormona gonadotropina coriónica en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de la hormona gonadotropina coriónica en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMHCG01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Entamoeba histolytica en muestreas de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Entamoeba histolytica en muestreas de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMENT01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígeno de Streptococcus pyogenes en muestras orofaríngeas.", "es_MX": "Prueba rápida para la detección cualitativa de antígeno de Streptococcus pyogenes en muestras orofaríngeas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMSPN02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígeno de Streptococcus del grupo B (EGB) en muestras de hisopado vaginal o rectal en mujeres embarazadas o hisopo general en recién nacidos.", "es_MX": "Prueba rápida para la detección cualitativa de antígeno de Streptococcus del grupo B (EGB) en muestras de hisopado vaginal o rectal en mujeres embarazadas o hisopo general en recién nacidos."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMSPN01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de fentanilo en muestras de orina.", "es_MX": "Prueba rápida para la detección cualitativa de fentanilo en muestras de orina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMFEN01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de Fibronectina fetal (fFN) en muestras de cervicovaginales durante el embarazo.", "es_MX": "Prueba rápida para la detección cualitativa de Fibronectina fetal (fFN) en muestras de cervicovaginales durante el embarazo."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMFFN01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno de Giardia lamblia en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa del antígeno de Giardia lamblia en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMGIA01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de hemoglobina glicada (HbA1c) en muestras de sangre total / capilar", "es_MX": "Prueba rápida para la detección cualitativa de hemoglobina glicada (HbA1c) en muestras de sangre total / capilar"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMHBA01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos contra Helicobacter pylori en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos contra Helicobacter pylori en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMHYP01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Helicobacter pylori en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Helicobacter pylori en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMHPY02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos IgE en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos IgE en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMIGE01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de sangre, proteínas, nitritos y leucocitos en muestras de orina.", "es_MX": "Prueba rápida para la detección cualitativa de sangre, proteínas, nitritos y leucocitos en muestras de orina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMIVU01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos heterófilos (IgM) contra mononucleosis infecciosa en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos heterófilos (IgM) contra mononucleosis infecciosa en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMMON01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígeno de NT-proBNP en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de antígeno de NT-proBNP en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMPRO01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa de pH vaginal en muestras de hisopado vaginal.", "es_MX": "Prueba rápida para la detección semicuantitativa de pH vaginal en muestras de hisopado vaginal."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMPHV01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa del antígeno prostático específico en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección semicuantitativa del antígeno prostático específico en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMPSA01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Salmonella typhi en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Salmonella typhi en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMSAT' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Shigella flexneri en muestras de heces humanas.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Shigella flexneri en muestras de heces humanas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMSGF01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de antígenos de Streptococcus pneumoniae en muestras de orina humana.", "es_MX": "Prueba rápida para la detección cualitativa de antígenos de Streptococcus pneumoniae en muestras de orina humana."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'SMSPO01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos contra la toxina del tétanos en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos contra la toxina del tétanos en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMTET01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos tipo IgG e IgM contra Salmonella typhi en muestras de total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos tipo IgG e IgM contra Salmonella typhi en muestras de total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMTIF01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos IgG/IgM contra Toxoplasma gondii, Virus de la rubeola, y virus del herpes simple 1 y/o 2 en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos IgG/IgM contra Toxoplasma gondii, Virus de la rubeola, y virus del herpes simple 1 y/o 2 en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMTOR02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de transferrina y hemoglobina en muestras de heces humanas", "es_MX": "Prueba rápida para la detección cualitativa de transferrina y hemoglobina en muestras de heces humanas"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMTRF01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de la hormona estimulante de la tiroides en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa de la hormona estimulante de la tiroides en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMTSH01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa de la hormona estimulante de la tiroides en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección semicuantitativa de la hormona estimulante de la tiroides en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMTSH02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "La prueba rápida para la detección cualitativa de anticuerpos anti-TB (isotipos de IgG e IgA) en muestras de sangre total en muestras de sangre total / capilar, suero o plasma", "es_MX": "La prueba rápida para la detección cualitativa de anticuerpos anti-TB (isotipos de IgG e IgA) en muestras de sangre total en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMATB01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos contra el virus de inmunodeficiencia humana tipo 1 y 2 en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos contra el virus de inmunodeficiencia humana tipo 1 y 2 en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMVIH01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos contra VIH tipo 1, tipo 2 y el antígeno p24 del VIH-1 en muestras de sangre total / capilar, suero o plasma", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos contra VIH tipo 1, tipo 2 y el antígeno p24 del VIH-1 en muestras de sangre total / capilar, suero o plasma"}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMVIH02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno NS1 del virus del zika del virus del zika y anticuerpos IgG e IgM anti zika en muestras de sangre total / capilar, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa del antígeno NS1 del virus del zika del virus del zika y anticuerpos IgG e IgM anti zika en muestras de sangre total / capilar, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMZIK01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para detección cualitativa y diferencial de drogas: marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI), y metanfetamina(MET).", "es_MX": "Prueba rápida en cartucho para detección cualitativa y diferencial de drogas: marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI), y metanfetamina(MET)."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMADO01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de analitos (anticuerpos, proteínas o amplificaciones genómicas) marcados simultáneamente con fluorescencia (FITC/FAM) y biotina.", "es_MX": "Prueba rápida para la detección cualitativa de analitos (anticuerpos, proteínas o amplificaciones genómicas) marcados simultáneamente con fluorescencia (FITC/FAM) y biotina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DLBIO01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa y diferencial de las proteínas mioglobina, CK-Mb y Troponina cardiaca I(cTnl).", "es_MX": "Prueba rápida para la detección cualitativa y diferencial de las proteínas mioglobina, CK-Mb y Troponina cardiaca I(cTnl)."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMMCT01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para la detección cualitativa del antígeno de Chlamydia trachomatis en muestras de exudado cervical/uretral u orina masculina.", "es_MX": "Prueba rápida en cartucho para la detección cualitativa del antígeno de Chlamydia trachomatis en muestras de exudado cervical/uretral u orina masculina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCLAM01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa y diferencial de anticuerpos IgG e IgM contra los virus del dengue (DENV), Chikunguña (CHIKV) y zika (ZIKV) en muestras de sangre (total o capilar), suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa y diferencial de anticuerpos IgG e IgM contra los virus del dengue (DENV), Chikunguña (CHIKV) y zika (ZIKV) en muestras de sangre (total o capilar), suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMDCZ01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para la detección cualitativa y diferencial de los antígenos de influenza A Y b, SARS-CoV-2 Y RSV (virus sincitial respiratorio) en muestras nasofaríngeas.", "es_MX": "Prueba rápida en cartucho para la detección cualitativa y diferencial de los antígenos de influenza A Y b, SARS-CoV-2 Y RSV (virus sincitial respiratorio) en muestras nasofaríngeas."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMCRD01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de la nucleoproteína N del virus SARS.CoV en muestras nasofaríngeas y de saliva.", "es_MX": "Prueba rápida para la detección cualitativa de la nucleoproteína N del virus SARS.CoV en muestras nasofaríngeas y de saliva."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DIAM-025' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de la nucleoproteína N del virus SARS.CoV en muestras nasofaríngeas y de saliva.", "es_MX": "Prueba rápida para la detección cualitativa de la nucleoproteína N del virus SARS.CoV en muestras nasofaríngeas y de saliva."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DIAM-029' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno NS1 y anticuerpos IgG e IgM del virus de dengue en sangre, suero y plasma.", "es_MX": "Prueba rápida para la detección cualitativa del antígeno NS1 y anticuerpos IgG e IgM del virus de dengue en sangre, suero y plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMDEN01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para detección cualitativa y diferencial de drogas: marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI), metanfetamina(MET), y alcohol (ALC) en muestra de saliva.", "es_MX": "Prueba rápida en cartucho para detección cualitativa y diferencial de drogas: marihuana (THC), anfetamina (AMP), cocaína (COC), opiáceos (OPI), metanfetamina(MET), y alcohol (ALC) en muestra de saliva."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMDRO01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección semicuantitativa de ferritina en muestras de sangre (total/capilar), suero y plasma.", "es_MX": "Prueba rápida para la detección semicuantitativa de ferritina en muestras de sangre (total/capilar), suero y plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMFRT02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa y diferencial, y además, diferenciación del virus de la influenza tipo A y B.", "es_MX": "Prueba rápida para la detección cualitativa y diferencial, y además, diferenciación del virus de la influenza tipo A y B."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMIAB01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno prostático especifico (PSA) en muestras de suero, plasma u orina.", "es_MX": "Prueba rápida para la detección cualitativa del antígeno prostático especifico (PSA) en muestras de suero, plasma u orina."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMHCG02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para la detección semicuantitativa de hemoglobina glicada en sangre total.", "es_MX": "Prueba rápida en cartucho para la detección semicuantitativa de hemoglobina glicada en sangre total."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DEMAM-001' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa del antígeno prostático específico (PSA) en muestras de sangre, suero o plasma.", "es_MX": "Prueba rápida para la detección cualitativa del antígeno prostático específico (PSA) en muestras de sangre, suero o plasma."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMPSA02' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de ADN bacteriano de Helicobacter pylori en muestras de saliva.", "es_MX": "Prueba rápida para la detección cualitativa de ADN bacteriano de Helicobacter pylori en muestras de saliva."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DLHPY01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa y diferencial de los antígenos de rotavirus y adenovirus en muestras de heces.", "es_MX": "Prueba rápida para la detección cualitativa y diferencial de los antígenos de rotavirus y adenovirus en muestras de heces."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMRAV01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de los antígenos del virus sincitial respiratorio (RSV).", "es_MX": "Prueba rápida para la detección cualitativa de los antígenos del virus sincitial respiratorio (RSV)."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMVSR01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida para la detección cualitativa de anticuerpos Anti-Treponema pallidum en muestras de sangre, suero y plasma humano.", "es_MX": "Prueba rápida para la detección cualitativa de anticuerpos Anti-Treponema pallidum en muestras de sangre, suero y plasma humano."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DIAM-002' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para la detección semicuantitativa de la 25 hidroxivitamina D (25(OH)D).", "es_MX": "Prueba rápida en cartucho para la detección semicuantitativa de la 25 hidroxivitamina D (25(OH)D)."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DMVID01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

UPDATE product_template SET description = '{"en_US": "Prueba rápida en cartucho para la detección cualitativa de ADN del virus del papiloma humano (VPH).", "es_MX": "Prueba rápida en cartucho para la detección cualitativa de ADN del virus del papiloma humano (VPH)."}'::jsonb, write_date = NOW()
  WHERE id = (SELECT product_tmpl_id FROM product_product WHERE default_code = 'DLVPH01' LIMIT 1)
  AND (description IS NULL OR description::text = '{}' OR description::text = 'null' OR description::text = '');

COMMIT;

-- Verificación post-ejecución:
-- SELECT pp.default_code, pt.description->>'es_MX' AS desc
-- FROM product_product pp
-- JOIN product_template pt ON pt.id=pp.product_tmpl_id
-- WHERE pp.default_code IN ('DMAFP01','DRAM-002','DRAM-001','DMALC01','DMAMH01','DMADO02','DMADB01','DMCAO01','DMCAM01','DMCAP01')
-- ORDER BY pp.default_code;