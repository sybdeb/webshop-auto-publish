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
        """Pre-fill wizard met geselecteerde errors - OPTIMIZED for large batches"""
        res = super().default_get(fields_list)
        error_ids = self.env.context.get('active_ids', [])
        
        if error_ids:
            # Voor grote batches (>1000): skip preview, create direct
            if len(error_ids) > 1000:
                _logger.info('Large batch detected (%s errors) - skipping preview', len(error_ids))
                res['error_ids'] = [(6, 0, error_ids)]
                # Lege line_ids - lines worden on-the-fly aangemaakt in action_create_products
            else:
                # Voor kleine batches: toon preview met duplicate check
                errors = self.env['supplier.import.error'].browse(error_ids)
                res['error_ids'] = [(6, 0, error_ids)]
                
                # Bulk duplicate check (veel sneller dan per error)
                barcodes = [e.barcode for e in errors if e.barcode]
                codes = [e.product_code for e in errors if e.product_code]
                
                existing_barcodes = {}
                existing_codes = {}
                
                if barcodes:
                    existing_products = self.env['product.template'].search([('barcode', 'in', barcodes)])
                    existing_barcodes = {p.barcode: p.name for p in existing_products}
                
                if codes:
                    existing_products = self.env['product.template'].search([('default_code', 'in', codes)])
                    existing_codes = {p.default_code: p.name for p in existing_products}
                
                # Maak preview lines
                lines = []
                for error in errors:
                    duplicate_warning = False
                    will_create = True
                    
                    # Get product name with fallback
                    product_name = (error.product_name or '').strip()
                    if not product_name:
                        product_name = error.product_code or error.barcode or ''
                        if product_name:
                            product_name = 'Product ' + str(product_name)
                        else:
                            product_name = 'Nieuw Product'
                    
                    if error.barcode and error.barcode in existing_barcodes:
                        duplicate_warning = existing_barcodes[error.barcode]
                        will_create = False
                    elif error.product_code and error.product_code in existing_codes:
                        duplicate_warning = existing_codes[error.product_code]
                        will_create = False
                    
                    lines.append((0, 0, {
                        'error_id': error.id,
                        'barcode': error.barcode,
                        'default_code': error.product_code,
                        'name': product_name,
                        'will_create': will_create,
                        'duplicate_warning': duplicate_warning,
                    }))
                
                res['line_ids'] = lines
        
        return res

    def action_create_products(self):
        """Bulk aanmaken van producten met batch processing - OPTIMIZED"""
        self.ensure_one()
        
        # Valideer batch_size
        batch_size = min(self.batch_size or 100, 500)
        
        # Voor grote batches zonder preview: maak direct aan vanuit errors
        if not self.line_ids and self.error_ids:
            return self._create_from_errors_direct()
        
        lines_to_process = self.line_ids.filtered(lambda l: l.will_create)
        
        lines_to_process = self.line_ids.filtered(lambda l: l.will_create)
        total_lines = len(lines_to_process)
        
        if total_lines == 0:
            raise UserError(_('Geen producten geselecteerd om aan te maken.'))
        
        # Voor grote imports (>5000): maak een job aan voor achtergrond processing
        if total_lines > 5000:
            job = self.env['product.import.job'].create({
                'name': _('Bulk Import - %s producten') % total_lines,
                'error_ids': [(6, 0, [line.error_id.id for line in lines_to_process if line.error_id])],
                'categ_id': self.categ_id.id,
                'public_categ_ids': [(6, 0, self.public_categ_ids.ids)],
                'create_supplier_info': self.create_supplier_info,
                'skip_duplicates': self.skip_duplicates,
                'batch_size': batch_size,
                'state': 'pending',
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Job Aangemaakt'),
                    'message': _('Job met %s producten is aangemaakt en wordt binnen 1 minuut verwerkt. Bekijk de voortgang bij Import Jobs.') % total_lines,
                    'type': 'success',
                    'sticky': False,
                    'next': job.action_view_job(),
                }
            }
        
        # Voor kleinere imports (<5000): direct verwerken
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
                        if history.supplier_id:
                            self.env['product.supplierinfo'].create({
                                'partner_id': history.supplier_id.id,
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
    
    def _create_from_errors_direct(self):
        """Direct aanmaken zonder preview - voor grote batches (>500)"""
        batch_size = min(self.batch_size or 100, 500)
        errors = self.error_ids
        total = len(errors)
        
        # Voor grote imports (>5000): maak een job aan voor achtergrond processing
        if total > 5000:
            job = self.env['product.import.job'].create({
                'name': _('Bulk Import - %s producten') % total,
                'error_ids': [(6, 0, errors.ids)],
                'categ_id': self.categ_id.id,
                'public_categ_ids': [(6, 0, self.public_categ_ids.ids)],
                'create_supplier_info': self.create_supplier_info,
                'skip_duplicates': self.skip_duplicates,
                'batch_size': batch_size,
                'state': 'pending',
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Import Job Aangemaakt'),
                    'message': _('Job met %s producten is aangemaakt en wordt binnen 1 minuut verwerkt. Bekijk de voortgang bij Import Jobs.') % total,
                    'type': 'success',
                    'sticky': False,
                }
            }
        
        _logger.info('DIRECT CREATE: Processing %s errors in batches of %s', total, batch_size)
        
        created_products = []
        skipped = 0
        batch_count = 0
        
        # Disable mail tracking for performance
        context = dict(self.env.context, tracking_disable=True, mail_create_nolog=True)
        
        for i in range(0, total, batch_size):
            batch = errors[i:i + batch_size]
            batch_count += 1
            _logger.info('Processing batch %s/%s (%s errors)', batch_count, (total // batch_size) + 1, len(batch))
            
            # Prepare bulk product vals
            product_vals_list = []
            error_mapping = {}  # track which error belongs to which product
            
            for error in batch:
                # Get product name with fallback to SKU or barcode
                product_name = getattr(error, 'product_name', None) or ''
                product_name = product_name.strip()
                
                if not product_name:
                    # Fallback: use SKU or barcode as name
                    product_name = error.product_code or error.barcode or None
                    if not product_name:
                        skipped += 1
                        continue
                    product_name = 'Product ' + str(product_name)
                
                # Skip duplicates if enabled
                if self.skip_duplicates:
                    if error.barcode and self.env['product.template'].search([('barcode', '=', error.barcode)], limit=1):
                        skipped += 1
                        continue
                    if error.product_code and self.env['product.template'].search([('default_code', '=', error.product_code)], limit=1):
                        skipped += 1
                        continue
                
                vals = {
                    'name': product_name,
                    'barcode': error.barcode or False,
                    'default_code': error.product_code or False,
                    'categ_id': self.categ_id.id,
                    'public_categ_ids': [(6, 0, self.public_categ_ids.ids)],
                    'type': 'consu',
                    'sale_ok': True,
                    'purchase_ok': True,
                    'website_published': False,
                }
                product_vals_list.append(vals)
                error_mapping[len(product_vals_list) - 1] = error
            
            # Bulk create products
            if product_vals_list:
                products = self.env['product.template'].with_context(context).create(product_vals_list)
                created_products.extend(products.ids)
                
                # Cleanup errors - bulk delete is faster
                errors_to_delete = [error_mapping.get(idx) for idx in range(len(products)) if error_mapping.get(idx)]
                if errors_to_delete:
                    try:
                        # Try bulk delete
                        self.env['supplier.import.error'].browse([e.id for e in errors_to_delete]).unlink()
                        _logger.info('Deleted %s error records', len(errors_to_delete))
                    except Exception as e:
                        _logger.error('Failed to delete errors: %s', str(e))
            
            # Commit after batch
            self.env.cr.commit()
            _logger.info('Batch %s COMMITTED: %s products created (total: %s)', batch_count, len(product_vals_list), len(created_products))
        
        # Return result
        _logger.info('COMPLETED: %s products created, %s skipped', len(created_products), skipped)
        
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
