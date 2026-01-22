# -*- coding: utf-8 -*-
{
    'name': 'QuickDevis 7 - Intégration CRM (111 champs)',
    'version': '19.0.2.0.0',
    'category': 'Sales/CRM',
    'summary': 'Synchronisation bidirectionnelle complète entre Odoo CRM et QuickDevis 7',
    'description': '''
QuickDevis 7 - Intégration CRM Complète
========================================

Module de synchronisation bidirectionnelle entre Odoo CRM et QuickDevis 7.

Fonctionnalités
---------------
* 111 champs personnalisés dans le module CRM
* Synchronisation bidirectionnelle :
  - 50 champs Odoo → QuickDevis (contexte client, projet, contacts)
  - 58 champs QuickDevis → Odoo (résultats chiffrage, prix, quantités)
  - 2 champs bidirectionnels
  - 1 champ QuickDevis uniquement
  
* Boutons de synchronisation :
  - "Synchroniser vers QuickDevis" : Envoie les données contexte
  - "Rafraîchir depuis QuickDevis" : Récupère les résultats de chiffrage
  
* Organisation en sections :
  - Section "Données envoyées à QuickDevis" (modifiable dans Odoo)
  - Section "Données reçues de QuickDevis" (lecture seule dans Odoo)
  - Section "Champs bidirectionnels"
  
* Colonnes optionnelles dans la vue liste
* Filtres de recherche avancés

Utilisation
-----------
1. Dans Odoo : Créer/modifier une opportunité, remplir les champs contexte
2. Cliquer "Synchroniser vers QuickDevis"
3. Dans QuickDevis 7 : Entrer le numéro d'opportunité Odoo
4. La macro récupère automatiquement les 50 champs de contexte
5. Effectuer le chiffrage dans QuickDevis
6. La macro envoie les 58 champs de résultats vers Odoo
7. Dans Odoo : Cliquer "Rafraîchir depuis QuickDevis" pour voir les résultats

Notes d'installation
-------------------
Ce module DOIT être installé manuellement dans le répertoire addons/ d'Odoo,
suivi d'un redémarrage du serveur Odoo.

L'interface "Importer un module" ne fonctionne PAS pour ce type de module
car elle ne charge que les fichiers XML et pas le code Python.

Auteur : Assistant Claude
Date : 2025-12-03
Version : 2.0.0 (111 champs complets)
    ''',
    'author': 'Votre Entreprise',
    'website': 'https://www.votreentreprise.com',
    'license': 'LGPL-3',
    'depends': ['crm'],
    'data': [
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
