# El modelo no permite unlink — cancelar y borrar vía SQL
env.cr.execute("""
    UPDATE amunet_material_request SET state='cancelled' 
    WHERE name IN ('SMP/26/00131') AND id = 146
""")
env.cr.execute("DELETE FROM amunet_material_request_line WHERE request_id = 146")
env.cr.execute("DELETE FROM amunet_material_request WHERE id = 146")
env.cr.commit()
print("SMP/26/00131 eliminada.")
