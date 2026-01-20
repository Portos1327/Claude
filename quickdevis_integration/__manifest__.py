# -*- coding: utf-8 -*-
{
    'name': 'QuickDevis Integration',
    'version': '18.0.1.0.0',
    'category': 'Sales/CRM',
    'summary': 'Intégration QuickDevis 7 avec Odoo 18',
    'description': """
        Module d'intégration entre QuickDevis 7 et Odoo 18.
        
        Fonctionnalités :
        - Ajout de 111 champs personnalisés sur les opportunités
        - Synchronisation bidirectionnelle Odoo ↔ QuickDevis
        - 50 champs Odoo → QuickDevis (données initiales)
        - 58 champs QuickDevis → Odoo (résultats du chiffrage)
        - 3 champs bidirectionnels
    """,
    'author': 'Dimitri Ferrandiz',
    'website': 'https://www.turquand.fr',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}