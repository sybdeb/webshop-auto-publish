from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    is_current_supplier = fields.Boolean(
        compute='_compute_is_current_supplier',
        store=True,
        string='Actuele Leverancier',
        help='True als deze leverancier de meest recente sync heeft voor dit product'
    )
    
    @api.depends('last_sync_date', 'product_tmpl_id.seller_ids.last_sync_date')
    def _compute_is_current_supplier(self):
        """Check of deze leverancier de meest recente sync heeft"""
        for supplier in self:
            if not supplier.product_tmpl_id or not supplier.last_sync_date:
                supplier.is_current_supplier = False
                continue
            
            # Vind de meest recente sync date van alle leveranciers voor dit product
            all_suppliers = supplier.product_tmpl_id.seller_ids
            max_sync_date = max([s.last_sync_date for s in all_suppliers if s.last_sync_date], default=None)
            
            if max_sync_date:
                # Deze leverancier is actueel als zijn sync date gelijk is aan de max
                supplier.is_current_supplier = (supplier.last_sync_date == max_sync_date)
            else:
                supplier.is_current_supplier = False
