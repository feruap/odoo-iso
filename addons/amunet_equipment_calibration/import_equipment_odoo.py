# import_equipment_odoo.py
from odoo import api, SUPERUSER_ID
import json
import os

def import_data(env):
    json_path = '/mnt/extra-addons/amunet_equipment_calibration/extracted_data.json'
    if not os.path.exists(json_path):
        # Alternative path if run from host context but accessing container files
        json_path = '/tmp/extracted_data.json'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Try to find a suitable location
    location = env['stock.location'].search([('name', 'ilike', 'Control de Calidad')], limit=1)
    if not location:
        # Fallback to any internal location if CC doesn't exist
        location = env['stock.location'].search([('usage', '=', 'internal')], limit=1)
    
    print(f"Using location: {location.name if location else 'None'}")
    
    Equipment = env['amunet.equipment']
    
    for dept, items in data.items():
        print(f"Importing {len(items)} items for {dept}...")
        for item in items:
            # Check if already exists by serial_number (codigo)
            existing = Equipment.search([('serial_number', '=', item['codigo'])], limit=1)
            vals = {
                'name': item['nombre'],
                'brand': item['marca'],
                'model_name': item['modelo'],
                'serial_number': item['codigo'],
                'department': dept,
                'location_id': location.id if location else False,
                'state': 'active'
            }
            if existing:
                existing.write(vals)
                # print(f"Updated: {item['codigo']}")
            else:
                Equipment.create(vals)
                # print(f"Created: {item['codigo']}")

# Run the import
import_data(env)
env.cr.commit()
