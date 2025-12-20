{
    'name': 'Webshop Quality Rules',
    'version': '19.0.2.0.0',
    'category': 'Website',
    'summary': 'Configureerbare validatieregels voor producten',
    'description': """
Standaardregels: foto, prijs, omschrijving, EAN, merk, leverancier >=5 stuks, prijsdaling 15%.
    """,
    'author': 'Sybdeb',
    'depends': ['website_sale', 'purchase', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/product_category_views.xml',
        'views/product_public_category_views.xml',
        'data/cron.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'OPL-1',  # Proprietary - Paid version (€49/month)
}
