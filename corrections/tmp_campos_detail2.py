# Ver todos los campos del modelo detail para saber exactamente qué acepta create()
Detail = env['amunet.quality.test.line.detail']
campos_str = [(n, str(f.type), getattr(f, 'required', False)) 
              for n, f in Detail._fields.items()
              if not n.startswith('_')]
for n, t, req in sorted(campos_str):
    r = ' *' if req else ''
    print(f"  {n}: {t}{r}")
