# Webshop Auto-Publish
Odoo 19 module voor automatische product-validatie en publicatie op de webshop.

## Installatie
1. Clone deze repo in je addons-map.
2. Update apps list in Odoo.
3. Installeer: webshop_catalog_dashboard, webshop_quality_rules, webshop_auto_publish.

## Features
- Klikbaar dashboard met tegels voor issues.
- Automatische validatie & publicatie.
- Configureerbare regels per categorie.

## Dependencies
- website_sale
- purchase
- product

## Modules

### webshop_catalog_dashboard
Dashboard met klikbare tegels voor producten die wachten op publicatie. Toont overzicht van:
- Producten klaar voor publicatie
- Producten zonder hoofdafbeelding
- Producten zonder prijs
- En meer...

### webshop_quality_rules
Validatieregels voor producten met standaard checks:
- Hoofdafbeelding aanwezig
- Verkoopprijs > 0
- Korte en lange omschrijving
- EAN/barcode
- Merk ingesteld
- Categorie ≠ "All"
- Leverancier met minimaal 5 stuks voorraad
- Prijsdaling max 15%

### webshop_auto_publish
Bundle module die beide modules combineert voor eenvoudige installatie.

## Configuratie
Per categorie kunnen regels worden aangepast via:
`Voorraad → Configuratie → Productcategorieën → Tab "Webshop Regels"`

## Cron Job
Draait elke 15 minuten en valideert producten die gemarkeerd zijn voor controle.

## Auteur
Sybdeb
