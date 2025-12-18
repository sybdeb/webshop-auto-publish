# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    # Webshop Auto-Publish Regels
    auto_publish = fields.Boolean(
        string='Auto-Publiceren',
        default=True,
        help='Automatisch publiceren wanneer product aan alle regels voldoet'
    )
    min_supplier_stock = fields.Integer(
        string='Minimale Voorraad Leverancier',
        default=5,
        help='Minimaal aantal stuks op voorraad bij leverancier'
    )
    price_drop_threshold = fields.Float(
        string='Prijsdaling Drempel (%)',
        default=15.0,
        help='Maximale prijsdaling als percentage (bijv. 15 voor 15%)'
    )
    require_ean = fields.Boolean(
        string='Vereist EAN/Barcode',
        default=True,
        help='Product moet een EAN/barcode hebben'
    )
    require_brand = fields.Boolean(
        string='Vereist Merk',
        default=True,
        help='Product moet een merk/brand hebben'
    )
    require_short_description = fields.Boolean(
        string='Vereist Verkoop Notitie',
        default=False,
        help='Product moet een korte verkoop notitie hebben (intern gebruik)'
    )
    require_long_description = fields.Boolean(
        string='Vereist E-commerce Beschrijving',
        default=True,
        help='Product moet een e-commerce/website beschrijving hebben'
    )
