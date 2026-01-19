# -*- coding: utf-8 -*-
{
    'name': 'VST Article Manager',
    'version': '18.0.2.0.0',
    'category': 'Inventory/Products',
    'summary': 'Gestion des articles VST avec import BATIGEST, exports Naviwest/QuickDevis',
    'description': """
        Module de gestion des articles du distributeur VST
        ==================================================
        
        Ce module permet de :
        - Importer automatiquement les articles depuis le fichier BATIGEST généré par l'exécutable VST
        - Planifier une mise à jour mensuelle automatique
        - Permettre des mises à jour manuelles à la demande
        - Gérer une hiérarchie de familles/sous-familles
        - Consulter l'historique des prix
        - Créer des produits Odoo avec fournisseur VST
        - Exporter vers Naviwest (BEG, NIEDAX, CÂBLES)
        - Exporter vers QuickDevis 7
        - Détecter les articles supprimés du catalogue
        
        Configuration:
        - Chemin de l'exécutable : C:\\Program Files\\Odoo 18.0.20251211\\server\\odoo\\addons\\VST\\BATIGEST.exe
        - Dossier de sortie : C:\\TARIFVST\\
        - Fichier généré : BATIGEST (format texte avec tabulations)
    """,
    'author': 'BYes - Centre GTB LA ROCHE/YON',
    'website': '',
    'license': 'LGPL-3',
    'depends': ['base', 'product', 'mail', 'purchase'],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'wizard/import_vst_wizard_views.xml',
        'wizard/export_naviwest_wizard_views.xml',
        'wizard/export_quickdevis_wizard_views.xml',
        'wizard/create_products_wizard_views.xml',
        'views/vst_article_views.xml',
        'views/vst_famille_views.xml',
        'views/vst_config_views.xml',
        'views/vst_menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
