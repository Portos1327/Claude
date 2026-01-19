# -*- coding: utf-8 -*-
{
    'name': 'Cable Price Comparator',
    'version': '18.0.14.0.0',
    'category': 'Purchases',
    'summary': 'Comparateur de prix câbles - Matching STRICT TYPE-CONFIG-SECTION',
    'description': """
Cable Price Comparator V14 - Module Odoo 18
============================================

**RÈGLES MÉTIER FONDAMENTALES:**
- Matching STRICT: TYPE + CONFIG + SECTION
- Différencier R2V 3G1,5 de R2V 3G2,5
- Différencier G (avec terre) de X (sans terre)
- AUCUN fuzzy matching

**Clé de matching:** TYPE-CONFIG-SECTION
Exemples:
- R2V-3G-1,5 (R2V 3 conducteurs avec terre, section 1,5mm²)
- AR2V-1X-50 (AR2V 1 conducteur sans terre, section 50mm²)
- H07V-U--2,5 (fil simple, section 2,5mm²)

**Types de câbles depuis fichier TURQUAND:**
- Fils rigides (H07V-U, H07V-R, H07Z1-U)
- Fils souples (H05V-K, H07V-K, H07Z1-K)
- Câbles industriels rigides (R2V, AR2V, Cuivre nu)
- Câbles industriels souples (H07RN-F)
- Sécurité incendie (CR1-C1, FR-N1X1G1)
- Téléphoniques (SYT1, LIYCY)

**Import €/ml par défaut**
Les tarifs sont en €/ml (mètre linéaire), pas €/km.

Développé pour BYes - Centre GTB LA ROCHE/YON
    """,
    'author': 'BYes - Dimitri',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'product',
        'purchase',
        'mail',
    ],
    'data': [
        # Sécurité
        'security/cable_comparator_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/sequence_data.xml',
        # Vues modèles
        'views/cable_supplier_views.xml',
        'views/cable_supplier_price_views.xml',
        'views/cable_pricelist_views.xml',
        'views/cable_pricelist_line_views.xml',
        'views/cable_product_master_views.xml',
        'views/cable_product_match_views.xml',
        'views/cable_comparison_views.xml',
        'views/product_template_views.xml',
        # Wizards
        'wizard/import_pricelist_wizard_views.xml',
        'wizard/import_elen_wizard_views.xml',
        'wizard/run_matching_wizard_views.xml',
        'wizard/export_comparison_wizard_views.xml',
        # Menus
        'views/menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
