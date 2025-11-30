from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    auto_publish = fields.Boolean(
        default=True, 
        string="Automatische publicatie",
        help="Producten in deze categorie worden automatisch gepubliceerd als ze klaar zijn"
    )
    min_supplier_stock = fields.Integer(
        default=5, 
        string="Min. voorraad bij leverancier",
        help="Minimale voorraad die een leverancier moet hebben"
    )
    price_drop_threshold = fields.Float(
        default=15.0, 
        string="Prijsdaling threshold (%)",
        help="Maximale toegestane prijsdaling voordat handmatige controle nodig is"
    )
    require_ean = fields.Boolean(
        default=True,
        string="EAN verplicht",
        help="Producten moeten een EAN/barcode hebben"
    )
    require_brand = fields.Boolean(
        default=False,
        string="Merk verplicht",
        help="Producten moeten een merk hebben (alleen als brand module geïnstalleerd is)"
    )
    require_long_description = fields.Boolean(
        default=True,
        string="Uitgebreide omschrijving verplicht",
        help="Producten moeten een uitgebreide omschrijving hebben"
    )
    require_short_description = fields.Boolean(
        default=True,
        string="Korte omschrijving verplicht",
        help="Producten moeten een korte omschrijving (verkoopomschrijving) hebben"
    )
