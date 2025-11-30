# 🧪 QUICK START - Test in 15 Minuten

## Snelle Installatie Test

### Stap 1: Kopieer naar Odoo (2 min)
```bash
# Kopieer hele folder naar je Odoo addons
cp -r /c/Users/Sybde/Projects/webshop_auto_publish /pad/naar/odoo/addons/

# OF maak symlink (beter voor development)
ln -s /c/Users/Sybde/Projects/webshop_auto_publish /pad/naar/odoo/addons/webshop_auto_publish
```

### Stap 2: Restart Odoo (1 min)
```bash
# Windows (als service):
# Services → Odoo → Restart

# Linux:
sudo systemctl restart odoo

# Docker:
docker restart odoo

# Development mode:
# Stop running odoo (Ctrl+C)
# Start weer: python3 odoo-bin -c odoo.conf
```

### Stap 3: Update Apps List (1 min)
1. Login als **Administrator**
2. **Settings → Activate Developer Mode** (rechtsonder)
3. **Apps** menu
4. Klik op de 3 stipjes (⋮) → **Update Apps List**
5. Klik **Update**

### Stap 4: Installeer Module (2 min)
1. Nog steeds in **Apps**
2. Verwijder filter "Apps" (zodat je ook modules ziet)
3. Zoek: **"webshop"**
4. Je zou moeten zien:
   - ✅ Webshop Quality Rules
   - ✅ Webshop Catalog Dashboard  
   - ✅ Webshop Auto-Publish (Bundle)

5. Klik **Activate** op: **Webshop Auto-Publish (Bundle)**
   - Dit installeert automatisch alles

⏱️ Installatie duurt ~30 seconden

### Stap 5: Eerste Test (5 min)

#### Test A: Dashboard Openen
1. Klik op het **≡** menu icoon (links bovenaan)
2. Zoek naar: **"Webshop Auto-Publish"**
3. Klik erop

**✅ Success als**: Dashboard opent met 6 tegels (cijfers kunnen 0 zijn)
**❌ Error als**: "Model not found" → Herinstalleer module

#### Test B: Maak Test Product
1. Ga naar: **Sales → Products → Products**
2. Klik **Create**
3. Vul in:
   - Name: **TEST Product**
   - Sales Price: **€0.00** (laat op 0!)
   - GEEN foto uploaden
4. Klik **Save**

5. Ga naar tab: **Webshop Validatie**

**✅ Success als**: 
```
Je ziet:
❌ Mist hoofdafbeelding
❌ Verkoopprijs ≤ 0
❌ Mist omschrijving (verkoop)
❌ Mist uitgebreide omschrijving
❌ Mist EAN/barcode
... etc
```

**❌ Error als**: Tab "Webshop Validatie" bestaat niet
→ Quality Rules module niet geïnstalleerd, installeer apart

#### Test C: Fix Product & Auto-Publish
1. Nog steeds in je TEST product
2. Upload een foto (kan een screenshot zijn)
3. Zet Sales Price op: **€99.99**
4. Vul in bij Sales tab:
   - **Sales Description**: "Test product voor validatie"
5. Vul in bij Notes tab:
   - **Notes**: "Uitgebreide omschrijving hier"
6. Vul in bij General Info tab (extra velden tonen):
   - **Barcode**: 1234567890123
7. Wijzig **Product Category** van "All" naar iets anders (bijv. "All / Saleable")

8. **Save**

9. Check tab **Webshop Validatie** opnieuw

**✅ Success als**:
```
✅ Alle controles geslaagd
☑️ Klaar voor publicatie: AAN
```

10. Nu **trigger de cron handmatig**:
    - Ga naar: **Settings → Technical → Automation → Scheduled Actions**
    - Zoek: **"Webshop: Valideer producten voor publicatie"**
    - Klik op de regel
    - Klik **Run Manually** knop

11. Ga terug naar je product en **refresh pagina** (F5)

12. Check **Website** tab:

**✅ Success als**: 
- **Website Published** checkbox is nu AAN! 🎉
- Product is zichtbaar op /shop (als je website hebt)

#### Test D: Dashboard Cijfers
1. Ga terug naar **Dashboard** (Webshop Auto-Publish menu)
2. Klik op tegel: **"Klaar voor publicatie"**

**✅ Success als**: 
- Er opent een lijst
- Je TEST product staat er NIET in (want net gepubliceerd)

3. Maak nóg een product aan maar met fouten (geen foto, geen prijs)
4. Ga terug naar Dashboard
5. Klik op: **"Mist hoofdafbeelding"**

**✅ Success als**:
- Lijst opent
- Je nieuwe (foute) product staat erin

---

## 🚨 Troubleshooting

### Error: "Module not found"
```bash
# Check of folder in juiste plaats staat:
ls -la /pad/naar/odoo/addons/ | grep webshop

# Moet tonen:
# webshop_auto_publish/
```

### Error: "No module named 'webshop_quality_rules'"
→ Je hebt circulaire dependency van oude versie
→ Doe `git pull` voor laatste fixes

### Dashboard cijfers blijven 0
**Check 1**: Heb je producten?
→ Maak test producten aan zoals hierboven

**Check 2**: Staat "Automatische publicatie" AAN?
1. Ga naar: **Inventory → Configuration → Product Categories**
2. Open "All" categorie
3. Tab: **Webshop Regels**
4. Zet **Automatische publicatie** op AAN
5. Save

**Check 3**: Draai cron opnieuw

### Cron draait niet automatisch
**Fix**: Enable workers in odoo.conf
```ini
[options]
workers = 2
max_cron_threads = 1
```
Restart Odoo daarna.

### "Access Denied" bij Dashboard
**Fix**: Geef jezelf Sales Manager rechten:
1. **Settings → Users → Manage Users**
2. Klik op jouw gebruiker
3. Tab **Access Rights**
4. Zet **Sales → Administrator** AAN
5. Save

---

## ✅ Als Alles Werkt...

### Je bent klaar voor productie als:
- ✅ Dashboard opent zonder errors
- ✅ Product validatie werkt (tab "Webshop Validatie")
- ✅ Auto-publish werkt (na cron run)
- ✅ Dashboard tegels zijn klikbaar
- ✅ Cijfers in tegels kloppen

### Volgende stap:
1. **Test met echte producten** (niet test data)
2. **Monitor 24 uur** - check Odoo logs voor errors
3. **Train je team** - laat ze dashboard zien
4. **Configureer categorieën** - stel regels in per categorie

### Dan pas:
→ Lees **FREEMIUM_GUIDE.md** voor Odoo Apps Store publicatie

---

## 📊 Verwachte Tijdlijn

- ✅ **Nu**: Lokaal testen (deze guide)
- ✅ **Week 1**: Productie deployment + 24u monitoring
- ✅ **Week 2**: Team training + fine-tuning
- 💰 **Week 3-4**: Apps Store setup + screenshots
- 🚀 **Maand 2**: Eerste klanten!

---

**Klaar om te testen?** 
Start bij Stap 1 en werk de checklist af. Kom terug als je errors krijgt! 💪
