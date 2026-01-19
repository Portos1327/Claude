# -*- coding: utf-8 -*-
{
    'name': 'Product Price Finder',
    'version': '18.0.1.0.0',
    'category': 'Sales',
    'summary': 'Recherche automatique des prix dans les modules de tarifs lors de la création de produits',
    'description': """
Product Price Finder - Recherche Multi-Sources
===============================================

Ce module intercepte la création de produits Odoo et recherche automatiquement 
les prix correspondants dans différents modules de tarifs installés.

Fonctionnalités principales:
----------------------------
* 🔍 Recherche automatique lors de la création d'un produit
* 🔗 Association automatique avec les articles des modules de tarifs
* 📊 Comparaison des prix entre plusieurs fournisseurs
* 🏷️ Recherche par référence fabricant ET marque
* ⚡ Système de plugins extensible pour nouveaux modules de tarifs

Modules de tarifs supportés:
-----------------------------
* Rexel Article Manager
* VST Article Manager
* Modules futurs via système de plugins

Architecture:
-------------
Le module utilise un système de "Price Providers" (fournisseurs de prix)
permettant d'ajouter facilement de nouvelles sources de prix sans modifier
le code existant.

Compatibilité Odoo 18:
----------------------
* Utilise @api.model_create_multi pour la création batch
* _compute_display_name au lieu de name_get()
* Widgets natifs Odoo (pas de directives OWL dans les formulaires)

    """,
    'author': 'BYes - Centre GTB',
    'website': 'https://www.byes.fr',
    'depends': ['base', 'product', 'purchase'],
    'data': [
        # Sécurité
        'security/ir.model.access.csv',
                
        # Wizards
        'wizard/search_prices_wizard_views.xml',

        # Vues
        'views/product_views.xml',
        'views/price_source_views.xml',
        'views/price_match_views.xml',
        'views/menu_views.xml',

        # Menus (TOUJOURS EN DERNIER)
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
