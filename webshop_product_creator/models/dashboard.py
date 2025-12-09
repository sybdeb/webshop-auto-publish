from odoo import models, fields, api

class CatalogDashboard(models.Model):
    _inherit = 'catalog.dashboard'

    missing_products_count = fields.Integer(
        compute='_compute_missing_products', 
        string='Ontbrekende Producten'
    )

    @api.depends_context('uid')
    def _compute_missing_products(self):
        for rec in self:
            # Check of supplier_pricelist_sync module geïnstalleerd is
            if 'supplier.import.error' in self.env:
                SupplierError = self.env['supplier.import.error']
                rec.missing_products_count = SupplierError.search_count([
                    ('resolved', '=', False),
                    ('error_type', '=', 'product_not_found')
                ])
            else:
                rec.missing_products_count = 0

    def action_view_missing_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Ontbrekende Producten',
            'res_model': 'supplier.import.error',
            'view_mode': 'list,form',
            'domain': [('resolved', '=', False), ('error_type', '=', 'product_not_found')],
            'context': {'create': False},
        }
