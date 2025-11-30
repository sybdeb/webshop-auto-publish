# Git Setup Instructies

## Stap 1: Initialize Git Repository
```bash
cd /c/Users/Sybde/Projects/webshop_auto_publish
git init
git add .
git commit -m "Initial commit: Webshop Auto-Publish v1.0"
```

## Stap 2: Maak GitHub Repository
1. Ga naar https://github.com/new
2. Repository naam: `webshop_auto_publish`
3. Beschrijving: "Odoo 19 module voor automatische product-validatie en publicatie"
4. Maak repository aan (public of private)

## Stap 3: Push naar GitHub
```bash
git remote add origin https://github.com/sybdeb/webshop_auto_publish.git
git branch -M main
git push -u origin main
```

## Stap 4: Installeer in Odoo
1. Kopieer/symlink deze folder naar je Odoo addons-path
2. Herstart Odoo server
3. Update Apps List: `Instellingen → Apps → Update Apps List`
4. Zoek naar "Webshop Auto-Publish"
5. Installeer de bundle module (installeert automatisch alle dependencies)

## Optioneel: .gitignore
Voeg eventueel een .gitignore toe:
```
__pycache__/
*.pyc
*.pyo
*.log
.vscode/
```
