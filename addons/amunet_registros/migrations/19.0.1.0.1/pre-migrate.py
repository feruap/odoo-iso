def migrate(cr, version):
    cr.execute("ALTER TABLE amunet_reg_entrega_vest_linea DROP COLUMN IF EXISTS empleado_nombre;")
    cr.execute("ALTER TABLE amunet_reg_revision_vest_linea DROP COLUMN IF EXISTS empleado_nombre;")
