from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProductBulkCreate(models.TransientModel):
    _name = 'product.bulk.create'
    _description = 'Bulk Producten Aanmaken vanuit Supplier Errors'

    error_ids = fields.Many2many('supplier.import.error', string='Te Verwerken Errors')
    categ_id = fields.Many2one('product.category', string='Standaard Categorie', required=True)
    public_categ_ids = fields.Many2many('product.public.category', string='Website Categorieën')
    create_supplier_info = fields.Boolean(string='Koppel aan leveranciers', default=True)
    skip_duplicates = fields.Boolean(string='Sla duplicaten over', default=True, 
                                     help='Negeer errors met EAN/SKU die al bestaan')
    batch_size = fields.Integer(string='Batch grootte', default=100,
                                help='Aantal producten per batch (max 500). Voor grote imports: kies 50-100.')
    line_ids = fields.One2many('product.bulk.create.line', 'wizard_id', string='Producten')
    products_created = fields.Integer(string='Producten Aangemaakt', readonly=True, default=0)
    products_skipped = fields.Integer(string='Producten Overgeslagen', readonly=True, default=0)

    @api.model
    def default_get(self, fields_list):
        """Pre-fill wizard met geselecteerde errors"""
        res = super().default_get(fields_list)
        error_ids = self.env.context.get('active_ids', [])
        
        if error_ids:
            errors = self.env['supplier.import.error'].browse(error_ids)
            res['error_ids'] = [(6, 0, error_ids)]
            
            # Maak preview lines
            lines = []
            for error in errors:
                # Check duplicate
                existing = False
                if error.barcode:
                    existing = self.env['product.template'].search([('barcode', '=', error.barcode)], limit=1)
                if not existing and error.product_code:
                    existing = self.env['product.template'].search([('default_code', '=', error.product_code)], limit=1)
                
                lines.append((0, 0, {
                    'error_id': error.id,
                    'barcode': error.barcode,
                    'default_code': error.product_code,
                    'name': error.product_name or 'Nieuw Product',
                    'will_create': not existing,
                    'duplicate_warning': existing.name if existing else False,
                }))
            
            res['line_ids'] = lines
        
        return res

    def action_create_products(self):
        """Bulk aanmaken van producten met batch processing"""
        self.ensure_one()
        
        # Valideer batch_size
        batch_size = min(self.batch_size or 100, 500)
        lines_to_process = self.line_ids.filtered(lambda l: l.will_create)
        total_lines = len(lines_to_process)
        
        if total_lines == 0:
            raise UserError(_('Geen producten geselecteerd om aan te maken.'))
        
        _logger.info('Starting bulk create: %s products in batches of %s', total_lines, batch_size)
        
        created_products = []
        skipped = 0
        batch_count = 0
        
        # Process in batches
        for i in range(0, total_lines, batch_size):
            batch = lines_to_process[i:i + batch_size]
            batch_count += 1
            _logger.info('Processing batch %s/%s (%s products)', batch_count, (total_lines // batch_size) + 1, len(batch))
            
            for line in batch:
            # Skip if user toggled off
            if not line.will_create:
                skipped += 1
                _logger.info('Skipping line %s - will_create is False', line.id)
                continue
            
            try:
                # Check voor duplicates (alleen als skip_duplicates aan staat)
                if self.skip_duplicates:
                    existing = False
                    if line.barcode:
                        existing = self.env['product.template'].search([('barcode', '=', line.barcode)], limit=1)
                    if not existing and line.default_code:
                        existing = self.env['product.template'].search([('default_code', '=', line.default_code)], limit=1)
                    
                    if existing:
                        _logger.info('Skipping duplicate: %s (matches %s)', line.name, existing.name)
                        skipped += 1
                        continue
                
                # Maak product aan
                product_vals = {
                    'name': line.name,
                    'barcode': line.barcode or False,
                    'default_code': line.default_code or False,
                    'categ_id': self.categ_id.id,
                    'public_categ_ids': [(6, 0, self.public_categ_ids.ids)],
                    'type': 'consu',  # Odoo 19: consu = Goods (stockable)
                    'sale_ok': True,
                    'purchase_ok': True,
                    'website_published': False,
                }
                
                product = self.env['product.template'].create(product_vals)
                created_products.append(product.id)
                
                # Maak leverancier info als beschikbaar
                if self.create_supplier_info and line.error_id.history_id:
                    history = line.error_id.history_id
                    if history.partner_id:
                        self.env['product.supplierinfo'].create({
                            'partner_id': history.partner_id.id,
                            'product_tmpl_id': product.id,
                            'min_qty': 1.0,
                        })
                
                # Verwijder error (of markeer als resolved als veld bestaat)
                try:
                    # Probeer eerst resolved=True (als veld bestaat)
                    line.error_id.write({'resolved': True})
                except Exception:
                    # Anders verwijder de error regel
                    line.error_id.unlink()
                
                _logger.info('Created product %s from supplier error %s', product.name, line.error_id.id)
                
            except Exception as e:
                _logger.error('Failed to create product from error %s: %s', line.error_id.id, str(e))
                skipped += 1
            
            # Commit after each batch to avoid timeout
            if (i + len(batch)) % batch_size == 0:
                self.env.cr.commit()
                _logger.info('Batch %s committed (%s products created so far)', batch_count, len(created_products))
        
        # Update counters
        self.write({
            'products_created': len(created_products),
            'products_skipped': skipped,
        })
        
        # Toon resultaat
        if created_products:
            return {
                'type': 'ir.actions.act_window',
                'name': _('%s Producten Aangemaakt') % len(created_products),
                'res_model': 'product.template',
                'view_mode': 'kanban,form',
                'domain': [('id', 'in', created_products)],
                'target': 'current',
            }
        else:
            raise UserError(_('Geen producten aangemaakt. %s overgeslagen.') % skipped)


class ProductBulkCreateLine(models.TransientModel):
    _name = 'product.bulk.create.line'
    _description = 'Bulk Create Line'

    wizard_id = fields.Many2one('product.bulk.create', required=True, ondelete='cascade')
    error_id = fields.Many2one('supplier.import.error', string='Supplier Error', readonly=True)
    barcode = fields.Char(string='EAN')
    default_code = fields.Char(string='SKU')
    name = fields.Char(string='Productnaam', required=True)
    will_create = fields.Boolean(string='Aanmaken?', default=True)
    duplicate_warning = fields.Char(string='Waarschuwing', readonly=True)
