{
    'name': 'QDV7 Sync - Configuration Complète',
    'version': '18.0.7.2',
    'category': 'Tools',
    'summary': 'Synchronisation Odoo → SQL Server → QuickDevis 7 avec gestion des familles',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'views/sql_config_views.xml',
        'views/family_views.xml',
        'views/supplier_views.xml',
        'views/menu.xml',
        'data/default_data.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
