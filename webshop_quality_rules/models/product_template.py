from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    need_validation = fields.Boolean(default=True, help="Moet gevalideerd worden door cron")
    is_ready_for_publication = fields.Boolean(compute='_compute_is_ready', store=True, string="Klaar voor publicatie")
    enforce_strictly = fields.Boolean(default=True, string="Streng afdwingen (automatisch offline bij fouten)")
    validation_errors = fields.Text(compute='_compute_is_ready', store=True, string="Validatiefouten")

    @api.depends('image_1920', 'list_price', 'description_sale', 'description', 'barcode', 'categ_id', 'seller_ids', 'categ_id.auto_publish', 'categ_id.min_supplier_stock', 'categ_id.require_ean', 'categ_id.require_brand')
    def _compute_is_ready(self):
        for template in self:
            errors = []
            
            # Regel 1: Hoofdafbeelding
            if not template.image_1920:
                errors.append(_("❌ Mist hoofdafbeelding"))
            
            # Regel 2: Verkoopprijs > 0
            if template.list_price <= 0:
                errors.append(_("❌ Verkoopprijs ≤ 0"))
            
            # Regel 3: Korte omschrijving
            if not template.description_sale:
                errors.append(_("❌ Mist omschrijving (verkoop)"))
            
            # Regel 4: Lange omschrijving
            if not template.description:
                errors.append(_("❌ Mist uitgebreide omschrijving"))
            
            # Regel 5: EAN/barcode (configureerbaar per categorie)
            if template.categ_id.require_ean and not template.barcode:
                errors.append(_("❌ Mist EAN/barcode"))
            
            # Regel 6: Merk (optioneel - alleen als brand_id field bestaat)
            if template.categ_id.require_brand and hasattr(template, 'brand_id') and not template.brand_id:
                errors.append(_("❌ Mist merk"))
            
            # Regel 7: Categorie ≠ All
            if template.categ_id.name == 'All':
                errors.append(_("❌ Staat nog in categorie 'All'"))
            
            # Regel 8: Leverancier met >=X stuks (configureerbaar per categorie)
            min_stock = template.categ_id.min_supplier_stock or 5
            supplier_ok = any(s.product_qty >= min_stock for s in template.seller_ids) if template.seller_ids else False
            if not supplier_ok:
                errors.append(_("❌ Geen leverancier met ≥%d stuks") % min_stock)
            
            # Regel 9: Prijsdaling check (optioneel - implementeer als je historische prijzen hebt)
            if template._has_price_drop_over_threshold():
                errors.append(_("⚠️ Prijsdaling >15% - controle nodig"))

            # Zet resultaten
            template.is_ready_for_publication = len(errors) == 0
            template.validation_errors = "\n".join(errors) if errors else "✅ Alle controles geslaagd"
            
            # Automatisch offline halen bij fouten (als enforce_strictly aan staat)
            if errors and template.enforce_strictly and template.website_published:
                template.website_published = False

    def _has_price_drop_over_threshold(self):
        """
        Controleer of er een prijsdaling is van meer dan threshold%.
        Implementeer dit als je historische prijzen hebt.
        Voor nu: return False (pas aan als je supplier sync hebt).
        """
        self.ensure_one()
        threshold = self.categ_id.price_drop_threshold or 15.0
        # TODO: Implementeer met historische prijzen
        # Voorbeeld: vergelijk self.list_price met vorige prijs uit history
        return False

    @api.model
    def cron_validate_products(self):
        """Cron job: Valideer alleen dirty producten"""
        dirty = self.search([('need_validation', '=', True)])
        _logger = self.env['ir.logging']._logger
        
        if dirty:
            _logger.info(f"Validating {len(dirty)} products...")
            dirty._compute_is_ready()
            dirty.write({'need_validation': False})
            
            # Auto-publish producten die klaar zijn
            ready_to_publish = dirty.filtered(
                lambda p: p.is_ready_for_publication 
                and p.categ_id.auto_publish 
                and not p.website_published
            )
            if ready_to_publish:
                ready_to_publish.write({'website_published': True})
                _logger.info(f"Auto-published {len(ready_to_publish)} products")
            
            # Auto-depublish producten met fouten
            need_depublish = dirty.filtered(
                lambda p: not p.is_ready_for_publication 
                and p.enforce_strictly 
                and p.website_published
            )
            if need_depublish:
                need_depublish.write({'website_published': False})
                _logger.info(f"Auto-depublished {len(need_depublish)} products due to validation errors")

    @api.model_create_multi
    def create(self, vals_list):
        """Mark nieuwe producten als dirty"""
        records = super().create(vals_list)
        records.write({'need_validation': True})
        return records

    def write(self, vals):
        """Mark aangepaste producten als dirty"""
        # Alleen markeren als relevante velden wijzigen
        relevant_fields = {
            'image_1920', 'list_price', 'description_sale', 'description',
            'barcode', 'categ_id', 'seller_ids', 'website_published'
        }
        if any(field in vals for field in relevant_fields):
            vals['need_validation'] = True
        return super().write(vals)
