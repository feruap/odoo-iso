"""
create_product_hoja_maestra_antidoping_sangre.py
Crea o corrige producto SPHMC75 basado en SPHMC53.
Fixes: (1) no usa columna datas en ir_attachment (Odoo 17+), (2) usa SAVEPOINT para imagen.
"""
import sys, json
from datetime import datetime, timezone
try:
    import psycopg2, psycopg2.extras
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable,'-m','pip','install','psycopg2-binary','-q'])
    import psycopg2, psycopg2.extras

SOURCE_CODE='SPHMC53'
NEW_NAME='Hoja Maestra Antidoping Sangre 2 Par\u00e1metros'
NEW_CODE='SPHMC75'
db,user,pwd,host,port=sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],int(sys.argv[5])
print(f"[{db}] Conectando a {host}:{port}...")
conn=psycopg2.connect(dbname=db,user=user,password=pwd,host=host,port=port)
conn.autocommit=False
cur=conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
now=datetime.now(timezone.utc)

def get_source_tmpl_id():
    cur.execute("SELECT pt.id FROM product_template pt JOIN product_product pp ON pp.product_tmpl_id=pt.id WHERE pp.default_code=%s LIMIT 1",(SOURCE_CODE,))
    r=cur.fetchone(); return r['id'] if r else None

def fix_codes(tmpl_id, pp_id=None):
    """Actualiza default_code en product_product Y product_template."""
    if pp_id:
        cur.execute("UPDATE product_product SET default_code=%s WHERE id=%s",(NEW_CODE,pp_id))
        print(f"[OK]   pp id={pp_id} default_code='{NEW_CODE}'")
    else:
        cur.execute("UPDATE product_product SET default_code=%s WHERE product_tmpl_id=%s AND (default_code!=%s OR default_code IS NULL)",(NEW_CODE,tmpl_id,NEW_CODE))
        print(f"[OK]   product_product updated: {cur.rowcount} row(s)")
    cur.execute("SELECT 1 FROM information_schema.columns WHERE table_schema='public' AND table_name='product_template' AND column_name='default_code'")
    if cur.fetchone():
        cur.execute("UPDATE product_template SET default_code=%s WHERE id=%s",(NEW_CODE,tmpl_id))
        print(f"[OK]   product_template.default_code='{NEW_CODE}'")

def has_image(tmpl_id):
    cur.execute("SELECT id FROM ir_attachment WHERE res_model='product.template' AND res_field='image_1920' AND res_id=%s LIMIT 1",(tmpl_id,))
    return cur.fetchone() is not None

def copy_image(src_id, dst_id):
    """Copia imagen. Detecta columnas disponibles en ir_attachment dinamicamente."""
    cur.execute("SELECT id,name,mimetype,store_fname,file_size FROM ir_attachment WHERE res_model='product.template' AND res_field='image_1920' AND res_id=%s ORDER BY id DESC LIMIT 1",(src_id,))
    att=cur.fetchone()
    if not att:
        cur.execute("SELECT id,name,mimetype,store_fname,file_size FROM ir_attachment WHERE res_model='product.template' AND res_id=%s AND mimetype ILIKE 'image/%' ORDER BY id DESC LIMIT 1",(src_id,))
        att=cur.fetchone()
    if not att:
        print(f"[WARN] No image found for src_tmpl_id={src_id}"); return False
    if not att['store_fname']:
        print(f"[WARN] store_fname is empty"); return False
    print(f"[INFO] Image: id={att['id']}, mime={att['mimetype']}, store_fname={att['store_fname']}, size={att['file_size']}")
    cur.execute("DELETE FROM ir_attachment WHERE res_model='product.template' AND res_field='image_1920' AND res_id=%s",(dst_id,))
    # Detectar columnas disponibles para no hardcodear
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='ir_attachment'")
    existing={r['column_name'] for r in cur.fetchall()}
    data={'name':att['name'] or 'image','res_model':'product.template','res_field':'image_1920',
          'res_id':dst_id,'type':'binary','mimetype':att['mimetype'] or 'image/jpeg',
          'store_fname':att['store_fname'],'file_size':att['file_size'] or 0,'create_date':now,'write_date':now}
    for col,val in {'res_name':NEW_NAME,'public':False,'create_uid':1,'write_uid':1}.items():
        if col in existing: data[col]=val
    cols=list(data.keys()); vals=[data[c] for c in cols]
    cur.execute("SAVEPOINT img_copy")
    try:
        cur.execute(f"INSERT INTO ir_attachment ({','.join(cols)}) VALUES ({','.join(['%s']*len(vals))})",vals)
        cur.execute("RELEASE SAVEPOINT img_copy")
        print(f"[OK]   Image copied to dst_tmpl_id={dst_id}"); return True
    except Exception as e:
        cur.execute("ROLLBACK TO SAVEPOINT img_copy")
        print(f"[ERROR] Image copy failed: {e}"); return False

# Case 1: SPHMC75 ya existe
cur.execute("SELECT pt.id,pp.id AS pp_id FROM product_template pt JOIN product_product pp ON pp.product_tmpl_id=pt.id WHERE pp.default_code=%s LIMIT 1",(NEW_CODE,))
r=cur.fetchone()
if r:
    fix_codes(r['id'],r['pp_id'])
    if has_image(r['id']):
        print(f"[{db}] '{NEW_CODE}' already correct with image Ã¢ÂÂ done.")
        conn.commit(); conn.close(); sys.exit(0)
    src=get_source_tmpl_id()
    if src: copy_image(src,r['id'])
    conn.commit(); conn.close()
    print(f"[LISTO] Imagen actualizada en '{db}'."); sys.exit(0)

# Case 2: codigo incorrecto + nombre correcto
cur.execute("SELECT pt.id,pp.id AS pp_id FROM product_template pt JOIN product_product pp ON pp.product_tmpl_id=pt.id WHERE pp.default_code=%s AND pt.name::text ILIKE '%Antidoping Sangre%' LIMIT 1",(SOURCE_CODE,))
r=cur.fetchone()
if r:
    print(f"[{db}] Wrong code found (tmpl_id={r['id']}) Ã¢ÂÂ fixing...")
    fix_codes(r['id'],r['pp_id'])
    if not has_image(r['id']):
        src=get_source_tmpl_id()
        if src: copy_image(src,r['id'])
    else:
        print("[OK]   Image already exists")
    conn.commit(); conn.close()
    print(f"[LISTO] '{NEW_CODE}' corregido en '{db}'."); sys.exit(0)

# Case 3: crear desde cero
print(f"[{db}] Creating '{NEW_CODE}' from scratch...")
src_tmpl_id=get_source_tmpl_id()
if not src_tmpl_id:
    print(f"[ERROR] Source '{SOURCE_CODE}' not found Ã¢ÂÂ aborting"); conn.close(); sys.exit(1)
print(f"[OK]   Source: tmpl_id={src_tmpl_id}")
SKIP_TMPL={'id','create_date','write_date','create_uid','write_uid','default_code','image_1920','image_128','active'}
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='product_template' ORDER BY ordinal_position")
copy_cols=[r['column_name'] for r in cur.fetchall() if r['column_name'] not in SKIP_TMPL]
cur.execute(f"SELECT {','.join(copy_cols)} FROM product_template WHERE id=%s",(src_tmpl_id,))
src_row=cur.fetchone()
values=[src_row[c] for c in copy_cols]
if 'name' in copy_cols:
    idx=copy_cols.index('name'); orig=src_row['name']
    if isinstance(orig,dict): values[idx]={k:NEW_NAME for k in orig}
    elif isinstance(orig,str):
        try: parsed=json.loads(orig); values[idx]=json.dumps({k:NEW_NAME for k in parsed})
        except: values[idx]=NEW_NAME
    else: values[idx]=NEW_NAME
values+=[NEW_CODE,True,now,now]
cols_str=','.join(copy_cols+['default_code','active','create_date','write_date'])
cur.execute(f"INSERT INTO product_template({cols_str}) VALUES({','.join(['%s']*len(values))}) RETURNING id",values)
new_tmpl_id=cur.fetchone()['id']
print(f"[OK]   product_template created: id={new_tmpl_id}")
SKIP_PP={'id','create_date','write_date','create_uid','write_uid','product_tmpl_id','default_code','active'}
cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name='product_product' ORDER BY ordinal_position")
copy_pp=[r['column_name'] for r in cur.fetchall() if r['column_name'] not in SKIP_PP]
cur.execute("SELECT pp.id FROM product_product pp WHERE pp.product_tmpl_id=%s LIMIT 1",(src_tmpl_id,))
src_pp=cur.fetchone()
if src_pp:
    cur.execute(f"SELECT {','.join(copy_pp)} FROM product_product WHERE id=%s",(src_pp['id'],))
    src_pp_row=cur.fetchone()
    pp_vals=[src_pp_row[c] for c in copy_pp]+[new_tmpl_id,NEW_CODE,True,now,now]
    pp_cols=','.join(copy_pp+['product_tmpl_id','default_code','active','create_date','write_date'])
else:
    pp_cols='product_tmpl_id,default_code,active,create_date,write_date'; pp_vals=[new_tmpl_id,NEW_CODE,True,now,now]
cur.execute(f"INSERT INTO product_product({pp_cols}) VALUES({','.join(['%s']*len(pp_vals))}) RETURNING id",pp_vals)
new_pp_id=cur.fetchone()['id']
print(f"[OK]   product_product created: id={new_pp_id} code='{NEW_CODE}'")
copy_image(src_tmpl_id,new_tmpl_id)
conn.commit(); conn.close()
print(f"[LISTO] '{NEW_CODE}' creado en '{db}'.")
