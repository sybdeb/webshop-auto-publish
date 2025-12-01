# Webshop Auto-Publish voor Odoo 19

> **Automatische product validatie en publicatie voor je Odoo webshop**

[![Odoo Version](https://img.shields.io/badge/Odoo-19.0-714B67.svg)](https://www.odoo.com)
[![License: LGPL-3](https://img.shields.io/badge/License-LGPL%20v3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)

## 🎯 Overzicht

Webshop Auto-Publish is een krachtige Odoo 19 module die automatisch je producten valideert en publiceert op basis van configureerbare kwaliteitsregels. Geen handmatig werk meer - laat het systeem beslissen welke producten klaar zijn voor publicatie!

### ✨ Belangrijkste Features

- **📊 Real-time Dashboard** - Overzicht van productstatus met 6 klikbare tegels
- **🔄 Automatische Validatie** - Cron job valideert producten elke 15 minuten
- **🎯 Configureerbaar per Categorie** - Stel regels in per website categorie
- **✅ 9 Validatieregels** - Van afbeelding tot leverancier voorraad
- **🚀 Auto-Publish/Depublish** - Producten gaan automatisch online/offline
- **📱 Emoji Feedback** - Visuele indicatoren (❌/✅) in producten
- **🔧 Freemium Model** - Gratis dashboard, premium validatie

---

## 📸 Screenshots

### Dashboard Overzicht
*Real-time overzicht van je product catalogus met 6 klikbare tegels*

### Product Validatie
*Duidelijke validatieresultaten met emoji's per product*

### Categorie Regels
*Configureer validatieregels per website categorie (Laptops, Desktops, etc.)*

---

## 🚀 Quick Start

### Installatie

```bash
# 1. Kopieer modules naar addons folder
cp -r webshop_* /path/to/odoo/addons/

# 2. Restart Odoo
sudo systemctl restart odoo

# 3. Update Apps lijst
# Ga naar Apps → Update Apps List

# 4. Installeer modules
# Zoek naar "Webshop Auto Publish" en klik Installeren
```

### Eerste Configuratie

1. **Ga naar Producten → Dashboard**
   - Zie onmiddellijk je product statistieken

2. **Configureer Website Categorieën**
   - Producten → Instellingen → Website Categorieën
   - Open een categorie (bijv. "Laptops")
   - Scroll naar "Webshop Auto-Publish Regels"
   - Configureer:
     - ✅ Auto-Publiceren aan/uit
     - 📦 Minimale Voorraad Leverancier (default: 5)
     - 📉 Prijsdaling Drempel (default: 15%)
     - 🔖 Vereiste velden (EAN, Merk, Omschrijvingen)

3. **Controleer Cron Job**
   - Producten → Instellingen → Cron Jobs
   - "Webshop Product Validatie" draait elke 15 minuten

4. **Bekijk Validatieresultaten**
   - Open een product
   - Ga naar tab "Webshop Validatie"
   - Zie validatiestatus en errors

---

## 📋 Validatieregels

Het systeem controleert automatisch 9 kwaliteitscriteria:

| # | Regel | Beschrijving | Configureerbaar |
|---|-------|--------------|-----------------|
| 1 | **Hoofdafbeelding** | Product moet een foto hebben | ❌ Verplicht |
| 2 | **Verkoopprijs** | Prijs moet > €0 zijn | ❌ Verplicht |
| 3 | **Korte Omschrijving** | Website beschrijving ingevuld | ✅ Per categorie |
| 4 | **Lange Omschrijving** | Verkoop omschrijving ingevuld | ✅ Per categorie |
| 5 | **EAN/Barcode** | Product heeft geldige barcode | ✅ Per categorie |
| 6 | **Merk** | Merk/brand toegewezen | ✅ Per categorie |
| 7 | **Website Categorie** | Minimaal 1 categorie toegewezen | ❌ Verplicht |
| 8 | **Leverancier Voorraad** | Minimaal X stuks op voorraad | ✅ Instelbaar (default: 5) |
| 9 | **Prijsdaling** | Niet meer dan X% gedaald | ✅ Instelbaar (default: 15%) |

---

## 🏗️ Module Structuur

```
webshop_auto_publish/              # Bundle module
├── webshop_catalog_dashboard/     # FREE - Dashboard basis
│   ├── models/
│   │   └── dashboard.py           # 6 computed tiles
│   └── views/
│       └── dashboard_views.xml    # Bootstrap cards UI
│
└── webshop_quality_rules/         # PREMIUM - Validatie engine
    ├── models/
    │   ├── product_template.py    # 9 validatieregels + cron
    │   └── product_public_category.py  # 7 configuratie velden
    ├── views/
    │   ├── product_template_views.xml
    │   └── product_public_category_views.xml
    └── data/
        └── cron.xml               # 15-min validatie job
```

---

## ⚙️ Configuratie

### Dashboard Tegels

| Tegel | Beschrijving | Action |
|-------|--------------|--------|
| 🟢 Klaar voor publicatie | Producten die aan alle regels voldoen | Toon kanban view |
| 🖼️ Mist hoofdafbeelding | Producten zonder foto | Filter missing image |
| 💰 Mist verkoopprijs | Prijs is €0 of lager | Filter missing price |
| 📝 Mist omschrijving | Korte of lange tekst ontbreekt | Filter missing description |
| 🏷️ Mist EAN/barcode | Barcode niet ingevuld | Filter missing EAN |
| 📉 Prijsdaling >15% | Producten met grote prijsdaling | Filter price drops |

### Cron Job

**Interval:** 15 minuten  
**Actief:** Ja (standaard)

**Functionaliteit:**
1. Zoekt producten met `need_validation = True`
2. Voert validatie uit
3. Publiceert/depubliceert automatisch
4. Logt resultaten

---

## 💼 Freemium Model

### FREE - Dashboard Module

**Inbegrepen:**
- ✅ Real-time dashboard met 6 tegels
- ✅ Product statistieken
- ✅ Klikbare acties
- ✅ Basis menu structuur

### PREMIUM - Quality Rules Module

**Prijs:** €49/maand of €490/jaar  

**Extra features:**
- ✅ Automatische validatie (9 regels)
- ✅ Auto-publish/depublish
- ✅ Configureerbare regels per categorie
- ✅ Cron job validatie
- ✅ Email support

---

## 📝 Changelog

### Version 19.0.1.0.0 (2025-12-01)

**Features:**
- ✨ Migratie van product.category naar product.public.category
- ✨ 7 configureerbare velden per website categorie
- ✨ Dashboard met 6 klikbare tegels
- ✨ Emoji validatie feedback (❌/✅)
- ✨ Auto-publish/depublish op basis van regels
- ✨ Cron job elke 15 minuten

**Bugfixes:**
- 🐛 Fixed view_mode "tree" → "kanban,form" (Odoo 19)
- 🐛 Removed deprecated cron fields
- 🐛 Fixed circular dependency
- 🐛 Odoo 18/19 compatibility improvements

---

## 📄 License

**LGPL-3.0** - Copyright (C) 2025 Nerbys

---

## 🤝 Support

**Email:** support@nerbys.nl  
**Website:** https://nerbys.nl  
**GitHub:** [Report a bug](https://github.com/nerbys/webshop_auto_publish/issues)

---

## 👨‍💻 Credits

**Ontwikkeld door:** Nerbys  
**Auteur:** Sybdeb  
**Odoo Version:** 19.0  
**Release:** December 2025

---

**⭐ Vond je deze module nuttig? Geef een ster op GitHub!**
