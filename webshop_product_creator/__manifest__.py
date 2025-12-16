{
    'name': 'Webshop Product Creator',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Snel producten aanmaken vanuit supplier errors en dashboard',
    'description': """
Webshop Product Creator
=======================
- Bulk aanmaken van producten vanuit supplier import errors
- Quick create wizard voor handmatige producten
- Dashboard tile voor ontbrekende producten
- Automatische koppeling aan leveranciers
- Duplicate detection (EAN/SKU check)

Integreert met:
- webshop_catalog_dashboard (dashboard tile)
- supplier_pricelist_sync (error resolution)
    """,
    'author': 'Nerbys',
    'website': 'https://nerbys.nl',
    'license': 'LGPL-3',
    'depends': ['purchase', 'product', 'website_sale', 'product_supplier_sync', 'webshop_catalog_dashboard'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_import_job_views.xml',
        'wizard/product_quick_create_views.xml',
        'wizard/product_bulk_create_views.xml',
        'views/dashboard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
