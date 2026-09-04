Detail = env['amunet.quality.test.line.detail']
campos_rel = [(n, str(f.type)) for n, f in Detail._fields.items() 
              if f.type in ('many2one', 'many2many') or 'line' in n.lower() or 'spec' in n.lower()]
for n, t in sorted(campos_rel):
    print(f"  {n}: {t}")
