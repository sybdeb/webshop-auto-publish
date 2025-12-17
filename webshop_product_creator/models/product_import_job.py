from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)

class ProductImportJob(models.Model):
    _name = 'product.import.job'
    _description = 'Product Import Job Queue'
    _order = 'create_date desc'

    name = fields.Char(string='Job Name', required=True)
    state = fields.Selection([
        ('pending', 'Wachtrij'),
        ('processing', 'Bezig'),
        ('completed', 'Voltooid'),
        ('failed', 'Mislukt'),
    ], default='pending', required=True, string='Status')
    
    error_ids = fields.Many2many('supplier.import.error', string='Te Verwerken Errors')
    error_count = fields.Integer(string='Aantal Errors', compute='_compute_error_count', store=True)
    
    categ_id = fields.Many2one('product.category', string='Standaard Categorie', required=True)
    public_categ_ids = fields.Many2many('product.public.category', string='Website Categorieën')
    create_supplier_info = fields.Boolean(string='Koppel aan leveranciers', default=True)
    skip_duplicates = fields.Boolean(string='Sla duplicaten over', default=True)
    batch_size = fields.Integer(string='Batch grootte', default=100)
    
    products_created = fields.Integer(string='Producten Aangemaakt', readonly=True, default=0)
    products_skipped = fields.Integer(string='Producten Overgeslagen', readonly=True, default=0)
    
    start_date = fields.Datetime(string='Gestart op', readonly=True)
    end_date = fields.Datetime(string='Voltooid op', readonly=True)
    error_message = fields.Text(string='Foutmelding', readonly=True)
    
    progress = fields.Float(string='Voortgang %', compute='_compute_progress')
    user_id = fields.Many2one('res.users', string='Gebruiker', default=lambda self: self.env.user, required=True)

    @api.depends('error_ids')
    def _compute_error_count(self):
        for job in self:
            job.error_count = len(job.error_ids)

    @api.depends('products_created', 'products_skipped', 'error_count')
    def _compute_progress(self):
        for job in self:
            if job.error_count > 0:
                processed = job.products_created + job.products_skipped
                job.progress = (processed / job.error_count) * 100
            else:
                job.progress = 0.0

    def action_process_job(self):
        """Process this job - called by cron"""
        self.ensure_one()
        
        if self.state != 'pending':
            _logger.warning('Job %s is not pending (state=%s), skipping', self.id, self.state)
            return
        
        _logger.info('Starting job %s: processing %s errors', self.id, self.error_count)
        
        self.write({
            'state': 'processing',
            'start_date': fields.Datetime.now(),
        })
        self.env.cr.commit()  # Commit status change
        
        try:
            created_count = 0
            skipped_count = 0
            batch_size = min(self.batch_size or 100, 500)
            
            errors_to_process = self.error_ids.filtered(lambda e: not e.resolved if hasattr(e, 'resolved') else True)
            total_errors = len(errors_to_process)
            
            if total_errors == 0:
                self.write({
                    'state': 'completed',
                    'end_date': fields.Datetime.now(),
                    'error_message': 'Geen errors om te verwerken',
                })
                return
            
            # Process in batches
            for i in range(0, total_errors, batch_size):
                batch = errors_to_process[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (total_errors // batch_size) + 1
                
                _logger.info('Job %s: Processing batch %s/%s (%s errors)', 
                           self.id, batch_num, total_batches, len(batch))
                
                for error in batch:
                    try:
                        # Check for duplicates
                        if self.skip_duplicates:
                            existing = False
                            if error.barcode:
                                existing = self.env['product.template'].search([
                                    ('barcode', '=', error.barcode)
                                ], limit=1)
                            if not existing and error.product_code:
                                existing = self.env['product.template'].search([
                                    ('default_code', '=', error.product_code)
                                ], limit=1)
                            
                            if existing:
                                # Product already exists - resolve/delete the error
                                try:
                                    if hasattr(error, 'resolved'):
                                        error.write({'resolved': True})
                                    else:
                                        error.unlink()
                                except Exception as e:
                                    _logger.warning('Job %s: Failed to resolve duplicate error %s: %s', 
                                                  self.id, error.id, str(e))
                                skipped_count += 1
                                continue
                        
                        # Get product name with fallback
                        product_name = (error.product_name or '').strip()
                        if not product_name:
                            product_name = error.product_code or error.barcode or ''
                            if product_name:
                                product_name = 'Product ' + str(product_name)
                            else:
                                product_name = 'Nieuw Product'
                        
                        # Create product
                        product_vals = {
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
                        
                        product = self.env['product.template'].create(product_vals)
                        created_count += 1
                        
                        # Create supplier info if applicable
                        if self.create_supplier_info and error.history_id:
                            history = error.history_id
                            if history.supplier_id:
                                self.env['product.supplierinfo'].create({
                                    'partner_id': history.supplier_id.id,
                                    'product_tmpl_id': product.id,
                                    'min_qty': 1.0,
                                })
                        
                        # Mark error as resolved or delete
                        try:
                            if hasattr(error, 'resolved'):
                                error.write({'resolved': True})
                                _logger.debug('Job %s: Marked error %s as resolved', self.id, error.id)
                            else:
                                error.unlink()
                                _logger.debug('Job %s: Deleted error %s', self.id, error.id)
                        except Exception as e:
                            _logger.warning('Job %s: Failed to resolve/delete error %s: %s', 
                                          self.id, error.id, str(e))
                        
                    except Exception as e:
                        _logger.error('Job %s: Failed to create product from error %s: %s', 
                                    self.id, error.id, str(e))
                        skipped_count += 1
                
                # Update progress after each batch
                self.write({
                    'products_created': created_count,
                    'products_skipped': skipped_count,
                })
                self.env.cr.commit()
                
                _logger.info('Job %s: Batch %s committed (%s created, %s skipped)', 
                           self.id, batch_num, created_count, skipped_count)
            
            # Job completed
            self.write({
                'state': 'completed',
                'end_date': fields.Datetime.now(),
                'products_created': created_count,
                'products_skipped': skipped_count,
            })
            self.env.cr.commit()
            
            _logger.info('Job %s COMPLETED: %s products created, %s skipped', 
                       self.id, created_count, skipped_count)
            
            # Send notification to user
            self._send_completion_notification()
            
        except Exception as e:
            _logger.error('Job %s FAILED: %s', self.id, str(e))
            self.write({
                'state': 'failed',
                'end_date': fields.Datetime.now(),
                'error_message': str(e),
            })
            self.env.cr.commit()

    def _send_completion_notification(self):
        """Send notification to user when job is complete"""
        self.ensure_one()
        
        message = _(
            '<p>Product import job voltooid:</p>'
            '<ul>'
            '<li>Producten aangemaakt: <strong>%s</strong></li>'
            '<li>Producten overgeslagen: <strong>%s</strong></li>'
            '</ul>'
        ) % (self.products_created, self.products_skipped)
        
        self.env['mail.message'].create({
            'message_type': 'notification',
            'subtype_id': self.env.ref('mail.mt_note').id,
            'body': message,
            'model': self._name,
            'res_id': self.id,
            'partner_ids': [(4, self.user_id.partner_id.id)],
        })

    @api.model
    def cron_process_pending_jobs(self):
        """Cron job to process pending import jobs"""
        # Get max parallel jobs from system parameter (default: 2)
        ICP = self.env['ir.config_parameter'].sudo()
        max_parallel_jobs = int(ICP.get_param('webshop_product_creator.max_parallel_jobs', 2))
        
        # Check if there's already a job being processed
        processing_jobs = self.search([('state', '=', 'processing')])
        
        # Check for stuck jobs (processing for more than 1 hour)
        if processing_jobs:
            from datetime import datetime, timedelta
            one_hour_ago = fields.Datetime.now() - timedelta(hours=1)
            stuck_jobs = processing_jobs.filtered(lambda j: j.start_date and j.start_date < one_hour_ago)
            
            if stuck_jobs:
                _logger.warning('Cron: Found %s stuck job(s) (running >1h), marking as failed: %s', 
                              len(stuck_jobs), stuck_jobs.ids)
                for job in stuck_jobs:
                    job.write({
                        'state': 'failed',
                        'end_date': fields.Datetime.now(),
                        'error_message': 'Job timeout: Processing took longer than 1 hour'
                    })
                # Refresh processing_jobs list
                processing_jobs = self.search([('state', '=', 'processing')])
        
        if len(processing_jobs) >= max_parallel_jobs:
            _logger.info('Cron: %s jobs already processing (max: %s), waiting... Job IDs: %s', 
                        len(processing_jobs), max_parallel_jobs, processing_jobs.ids)
            return
        
        # Process multiple pending jobs (up to max_parallel_jobs)
        jobs_to_start = max_parallel_jobs - len(processing_jobs)
        pending_jobs = self.search([('state', '=', 'pending')], limit=jobs_to_start, order='create_date asc')
        
        if pending_jobs:
            _logger.info('Cron: Found %s pending job(s), starting processing', len(pending_jobs))
            for job in pending_jobs:
                # Process directly in new thread-like fashion using env
                job.action_process_job()
        else:
            _logger.debug('Cron: No pending jobs found')

    def action_view_job(self):
        """Open the job in form view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import Job'),
            'res_model': 'product.import.job',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
