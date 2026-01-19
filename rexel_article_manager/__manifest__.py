# -*- coding: utf-8 -*-
{
    'name': 'Rexel Article Manager v5.53',
    'version': '5.53.0',
    'category': 'Sales',
    'summary': 'Gestion articles Rexel Cloud - Import Excel et API officielle',
    'description': """
Rexel Article Manager v5.53 - Cloud Ready
==========================================

Gestion complète des articles Rexel avec support API Cloud officielle.

Fonctionnalités principales:
-----------------------------
* 🔄 Import articles depuis Excel Cloud Rexel
* 🌐 Import et mise à jour via API Rexel officielle
* 📊 Mapping complet des 29 colonnes cloud
* ✅ Unités automatiques via API units (logique priorité: API > Conditionnement > Défaut)
* 💰 Mise à jour automatique des prix via API
* 🌳 Création automatique arborescence Famille/Sous-famille/Fonction
* 📈 Historique des prix avec graphiques
* 🔗 Création automatique produits Odoo avec fournisseur
* 📤 Exports Naviwest, QuickDevis 7 (format exact) et Format Rexel
* 🚀 Import rapide par référence Rexel
* 🏷️ Support écotaxe D3E complète
* 🌱 Ecoscore et sélection durable
* 🖼️ URL images produits
* ⚠️ Suivi des articles obsolètes
* 🔒 Verrouillage unité par article
* 🔍 Test API (données brutes) - toutes APIs Découverte et Premium
* 🏭 Association fournisseur Odoo automatique

Nouveautés v5.53:
-----------------
- 🏭 Association Rexel → Fournisseur Odoo (onglet Configuration)
- ✅ Création produit intelligente: détection produit existant par REF/EAN
- 🔗 Ajout automatique fournisseur dans onglet Achats des produits
- 💰 Prix net Rexel intégré comme prix fournisseur
- 📋 Mode import avancé (nouveaux uniquement, MAJ uniquement, tous)
- 🔧 Sélection des champs à mettre à jour lors de l'import
- 🔍 Filtres avancés dans le wizard de mise à jour API

APIs Rexel supportées:
----------------------
Pack Découverte:
* ProductPrice - Prix et remises
* Products/units - Unités de mesure
* Stocks - Disponibilité

Pack Premium:
* Full-image - Images produits
* Technical-sheets - Fiches techniques
* ProductCEE - Certificats économies énergie
* EnvironmentalAttributes - Attributs durables
* ReplacementLinks - Produits de remplacement

    """,
    'author': 'Turquand BTP',
    'website': 'https://www.turquand.fr',
    'depends': ['base', 'stock', 'sale', 'purchase'],
    'data': [
        # Sécurité
        'security/ir.model.access.csv',
        
        # Vues (AVANT les menus pour définir les actions)
        'views/rexel_article_views.xml',
        'views/rexel_config_views.xml',
        'views/rexel_price_history_views.xml',
        'views/rexel_product_family_views.xml',
        'views/rexel_unit_mapping_views.xml',
        
        # Wizards (définissent leurs actions)
        'wizard/import_articles_wizard_views.xml',
        'wizard/export_naviwest_wizard_views.xml',
        'wizard/export_quickdevis_wizard_views.xml',
        'wizard/update_prices_wizard_views.xml',
        'wizard/create_products_wizard_views.xml',
        'wizard/export_rexel_wizard_views.xml',
        'wizard/import_reference_wizard_views.xml',
        'wizard/test_api_wizard_views.xml',
        
        # Menus (EN DERNIER pour référencer les actions)
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl', 'requests'],
    },
    'post_init_hook': '_post_init_hook',
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
