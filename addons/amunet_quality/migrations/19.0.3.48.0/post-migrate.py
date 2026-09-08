# -*- coding: utf-8 -*-
"""
Migración 48.0 — Códigos y versiones de reportes/certificados para PT.

FDC-017 versión vigente: los documentos de PT pasan de la versión 03 (papel)
a la versión 04 generada en Odoo. Se pre-cargan:
  - report_document_code  (RAPT-XXX)
  - certificate_document_code  (CERPT-XXX)
  - report_version = 4  /  report_replaces_version = 3
  - certificate_version = 4  /  certificate_replaces_version = 3

Solo se actualiza si los campos están vacíos (no sobrescribe si ya existía un
análisis finalizado previo que los hubiera establecido).
"""

# (default_code, RAPT, CERPT, TAPT)
PT_CODIGOS = [
    ('DMALC01', 'RAPT-001', 'CERPT-001', 'TAPT-001'),
    ('DRAM-002', 'RAPT-002', 'CERPT-002', 'TAPT-002'),
    ('DRAM-001', 'RAPT-003', 'CERPT-003', 'TAPT-003'),
    ('DMAFP01', 'RAPT-004', 'CERPT-004', 'TAPT-004'),
    ('DMAMH01', 'RAPT-005', 'CERPT-005', 'TAPT-005'),
    ('DMADO02', 'RAPT-006', 'CERPT-006', 'TAPT-006'),
    ('DMADO04', 'RAPT-007', 'CERPT-007', 'TAPT-007'),
    ('DMADO03', 'RAPT-008', 'CERPT-008', 'TAPT-008'),
    ('DMADG01', 'RAPT-009', 'CERPT-009', 'TAPT-009'),
    ('DMIAM01', 'RAPT-010', 'CERPT-010', 'TAPT-010'),
    ('DLBIO01', 'RAPT-011', 'CERPT-011', 'TAPT-011'),
    ('DLKRS01', 'RAPT-012', 'CERPT-012', 'TAPT-012'),
    ('DMADB01', 'RAPT-013', 'CERPT-013', 'TAPT-013'),
    ('DMACT02', 'RAPT-014', 'CERPT-014', 'TAPT-014'),
    ('DMASN01', 'RAPT-015', 'CERPT-015', 'TAPT-015'),
    ('DMCAO01', 'RAPT-016', 'CERPT-016', 'TAPT-016'),
    ('DMCAM01', 'RAPT-017', 'CERPT-017', 'TAPT-017'),
    ('DMCAP01', 'RAPT-018', 'CERPT-018', 'TAPT-018'),
    ('DMCAL01', 'RAPT-019', 'CERPT-019', 'TAPT-019'),
    ('DMCBR01', 'RAPT-020', 'CERPT-020', 'TAPT-020'),
    ('DMMCT01', 'RAPT-021', 'CERPT-021', 'TAPT-021'),
    ('DMCHA01', 'RAPT-022', 'CERPT-022', 'TAPT-022'),
    ('DMCHI01', 'RAPT-023', 'CERPT-023', 'TAPT-023'),
    ('DMICR01', 'RAPT-024', 'CERPT-024', 'TAPT-024'),
    ('DIAM-023', 'RAPT-025', 'CERPT-025', 'TAPT-025'),
    ('DIAM-025', 'RAPT-026', 'CERPT-026', 'TAPT-026'),
    ('DIAM-029', 'RAPT-027', 'CERPT-027', 'TAPT-027'),
    ('DIAM-024', 'RAPT-028', 'CERPT-028', 'TAPT-028'),
    ('DMCLAM01', 'RAPT-029', 'CERPT-029', 'TAPT-029'),
    ('DMCAN01', 'RAPT-030', 'CERPT-030', 'TAPT-030'),
    ('DMDEN01', 'RAPT-031', 'CERPT-031', 'TAPT-031'),
    ('DMDEN02', 'RAPT-032', 'CERPT-032', 'TAPT-032'),
    ('DMDMD01', 'RAPT-033', 'CERPT-033', 'TAPT-033'),
    ('DMHCG03', 'RAPT-034', 'CERPT-034', 'TAPT-034'),
    ('DMHCG02', 'RAPT-035', 'CERPT-035', 'TAPT-035'),
    ('DMHCG01', 'RAPT-036', 'CERPT-036', 'TAPT-036'),
    ('DMENT01', 'RAPT-037', 'CERPT-037', 'TAPT-037'),
    ('DMENG01', 'RAPT-038', 'CERPT-038', 'TAPT-038'),
    ('DMESC01', 'RAPT-039', 'CERPT-039', 'TAPT-039'),
    ('DMSPN01', 'RAPT-040', 'CERPT-040', 'TAPT-040'),
    ('DMSPN02', 'RAPT-041', 'CERPT-041', 'TAPT-041'),
    ('DMFRE01', 'RAPT-042', 'CERPT-042', 'TAPT-042'),
    ('DMFRT02', 'RAPT-043', 'CERPT-043', 'TAPT-043'),
    ('DMFFN01', 'RAPT-044', 'CERPT-044', 'TAPT-044'),
    ('DMGIA01', 'RAPT-045', 'CERPT-045', 'TAPT-045'),
    ('DMHPY01', 'RAPT-046', 'CERPT-046', 'TAPT-046'),
    ('DMHPY02', 'RAPT-047', 'CERPT-047', 'TAPT-047'),
    ('DMHBA01', 'RAPT-048', 'CERPT-048', 'TAPT-048'),
    ('DEMAM-001', 'RAPT-049', 'CERPT-049', 'TAPT-049'),
    ('DMMON01', 'RAPT-050', 'CERPT-050', 'TAPT-050'),
    ('DMMYC01', 'RAPT-051', 'CERPT-051', 'TAPT-051'),
    ('DMPRO01', 'RAPT-052', 'CERPT-052', 'TAPT-052'),
    ('DMIGE01', 'RAPT-053', 'CERPT-053', 'TAPT-053'),
    ('DMIVU01', 'RAPT-054', 'CERPT-054', 'TAPT-054'),
    ('DMIAB01', 'RAPT-055', 'CERPT-055', 'TAPT-055'),
    ('DMPHV01', 'RAPT-056', 'CERPT-056', 'TAPT-056'),
    ('DMPSA01', 'RAPT-057', 'CERPT-057', 'TAPT-057'),
    ('DMPSA02', 'RAPT-058', 'CERPT-058', 'TAPT-058'),
    ('DMRAV01', 'RAPT-059', 'CERPT-059', 'TAPT-059'),
    ('DMVSR01', 'RAPT-060', 'CERPT-060', 'TAPT-060'),
    ('DMSVI01', 'RAPT-061', 'CERPT-061', 'TAPT-061'),
    ('DMSAT01', 'RAPT-062', 'CERPT-062', 'TAPT-062'),
    ('DMSGF01', 'RAPT-063', 'CERPT-063', 'TAPT-063'),
    ('DIAM-002', 'RAPT-064', 'CERPT-064', 'TAPT-064'),
    ('DMSPO01', 'RAPT-065', 'CERPT-065', 'TAPT-065'),
    ('DMTET01', 'RAPT-066', 'CERPT-066', 'TAPT-066'),
    ('DMTRF01', 'RAPT-067', 'CERPT-067', 'TAPT-067'),
    ('DMTIF01', 'RAPT-068', 'CERPT-068', 'TAPT-068'),
    ('DMTOR02', 'RAPT-069', 'CERPT-069', 'TAPT-069'),
    ('DMTSH01', 'RAPT-070', 'CERPT-070', 'TAPT-070'),
    ('DMTSH02', 'RAPT-071', 'CERPT-071', 'TAPT-071'),
    ('DMATB01', 'RAPT-072', 'CERPT-072', 'TAPT-072'),
    ('DMVIH01', 'RAPT-073', 'CERPT-073', 'TAPT-073'),
    ('DMVIH02', 'RAPT-074', 'CERPT-074', 'TAPT-074'),
    ('DMVID01', 'RAPT-075', 'CERPT-075', 'TAPT-075'),
    ('DMZIK01', 'RAPT-076', 'CERPT-076', 'TAPT-076'),
    ('DLVPH01', 'RAPT-077', 'CERPT-077', 'TAPT-077'),
    ('DLHIV01', 'RAPT-078', 'CERPT-078', 'TAPT-078'),
    ('DLHPY01', 'RAPT-079', 'CERPT-079', 'TAPT-079'),
    ('DLTB02',  'RAPT-080', 'CERPT-080', 'TAPT-080'),
    ('DLVIH01', 'RAPT-081', 'CERPT-081', 'TAPT-081'),
    ('DLKRS01', 'RAPT-082', 'CERPT-082', 'TAPT-082'),
    ('DLSAN01', 'RAPT-083', 'CERPT-083', 'TAPT-083'),
]


def migrate(cr, version):
    import logging
    _logger = logging.getLogger(__name__)

    actualizados = 0
    for default_code, rapt, cerpt, tapt in PT_CODIGOS:
        cr.execute("""
            UPDATE product_template
            SET report_document_code      = %s,
                certificate_document_code = %s,
                report_version            = COALESCE(NULLIF(report_version, 0), 4),
                report_replaces_version   = CASE
                    WHEN (report_version IS NULL OR report_version = 0) THEN 3
                    ELSE report_replaces_version
                END,
                certificate_version       = COALESCE(NULLIF(certificate_version, 0), 4),
                certificate_replaces_version = CASE
                    WHEN (certificate_version IS NULL OR certificate_version = 0) THEN 3
                    ELSE certificate_replaces_version
                END,
                write_date = NOW()
            WHERE default_code = %s
              AND (report_document_code IS NULL OR report_document_code = '')
        """, (rapt, cerpt, default_code))
        if cr.rowcount:
            actualizados += cr.rowcount
            _logger.info("PT %s: report=%s cert=%s v4→3", default_code, rapt, cerpt)

    _logger.info("Migración 48.0: %d productos PT actualizados con códigos y versión 4.", actualizados)
