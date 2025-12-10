from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductQuickCreate(models.TransientModel):
    _name = 'product.quick.create'
    _description = 'Snel Product Aanmaken'

    barcode = fields.Char(string='EAN Barcode', required=True)
    default_code = fields.Char(string='SKU/Artikelcode')
    name = fields.Char(string='Productnaam', required=True)
    list_price = fields.Float(string='Verkoopprijs', default=0.0)
    categ_id = fields.Many2one('product.category', string='Product Categorie', required=True)
    public_categ_ids = fields.Many2many('product.public.category', string='Website Categorieën')
    description_sale = fields.Text(string='Korte Omschrijving')
    create_supplier_info = fields.Boolean(string='Koppel aan leverancier', default=False)
    partner_id = fields.Many2one('res.partner', string='Leverancier', domain=[('supplier_rank', '>', 0)])
    supplier_price = fields.Float(string='Inkoopprijs')
    min_qty = fields.Float(string='Minimum Bestelhoeveelheid', default=1.0)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Check of product al bestaat"""
        if self.barcode:
            existing = self.env['product.template'].search([('barcode', '=', self.barcode)], limit=1)
            if existing:
                return {
                    'warning': {
                        'title': _('Product bestaat al'),
                        'message': _('Er bestaat al een product met EAN %s: %s') % (self.barcode, existing.name)
                    }
                }

    @api.onchange('default_code')
    def _onchange_default_code(self):
        """Check of SKU al bestaat"""
        if self.default_code:
            existing = self.env['product.template'].search([('default_code', '=', self.default_code)], limit=1)
            if existing:
                return {
                    'warning': {
                        'title': _('SKU bestaat al'),
                        'message': _('Er bestaat al een product met SKU %s: %s') % (self.default_code, existing.name)
                    }
                }

    def action_create_product(self):
        """Maak product aan en optioneel leverancier info"""
        self.ensure_one()
        
        # Check duplicates
        if self.env['product.template'].search([('barcode', '=', self.barcode)], limit=1):
            raise ValidationError(_('Product met EAN %s bestaat al!') % self.barcode)
        
        # Maak product aan
        product_vals = {
            'name': self.name,
            'barcode': self.barcode,
            'default_code': self.default_code,
            'list_price': self.list_price,
            'categ_id': self.categ_id.id,
            'public_categ_ids': [(6, 0, self.public_categ_ids.ids)],
            'description_sale': self.description_sale,
            'type': 'consu',  # Odoo 19: consu = Goods (stockable)
            'sale_ok': True,
            'purchase_ok': True,
            'website_published': False,  # Draft state
        }
        
        product = self.env['product.template'].create(product_vals)
        
        # Maak leverancier info aan
        if self.create_supplier_info and self.partner_id:
            self.env['product.supplierinfo'].create({
                'partner_id': self.partner_id.id,
                'product_tmpl_id': product.id,
                'price': self.supplier_price,
                'min_qty': self.min_qty,
            })
        
        # Open het nieuwe product
        return {
            'type': 'ir.actions.act_window',
            'name': _('Nieuw Product'),
            'res_model': 'product.template',
            'res_id': product.id,
            'view_mode': 'form',
            'target': 'current',
        }
