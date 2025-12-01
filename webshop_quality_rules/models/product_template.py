from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    need_validation = fields.Boolean(default=True, help="Moet gevalideerd worden door cron")
    is_ready_for_publication = fields.Boolean(compute='_compute_is_ready', store=True, string="Klaar voor publicatie")
    enforce_strictly = fields.Boolean(default=True, string="Streng afdwingen (automatisch offline bij fouten)")
    validation_errors = fields.Text(compute='_compute_is_ready', store=True, string="Validatiefouten")

    @api.depends('image_1920', 'list_price', 'description_sale', 'description', 'barcode', 'public_categ_ids', 'seller_ids', 'public_categ_ids.auto_publish', 'public_categ_ids.min_supplier_stock', 'public_categ_ids.require_ean', 'public_categ_ids.require_brand')
    def _compute_is_ready(self):
        for template in self:
            errors = []
            
            # Haal de strengste regels van alle website categorieën
            categories = template.public_categ_ids
            if not categories:
                errors.append(_("❌ Geen website categorie toegewezen"))
                template.is_ready_for_publication = False
                template.validation_errors = "\n".join(errors)
                continue
            
            # Regel 1: Hoofdafbeelding
            if not template.image_1920:
                errors.append(_("❌ Mist hoofdafbeelding"))
            
            # Regel 2: Verkoopprijs > 0
            if template.list_price <= 0:
                errors.append(_("❌ Verkoopprijs ≤ 0"))
            
            # Regel 3: Korte omschrijving (als minstens 1 categorie het vereist)
            if any(cat.require_short_description for cat in categories) and not template.description_sale:
                errors.append(_("❌ Mist omschrijving (verkoop)"))
            
            # Regel 4: Lange omschrijving (als minstens 1 categorie het vereist)
            if any(cat.require_long_description for cat in categories) and not template.description:
                errors.append(_("❌ Mist uitgebreide omschrijving"))
            
            # Regel 5: EAN/barcode (als minstens 1 categorie het vereist)
            if any(cat.require_ean for cat in categories) and not template.barcode:
                errors.append(_("❌ Mist EAN/barcode"))
            
            # Regel 6: Merk (als minstens 1 categorie het vereist)
            if any(cat.require_brand for cat in categories) and hasattr(template, 'brand_id') and not template.brand_id:
                errors.append(_("❌ Mist merk"))
            
            # Regel 7: Leverancier met >=X stuks (neem hoogste minimum van alle categorieën)
            min_stock = max([cat.min_supplier_stock or 5 for cat in categories])
            supplier_ok = any(s.min_qty >= min_stock for s in template.seller_ids) if template.seller_ids else False
            if not supplier_ok:
                errors.append(_("❌ Geen leverancier met ≥%d stuks") % min_stock)
            
            # Regel 8: Prijsdaling check
            if template._has_price_drop_over_threshold():
                errors.append(_("⚠️ Prijsdaling >15%% - controle nodig"))

            # Zet resultaten
            template.is_ready_for_publication = len(errors) == 0
            template.validation_errors = "\n".join(errors) if errors else "✅ Alle controles geslaagd"

    def _has_price_drop_over_threshold(self):
        """
        Controleer of er een prijsdaling is van meer dan threshold%.
        Implementeer dit als je historische prijzen hebt.
        Voor nu: return False (pas aan als je supplier sync hebt).
        """
        self.ensure_one()
        # Neem laagste threshold van alle categorieën (meest streng)
        if self.public_categ_ids:
            threshold = min([cat.price_drop_threshold or 15.0 for cat in self.public_categ_ids])
        else:
            threshold = 15.0
        # TODO: Implementeer met historische prijzen
        # Voorbeeld: vergelijk self.list_price met vorige prijs uit history
        return False

    @api.model
    def cron_validate_products(self):
        """Cron job: Valideer alleen dirty producten"""
        dirty = self.search([('need_validation', '=', True)])
        
        if dirty:
            _logger.info("Validating %d products...", len(dirty))
            dirty._compute_is_ready()
            dirty.write({'need_validation': False})
            
            # Auto-publish producten die klaar zijn (alle categorieën moeten auto_publish aan hebben)
            ready_to_publish = dirty.filtered(
                lambda p: p.is_ready_for_publication 
                and p.public_categ_ids
                and all(cat.auto_publish for cat in p.public_categ_ids)
                and not p.website_published
            )
            if ready_to_publish:
                ready_to_publish.write({'website_published': True})
                _logger.info("Auto-published %d products", len(ready_to_publish))
            
            # Auto-depublish producten met fouten
            need_depublish = dirty.filtered(
                lambda p: not p.is_ready_for_publication 
                and p.enforce_strictly 
                and p.website_published
            )
            if need_depublish:
                need_depublish.write({'website_published': False})
                _logger.info("Auto-depublished %d products due to validation errors", len(need_depublish))

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
            'barcode', 'public_categ_ids', 'seller_ids', 'website_published'
        }
        if any(field in vals for field in relevant_fields):
            vals['need_validation'] = True
        return super().write(vals)
