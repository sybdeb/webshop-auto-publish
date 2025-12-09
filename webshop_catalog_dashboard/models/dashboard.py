from odoo import models, fields, api

class CatalogDashboard(models.Model):
    _name = 'catalog.dashboard'
    _description = 'Webshop Catalog Dashboard'

    name = fields.Char(string='Dashboard Name', default='Product Overzicht', readonly=True)
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
            ProductTemplate = self.env['product.template']
            # Check of quality_rules module geïnstalleerd is
            if 'is_ready_for_publication' in ProductTemplate._fields:
                rec.ready_count = ProductTemplate.search_count([
                    ('is_ready_for_publication', '=', True),
                    ('website_published', '=', False),
                    ('public_categ_ids.auto_publish', '=', True)
                ])
            else:
                rec.ready_count = 0

    @api.depends_context('uid')
    def _compute_missing_image(self):
        for rec in self:
            ProductTemplate = self.env['product.template']
            domain = [('image_1920', '=', False), ('active', '=', True)]
            rec.missing_image_count = ProductTemplate.search_count(domain)

    @api.depends_context('uid')
    def _compute_missing_price(self):
        for rec in self:
            ProductTemplate = self.env['product.template']
            domain = [('list_price', '<=', 0), ('active', '=', True)]
            rec.missing_price_count = ProductTemplate.search_count(domain)

    @api.depends_context('uid')
    def _compute_missing_description(self):
        for rec in self:
            ProductTemplate = self.env['product.template']
            domain = ['|', ('description_sale', '=', False), ('description', '=', False), ('active', '=', True)]
            rec.missing_description_count = ProductTemplate.search_count(domain)

    @api.depends_context('uid')
    def _compute_missing_ean(self):
        for rec in self:
            ProductTemplate = self.env['product.template']
            domain = [('barcode', '=', False), ('active', '=', True)]
            rec.missing_ean_count = ProductTemplate.search_count(domain)

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
        domain = []
        if 'is_ready_for_publication' in self.env['product.template']._fields:
            domain.append(('is_ready_for_publication', '=', True))
            domain.append(('website_published', '=', False))
        if 'auto_publish' in self.env['product.public.category']._fields:
            domain.append(('public_categ_ids.auto_publish', '=', True))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Klaar voor publicatie',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': domain,
        }

    def action_view_missing_image(self):
        domain = [('image_1920', '=', False), ('active', '=', True)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder hoofdafbeelding',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': domain,
        }

    def action_view_missing_price(self):
        domain = [('list_price', '<=', 0), ('active', '=', True)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder prijs',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': domain,
        }

    def action_view_missing_description(self):
        domain = ['|', ('description_sale', '=', False), ('description', '=', False), ('active', '=', True)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder omschrijving',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': domain,
        }

    def action_view_missing_ean(self):
        domain = [('barcode', '=', False), ('active', '=', True)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder EAN',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': domain,
        }

    def action_view_missing_brand(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten zonder merk',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': [],
        }

    def action_view_price_drop(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Producten met prijsdaling >15%',
            'res_model': 'product.template',
            'view_mode': 'kanban,form',
            'domain': [],
        }
