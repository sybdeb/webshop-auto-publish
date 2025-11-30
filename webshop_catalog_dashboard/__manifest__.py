{
    'name': 'Webshop Catalog Dashboard',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Dashboard voor webshop product-validatie',
    'description': """
Klikbaar dashboard met tegels voor producten die wachten op publicatie.
    """,
    'author': 'Sybdeb',
    'depends': ['website_sale', 'webshop_quality_rules'],
    'data': [
        'views/dashboard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
