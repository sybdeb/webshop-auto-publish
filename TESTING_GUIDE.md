# ✅ TEST CHECKLIST - Webshop Auto-Publish

## Pre-installatie Check

### 1. Odoo Versie Check
- [ ] Odoo 18.0 of 19.0 draait
- [ ] Database backup gemaakt
- [ ] Addons path geconfigureerd

### 2. Dependencies Check
```bash
# Controleer of deze modules geïnstalleerd zijn:
- website_sale (komt standaard met Odoo)
- purchase (komt standaard met Odoo)  
- product (komt standaard met Odoo)
```

---

## Installatie Procedure

### Stap 1: Clone/Copy Repository
```bash
cd /pad/naar/odoo/addons
git clone https://github.com/sybdeb/webshop_auto_publish.git
# OF: kopieer de folder handmatig
```

### Stap 2: Restart Odoo Server
```bash
# Stop Odoo
sudo systemctl stop odoo
# OF via process manager

# Start Odoo
sudo systemctl start odoo
# Check logs:
tail -f /var/log/odoo/odoo-server.log
```

### Stap 3: Update Apps List
1. Log in als Administrator
2. Ga naar: **Apps** (developer mode moet AAN zijn)
3. Klik: **Update Apps List**
4. Bevestig

### Stap 4: Installeer Modules (in deze volgorde!)

#### A. Installeer eerst: `Webshop Quality Rules`
- Zoek: "Webshop Quality Rules"
- Klik: **Activate/Install**
- Wacht tot installatie compleet

#### B. Installeer daarna: `Webshop Catalog Dashboard`  
- Zoek: "Webshop Catalog Dashboard"
- Klik: **Activate/Install**
- Wacht tot installatie compleet

#### C. (Optioneel) Installeer: `Webshop Auto-Publish (Bundle)`
- Dit installeert automatisch beide bovenstaande modules
- Handig voor nieuwe installaties

---

## Functionaliteit Testen

### TEST 1: Dashboard Toegang ✅
1. Klik op menu icoon (≡) links bovenin
2. Zoek: **"Webshop Auto-Publish"** menu item
3. Klik erop → Dashboard moet openen
4. Je ziet 6 tegels met cijfers

**Verwacht resultaat**: 
- Dashboard opent zonder errors
- Tegels tonen cijfers (kunnen 0 zijn)

**Troubleshoot**:
- Menu niet zichtbaar? → Check of module geïnstalleerd is
- Error 404? → Restart Odoo server
- Lege pagina? → Check browser console (F12)

---

### TEST 2: Product Validatie Tab ✅
1. Ga naar: **Verkoop → Producten → Producten**
2. Open een willekeurig product
3. Ga naar tab: **"Webshop Validatie"**
4. Je ziet:
   - ✅ "Klaar voor publicatie" (checkbox)
   - ⚙️ "Streng afdwingen" (checkbox)
   - 📝 "Validatieresultaten" (tekstblok met emoji's)

**Verwacht resultaat**:
- Tab is zichtbaar
- Velden zijn readonly (is_ready_for_publication)
- Validatieresultaten tonen errors/success

**Troubleshoot**:
- Tab niet zichtbaar? → Check of quality_rules geïnstalleerd is
- Fields leeg? → Trigger recompute: wijzig product prijs en save

---

### TEST 3: Categorie Configuratie ✅
1. Ga naar: **Voorraad → Configuratie → Productcategorieën**
2. Open categorie "All" of maak nieuwe aan
3. Ga naar tab: **"Webshop Regels"**
4. Je ziet instellingen:
   - ☑️ Automatische publicatie
   - 📦 Min. voorraad bij leverancier (default: 5)
   - 📉 Prijsdaling threshold (default: 15%)
   - ☑️ EAN verplicht
   - ☑️ Merk verplicht (optioneel)

**Verwacht resultaat**:
- Tab "Webshop Regels" bestaat
- Alle velden zijn editeerbaar
- Defaults zijn ingesteld

**Test**: 
- Zet "Automatische publicatie" UIT
- Save
- Check of cron deze producten skipt

---

### TEST 4: Dashboard Tegels Klikken ✅
1. Open Dashboard: **Webshop Auto-Publish** menu
2. Klik op tegel: **"Mist hoofdafbeelding"**

**Verwacht resultaat**:
- Nieuwe window opent
- Toon list view van producten zonder foto
- Je kan producten openen/bewerken

**Test alle 6 tegels**:
- [ ] Klaar voor publicatie
- [ ] Mist hoofdafbeelding  
- [ ] Mist verkoopprijs
- [ ] Mist omschrijving
- [ ] Mist EAN
- [ ] Prijsdaling >15% (kan leeg zijn)

---

### TEST 5: Automatische Validatie (Cron) ✅

#### Handmatige Cron Test:
1. Maak een nieuw product aan:
   - Naam: "TEST Product"
   - GEEN foto
   - GEEN prijs ingevuld (of 0)
   - GEEN omschrijving
2. Save product
3. Check product tab "Webshop Validatie"
   - Moet errors tonen: ❌ Mist hoofdafbeelding, etc.
4. Trigger cron handmatig:
   - Ga naar: **Instellingen → Technisch → Automation → Geplande acties**
   - Zoek: "Webshop: Valideer producten voor publicatie"
   - Klik: **"Voer nu uit"** (Run Manually)
5. Refresh product → Check of status updated is

**Verwacht resultaat**:
- Cron draait zonder errors
- Product krijgt validation_errors tekst
- is_ready_for_publication = False
- Dashboard cijfers updaten

#### Automatische Cron Test:
1. Wacht 15 minuten (cron interval)
2. Maak ondertussen 2-3 test producten
3. Na 15 min: Check of ze automatisch gevalideerd zijn
4. Check Odoo logs: `grep "Validating" /var/log/odoo/odoo-server.log`

**Verwacht in logs**:
```
INFO webshop_quality_rules.models.product_template: Validating 3 products...
INFO webshop_quality_rules.models.product_template: Auto-published 0 products
INFO webshop_quality_rules.models.product_template: Auto-depublished 2 products due to validation errors
```

---

### TEST 6: Auto-Publish Flow ✅

**Scenario**: Product moet automatisch online komen als alle regels OK zijn

1. Maak nieuw product:
   - Naam: "Auto-Publish Test"
   - Foto: Upload een afbeelding
   - Prijs: €99.99
   - Korte omschrijving: "Test product"
   - Uitgebreide omschrijving: "Lange tekst hier"
   - EAN: 1234567890123
   - Categorie: Kies een (niet "All")
   - Leverancier: Voeg toe met voorraad ≥ 5 stuks
   
2. Save product
3. Check tab "Webshop Validatie":
   - Moet tonen: ✅ Alle controles geslaagd
   - is_ready_for_publication = TRUE
   
4. Zorg dat categorie "Automatische publicatie" = AAN staat
5. Trigger cron (handmatig of wacht 15 min)
6. Check product:
   - **Website gepubliceerd** checkbox moet AAN staan!

**Verwacht resultaat**:
- Product wordt automatisch online gezet
- Zichtbaar op frontend (/shop)

---

### TEST 7: Auto-Depublish Flow ✅

**Scenario**: Gepubliceerd product moet offline als het errors krijgt

1. Open het auto-published product van TEST 6
2. Verwijder de hoofdafbeelding
3. Save
4. Check "Streng afdwingen" = AAN
5. Trigger cron
6. Refresh product:
   - **Website gepubliceerd** moet nu UIT staan!
   - validation_errors toont: ❌ Mist hoofdafbeelding

**Verwacht resultaat**:
- Product wordt automatisch offline gehaald
- Niet meer zichtbaar op /shop

---

### TEST 8: Performance (Grote Database) ✅

**Als je >1000 producten hebt**:

1. Check cron execution time:
   ```python
   # In Odoo shell:
   import time
   start = time.time()
   env['product.template'].cron_validate_products()
   print(f"Time: {time.time() - start} sec")
   ```

**Verwacht**:
- <5 seconden voor 1000 producten
- <30 seconden voor 10.000 producten

**Optimalisatie** (als te traag):
- Verhoog cron interval naar 30 min
- Limiteer dirty products: `search(..., limit=500)`

---

### TEST 9: Multi-Company (Optioneel) ✅

**Als je meerdere bedrijven hebt**:

1. Switch naar Company 2
2. Open Dashboard
3. Check of cijfers alleen producten van Company 2 tonen

**Verwacht**:
- Dashboard filtert op current company
- Validatie respecteert company

---

### TEST 10: Upgrades & Updates ✅

**Test dat updates werken**:

1. Maak kleine wijziging in code (bijv. verhoog versie)
2. Restart Odoo
3. Ga naar Apps → Webshop modules
4. Klik: **Upgrade** 
5. Check of alles nog werkt

**Verwacht**:
- Geen data loss
- Geen errors tijdens upgrade
- Alle features werken nog

---

## 🐛 Common Issues & Fixes

### Issue 1: "Module not found"
**Fix**: 
```bash
# Check addons path
grep addons_path /etc/odoo/odoo.conf
# Restart Odoo
sudo systemctl restart odoo
```

### Issue 2: "Field 'is_ready_for_publication' does not exist"
**Fix**:
- Uninstall dashboard module
- Install quality_rules first
- Then install dashboard

### Issue 3: Dashboard tegels tonen allemaal "0"
**Check**:
- Heb je producten in database?
- Staat "Automatische publicatie" AAN bij categorieën?
- Run cron handmatig

### Issue 4: Cron draait niet
**Fix**:
```bash
# Check of Odoo cron worker draait
ps aux | grep odoo | grep cron
# Enable workers in config:
workers = 2
```

### Issue 5: "Access Denied" errors
**Fix**:
- Check of user in juiste groep zit (Sales Manager)
- Check security/ir.model.access.csv
- Update apps list

### Issue 6: Dashboard knoppen werken niet
**Fix**:
- Dit was een bug, is gefixed in laatste commit
- Pull laatste versie: `git pull origin main`

---

## ✅ Final Checklist

- [ ] Alle 10 tests passed
- [ ] Geen errors in Odoo logs
- [ ] Dashboard cijfers kloppen
- [ ] Auto-publish werkt
- [ ] Auto-depublish werkt  
- [ ] Cron draait elke 15 min
- [ ] Performance is OK (<30 sec)

---

## 🚀 Production Ready?

**JA** als:
- ✅ Alle tests zijn groen
- ✅ Geen errors in logs (24 uur monitoren)
- ✅ Backup strategie staat
- ✅ Je weet hoe te troubleshooten

**NEE** als:
- ❌ Nog errors in logs
- ❌ Performance issues
- ❌ Features werken niet consistent

---

## 📞 Support

**Odoo version incompatibility?**
→ Check `/webshop_quality_rules/models/product_template.py` line 5 voor logger import

**Dashboard leeg?**  
→ Check of quality_rules module installed is first

**Cron draait niet?**
→ Enable workers in odoo.conf (`workers = 2`)

**Vragen?**
→ Open GitHub issue of check FREEMIUM_GUIDE.md voor commerciële support opties

---

🎉 **Success!** Je module is production-ready voor Odoo 18 & 19!
