# Webshop Auto-Publish
Odoo 18/19 module voor automatische product-validatie en publicatie op de webshop.

## 🚀 Quick Start
**Nieuw hier?** → Lees **[QUICKSTART.md](QUICKSTART.md)** voor installatie in 15 minuten!

## Installatie
1. Clone deze repo in je addons-map.
2. Restart Odoo server.
3. Update apps list in Odoo (Settings → Apps → Update Apps List).
4. Installeer: **Webshop Auto-Publish (Bundle)** - installeert alles automatisch.

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

## 📚 Documentatie

- **[QUICKSTART.md](QUICKSTART.md)** - Installatie & eerste test in 15 min
- **[TESTING_GUIDE.md](TESTING_GUIDE.md)** - Uitgebreide test procedures (10 tests)
- **[FREEMIUM_GUIDE.md](FREEMIUM_GUIDE.md)** - Hoe geld verdienen met deze module
- **[GIT_SETUP.md](GIT_SETUP.md)** - GitHub repository setup

## 🐛 Troubleshooting

Problemen? Check eerst:
1. Odoo versie 18.0 of 19.0?
2. Developer mode ingeschakeld?
3. Workers enabled in odoo.conf? (`workers = 2`)
4. Alle dependencies geïnstalleerd?

## Auteur
Sybdeb

## Versie
1.0.0 - Compatible met Odoo 18.0 en 19.0
