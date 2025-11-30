{
    'name': 'Webshop Auto-Publish (Bundle)',
    'version': '19.0.1.0.0',
    'category': 'Website',
    'summary': 'Bundle: Dashboard + Quality Rules voor automatische webshop publicatie',
    'description': """
Volledige suite voor automatische product-validatie en publicatie.

Installeer deze module om alles in één keer te activeren:
- Webshop Catalog Dashboard: Overzicht van productstatus
- Webshop Quality Rules: Automatische validatie en publicatie

Na installatie vind je het dashboard onder het Webshop Auto-Publish menu.
    """,
    'author': 'Sybdeb',
    'depends': [
        'webshop_catalog_dashboard',
        'webshop_quality_rules',
    ],
    'data': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
