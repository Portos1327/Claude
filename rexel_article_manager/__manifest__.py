# -*- coding: utf-8 -*-
{
    'name': 'Rexel Article Manager v5.0 Cloud',
    'version': '5.0.0',
    'category': 'Sales',
    'summary': 'Gestion articles Rexel Cloud - Import Excel et API officielle',
    'description': """
Rexel Article Manager v5.0 - Cloud Ready
=========================================

Gestion complète des articles Rexel avec support API Cloud officielle.

Fonctionnalités principales:
-----------------------------
* 🔄 Import articles depuis Excel Cloud Rexel
* 🌐 Import et mise à jour via API Rexel officielle
* 📊 Mapping complet des 29 colonnes cloud
* ✅ Unités automatiques via API units
* 💰 Mise à jour automatique des prix via API
* 🌳 Création automatique arborescence Famille/Sous-famille/Fonction
* 📈 Historique des prix avec graphiques
* 🔗 Création automatique produits Odoo
* 📤 Exports Naviwest, QuickDevis 7 et Format Rexel
* 🚀 Import rapide par référence Rexel
* 🏷️ Support écotaxe D3E complète
* 🌱 Ecoscore et sélection durable
* 🖼️ URL images produits
* ⚠️ Suivi des articles obsolètes

Nouveautés v5.0:
----------------
- ✅ Export format Rexel (réimportable)
- ✅ Import rapide par référence via API
- ✅ Création automatique hiérarchie familles
- ✅ Correction récupération unités API units
- ✅ Suivi articles obsolètes

APIs Rexel supportées:
----------------------
* ProductPrice - Mise à jour prix et remises
* Products/units - Récupération unités de mesure
* Customers - Informations client
* Stocks - Disponibilité (à venir)
* Quotes - Gestion devis (à venir)

    """,
    'author': 'Your Company',
    'website': 'https://www.yourcompany.com',
    'depends': ['base', 'stock', 'sale', 'purchase'],
    'data': [
        # Sécurité
        'security/ir.model.access.csv',
        
        # Vues (AVANT les menus pour définir les actions)
        'views/rexel_article_views.xml',
        'views/rexel_config_views.xml',
        'views/rexel_price_history_views.xml',
        'views/rexel_product_family_views.xml',
        
        # Wizards (définissent leurs actions)
        'wizard/import_articles_wizard_views.xml',
        'wizard/export_naviwest_wizard_views.xml',
        'wizard/export_quickdevis_wizard_views.xml',
        'wizard/update_prices_wizard_views.xml',
        'wizard/create_products_wizard_views.xml',
        'wizard/export_rexel_wizard_views.xml',
        'wizard/import_reference_wizard_views.xml',
        
        # Menus (EN DERNIER pour référencer les actions)
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl', 'requests'],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
