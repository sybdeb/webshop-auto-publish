from odoo import models, fields, api

class CatalogDashboard(models.TransientModel):
    _name = 'catalog.dashboard'
    _description = 'Webshop Catalog Dashboard'

    ready_count = fields.Integer(compute='_compute_ready_count', string='Klaar voor publicatie')
    missing_image_count = fields.Integer(compute='_compute_missing_image', string='Mist hoofdafbeelding')
    missing_price_count = fields.Integer(compute='_compute_missing_price', string='Mist verkoopprijs')
    missing_description_count = fields.Integer(compute='_compute_missing_description', string='Mist omschrijving')
    missing_ean_count = fields.Integer(compute='_compute_missing_ean', string='Mist EAN')
    missing_brand_count = fields.Integer(compute='_compute_missing_brand', string='Mist merk')
    price_drop_count = fields.Integer(compute='_compute_price_drop', string='Prijsdaling >15%')

    @api.depends_context('uid')
    def _compute_ready_count(self):
        for rec in self:
            rec.ready_count = self.env['product.template'].search_count([
                ('is_ready_for_publication', '=', True),
                ('website_published', '=', False),
                ('categ_id.auto_publish', '=', True)
            ])

    @api.depends_context('uid')
    def _compute_missing_image(self):
        for rec in self:
            rec.missing_image_count = self.env['product.template'].search_count([
                ('image_1920', '=', False),
                ('categ_id.auto_publish', '=', True)
            ])

    @api.depends_context('uid')
    def _compute_missing_price(self):
        for rec in self:
            rec.missing_price_count = self.env['product.template'].search_count([
                ('list_price', '<=', 0),
                ('categ_id.auto_publish', '=', True)
            ])

    @api.depends_context('uid')
    def _compute_missing_description(self):
        for rec in self:
            rec.missing_description_count = self.env['product.template'].search_count([
                '|',
                ('description_sale', '=', False),
                ('description', '=', False),
                ('categ_id.auto_publish', '=', True)
            ])

    @api.depends_context('uid')
    def _compute_missing_ean(self):
        for rec in self:
            rec.missing_ean_count = self.env['product.template'].search_count([
                ('barcode', '=', False),
                ('categ_id.auto_publish', '=', True)
            ])

    @api.depends_context('uid')
    def _compute_missing_brand(self):
        for rec in self:
            # Pas aan als je een brand_id field hebt
            rec.missing_brand_count = 0

    @api.depends_context('uid')
    def _compute_price_drop(self):
        for rec in self:
            # Tel producten met prijsdaling >15%
            rec.price_drop_count = 0

    def action_view_ready_products(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Klaar voor publicatie',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('is_ready_for_publication', '=', True),
                ('website_published', '=', False),
                ('categ_id.auto_publish', '=', True)
            ],
        }

    def action_view_missing_image(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder hoofdafbeelding',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('image_1920', '=', False),
                ('categ_id.auto_publish', '=', True)
            ],
        }

    def action_view_missing_price(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder prijs',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('list_price', '<=', 0),
                ('categ_id.auto_publish', '=', True)
            ],
        }

    def action_view_missing_description(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder omschrijving',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [
                '|',
                ('description_sale', '=', False),
                ('description', '=', False),
                ('categ_id.auto_publish', '=', True)
            ],
        }

    def action_view_missing_ean(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder EAN',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [
                ('barcode', '=', False),
                ('categ_id.auto_publish', '=', True)
            ],
        }

    def action_view_missing_brand(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder merk',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [],
        }

    def action_view_price_drop(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten met prijsdaling >15%',
            'res_model': 'product.template',
            'view_mode': 'kanban,tree,form',
            'domain': [],
        }
