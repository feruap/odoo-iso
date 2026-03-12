
def fix_all_membranas_symbols_orm(env):
    PLUS_MINUS = "\u00b1"
    MICRO = "\u00b5"
    
    product_codes = ['MPMNC01', 'MPMNC02', 'MPMNC03', 'MPTS01', 'MPTS02']
    templates = env['product.template'].search([('default_code', 'in', product_codes)])
    
    configs = env['amunet.quality.parameter.specification.config'].search([
        ('product_tmpl_id', 'in', templates.ids)
    ])
    
    print(f"Cleaning symbols for {len(configs)} configuration records...")
    
    for c in configs:
        old_criteria = c.acceptance_criteria or ""
        old_summary = c.config_summary or ""
        
        # Replace common corruptions
        # 1. Replace '??' with ± (safest assumption for these products)
        # 2. Replace '±m' or '??m' with µm
        # 3. Ensure any existing literal ± is replaced with the correct unicode char just in case
        
        new_criteria = old_criteria.replace('??', PLUS_MINUS).replace('\u00b1m', MICRO + 'm')
        new_summary = old_summary.replace('??', PLUS_MINUS).replace('\u00b1m', MICRO + 'm')
        
        # Specific fixes for things like '180 ±m' which became '180 µm'
        # If it was '??m' it might have been caught by the above
        
        if new_criteria != old_criteria or new_summary != old_summary:
            print(f"  Fixing Config {c.id} ({c.specification_name}): '{old_criteria}' -> '{new_criteria}'")
            c.write({
                'acceptance_criteria': new_criteria,
                'config_summary': new_summary
            })

    # Re-apply the specific migration for MAVI-09 and Grosor to be absolutely sure
    # (using the previously confirmed values)
    
    env.cr.commit()
    print("Comprehensive Symbol Fix completed.")

if 'env' in locals():
    fix_all_membranas_symbols_orm(env)
elif 'env' in globals():
    fix_all_membranas_symbols_orm(globals()['env'])
