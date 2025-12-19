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
            
            # Als partner.last_sync_date leeg is, gebruik dan de nieuwste supplierinfo sync van deze partner
            if not partner_last_sync:
                all_partner_infos = self.search([('partner_id', '=', supplier.partner_id.id), ('last_sync_date', '!=', False)])
                if all_partner_infos:
                    partner_last_sync = max(all_partner_infos.mapped('last_sync_date'))
                else:
                    supplier.is_current_supplier = True  # Geen sync data beschikbaar, assume current
                    continue
            
            # Product is actueel als het in de laatste import zat
            supplier.is_current_supplier = (supplier.last_sync_date == partner_last_sync)
