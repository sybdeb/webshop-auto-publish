from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'
    
    is_current_supplier = fields.Boolean(
        compute='_compute_is_current_supplier',
        store=True,
        string='Actuele Leverancier',
        help='True als dit product in de laatste import van deze leverancier zat'
    )
    
    @api.depends('last_sync_date', 'partner_id.last_sync_date')
    def _compute_is_current_supplier(self):
        """Check of dit product in de laatste import van deze leverancier zat"""
        for supplier in self:
            if not supplier.last_sync_date or not supplier.partner_id:
                supplier.is_current_supplier = False
                continue
            
            # Haal de laatste sync date van de leverancier (partner)
            partner_last_sync = supplier.partner_id.last_sync_date
            
            if partner_last_sync:
                # Product is actueel als het in de laatste import zat
                # (supplierinfo.last_sync_date == partner.last_sync_date)
                supplier.is_current_supplier = (supplier.last_sync_date == partner_last_sync)
            else:
                # Leverancier heeft nog nooit geïmporteerd
                supplier.is_current_supplier = False
