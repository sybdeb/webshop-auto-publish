# Webshop Product Creator

Efficiënt producten aanmaken vanuit supplier import errors en handmatige invoer.

## Features

### 1. **Quick Create Wizard** 
Snel producten aanmaken via Producten menu:
- EAN barcode + SKU validatie
- Direct leverancier koppelen
- Website categorieën toewijzen
- Duplicate detection

### 2. **Bulk Create vanuit Supplier Errors**
Converteer ontbrekende producten naar echte producten:
- Selecteer meerdere supplier errors
- Preview met duplicate warnings
- Auto-koppel aan leveranciers
- Markeer errors automatisch als resolved

### 3. **Dashboard Tile**
Zie direct hoeveel producten ontbreken:
- Telt unresolved supplier.import.error records
- Click-through naar error lijst
- Integration met webshop_catalog_dashboard

## Gebruik

### Handmatig Product Aanmaken
1. Ga naar **Producten → Nieuw Product (Snel)**
2. Vul EAN, SKU, naam in
3. Optioneel: koppel leverancier
4. Klik "Product Aanmaken"

### Bulk Aanmaken vanuit Errors
1. Ga naar supplier error lijst (via dashboard tile of direct)
2. Selecteer errors met checkbox
3. Klik **Action → Bulk Producten Aanmaken**
4. Controleer preview, deselecteer duplicaten
5. Klik "Producten Aanmaken"

## Technische Details

**Models:**
- `product.quick.create` - TransientModel voor snelle invoer
- `product.bulk.create` - TransientModel voor bulk processing
- `product.bulk.create.line` - Preview lines met duplicate check

**Integrations:**
- `webshop_catalog_dashboard` - Dashboard tile
- `supplier_pricelist_sync` - Error resolution
- `product` - Product creation
- `purchase` - Leverancier koppeling

## License
LGPL-3

## Author
Nerbys - https://nerbys.nl
