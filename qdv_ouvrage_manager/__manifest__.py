# -*- coding: utf-8 -*-
{
    'name': 'QDV Ouvrage Manager',
    'version': '18.0.3.1.0',
    'category': 'Sales',
    'summary': 'Gestion des bases d\'ouvrage QDV7 avec picker articles et création',
    'description': '''
QDV Ouvrage Manager v3.1
=========================

Gestion complète des ouvrages QuickDevis 7 dans Odoo 18.

Fonctionnalités principales :
- 🔍 Découverte automatique des fichiers .grp
- 📥 Import bases d\'ouvrage QDV7 (.grp / SQLite)
- ✏️ Visualisation et modification des ouvrages
- 📋 Gestion des articles/minutes par ouvrage
- 🔍 Picker : recherche dans qdv_tarifs_manager et qdv_sync_v7
  → Insertion avec base_source exact (.qdb) pour QDV7
- ➕ Création d\'ouvrages de zéro avec composition guidée
- 🔄 Remplacement en masse d\'articles
- 📤 Export JSON pour synchronisation vers QDV7
- 🕒 Surveillance automatique (CRON)

Dépendances optionnelles :
- qdv_tarifs_manager : bases tarifs fabricants (LEG, SCH, BEG...)
- qdv_sync_v7        : bases articles personnalisées (Turquand, temps de pose...)
    ''',
    'author': 'BYes - Centre GTB LA ROCHE/YON - Turquand',
    'website': 'https://www.turquand.fr',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/qdv_ouvrage_config_views.xml',
        'views/qdv_ouvrage_famille_views.xml',
        'views/qdv_ouvrage_views.xml',
        'views/qdv_ouvrage_base_views.xml',
        'wizard/import_grp_wizard_views.xml',
        'wizard/export_grp_wizard_views.xml',
        'wizard/discovery_wizard_views.xml',
        'wizard/replace_article_wizard_views.xml',
        'wizard/catalogue_wizards_views.xml',
        'views/qdv_ouvrage_minute_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
