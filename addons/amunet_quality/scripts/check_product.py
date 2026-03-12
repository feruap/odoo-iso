if 'env' in locals():
    print("--- Buscando ID 546 ---")
    for m in ['product.template', 'product.product']:
        rec = env[m].browse(546)
        if rec.exists():
            print(f"ID 546 SI existe en {m}: {rec.name} / {rec.default_code}")
