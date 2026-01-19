# 🚀 REXEL ARTICLE MANAGER v4.0 - GUIDE DE MIGRATION

## 📋 CHANGEMENTS MAJEURS

### ✅ NOUVEAUTÉS v4.0

1. **DOUBLE MODE D'IMPORT**
   - Import depuis fichier Excel (comme avant)
   - **NOUVEAU** : Import depuis API Rexel Cloud
   - Configuration flexible dans "Configuration Rexel"

2. **MAPPING COMPLET DES COLONNES CLOUD**
   - 29 champs mappés depuis le fichier cloud Rexel
   - Noms de colonnes lisibles en français
   - Support de toutes les données : prix, écotaxe, environnement, etc.

3. **UNITÉS AUTOMATIQUES**
   - ❌ SUPPRIMÉ : Scraping des unités sur rexel.fr
   - ✅ NOUVEAU : Unités directement dans la colonne "UOM" du fichier

4. **MISE À JOUR DES PRIX VIA API**
   - ❌ SUPPRIMÉ : Connexion au site rexel.fr
   - ✅ NOUVEAU : API ProductPrice pour mise à jour automatique
   - Fréquence configurable (quotidien, hebdomadaire, mensuel)

5. **NOUVEAUX CHAMPS**
   - Écotaxe D3E complète (réf, libellé, code, unité, montant)
   - Ecoscore et sélection durable
   - URL d'image produit
   - Date de péremption
   - Trigramme fabricant + nom complet

## 📊 MAPPING DES COLONNES

### Fichier Excel Cloud Rexel → Odoo

| Colonne Excel          | Champ Odoo               | Description                      |
|------------------------|--------------------------|----------------------------------|
| REF                    | reference_fabricant      | Référence fabricant              |
| REF_REXEL              | reference_rexel          | Référence commerciale Rexel      |
| CODE_LIDIC_AND_REF     | code_lidic_and_ref       | Trigramme + référence            |
| DESIGNATION            | designation              | Désignation de l'article         |
| CODE_EAN13             | code_ean13               | Code GTIN ou EAN13               |
| CODE_LIDIC             | trigramme_fabricant      | Trigramme Fabricant (3 lettres)  |
| LIBELLE_FABRICANT      | fabricant_libelle        | Nom du fabricant                 |
| PRIX_BASE              | prix_base                | Tarif de base                    |
| PRIX_NET               | prix_net                 | Tarif client appliqué            |
| PRIX_VENTE             | prix_vente               | Tarif avec conditions            |
| REMISE                 | remise                   | Condition commerciale            |
| DATE_TARIF             | date_tarif               | Date de référence du tarif       |
| DATE_PEREMPTION        | date_peremption          | Date de péremption               |
| CONDITIONNEMENT        | conditionnement          | Conditionnement de vente         |
| **UOM**                | **unite_mesure**         | **Unité de mesure** ⭐            |
| FAMILLE                | famille_code             | Code famille Rexel               |
| SOUS_FAMILLE           | sous_famille_code        | Code sous-famille Rexel          |
| FONCTION               | fonction_code            | Code fonction Rexel              |
| LIBELLE_FAMILLE        | famille_libelle          | Libellé famille                  |
| LIBELLE_SOUS_FAMILLE   | sous_famille_libelle     | Libellé sous-famille             |
| LIBELLE_FONCTION       | fonction_libelle         | Libellé fonction                 |
| REF_D3E                | ref_d3e                  | Référence écotaxe                |
| LIBELLE_D3E            | libelle_d3e              | Désignation écotaxe              |
| CODE_D3E               | code_d3e                 | Code écotaxe                     |
| UNITE_D3E              | unite_d3e                | Unité d'écotaxe                  |
| MONTANT_D3E            | montant_d3e              | Montant écotaxe                  |
| ECOSCORE               | ecoscore                 | Ecoscore de l'article            |
| SELECTION_DURABLE      | selection_durable        | Sélection durable (oui/non)      |
| URL_IMAGE              | url_image                | URL de l'image article           |

## 🔧 CONFIGURATION API REXEL

### Dans Odoo : Menu → Configuration → Configuration Rexel

```
┌─────────────────────────────────────────────────┐
│ API Rexel Cloud                                 │
├─────────────────────────────────────────────────┤
│ ☑ API activée                                   │
│                                                 │
│ URL de base API:                                │
│ https://api.rexel.fr                            │
│                                                 │
│ N° client Rexel:                                │
│ 6353343                                         │
│                                                 │
│ Périmètre client (Mot client):                  │
│ APITEST                                         │
│                                                 │
│ [Tester la connexion API]                       │
└─────────────────────────────────────────────────┘
```

### APIs utilisées :

1. **ProductPrice** - Mise à jour des prix
   - URL: `/external/productprices/productSalePrices`
   - Permet de récupérer prix_base, prix_net, remise

2. **Customers** - Informations client
   - URL: `/external/customers/{idCustomer}`
   - Pour tester la connexion

3. **Stocks** (optionnel) - Niveaux de stock
   - URL: `/external/stocks/positions`

## 📥 PROCÉDURE D'IMPORT

### Option 1 : Import depuis Excel

```
1. Menu → Import / Export → Importer depuis Excel/API
2. Choisir "Importer depuis un fichier Excel"
3. Sélectionner votre fichier cloud Rexel (.xlsx)
4. Options:
   ☑ Mettre à jour les articles existants
   ☐ Créer automatiquement les produits Odoo
5. Cliquer "Importer"
6. ✅ Articles importés avec unités automatiques !
```

### Option 2 : Mise à jour des prix via API

```
1. Menu → Import / Export → Mettre à jour les prix (API)
2. Configuration déjà chargée
3. Cliquer "Mettre à jour"
4. ✅ Tous les prix mis à jour depuis l'API !
```

## 🔄 MIGRATION DEPUIS v3.0

### Étape 1 : Sauvegarde (IMPORTANT)

```sql
-- Exporter vos données existantes
SELECT * FROM rexel_article;
```

### Étape 2 : Désinstallation v3.0

```
1. Odoo → Applications
2. Rechercher "Rexel Article Manager"
3. Désinstaller
4. Supprimer le dossier physique
```

### Étape 3 : Installation v4.0

```
1. Copier rexel_v4/ vers addons/
2. Renommer en "rexel_article_manager"
3. Redémarrer Odoo
4. Applications → Mettre à jour la liste
5. Installer "Rexel Article Manager v4.0"
```

### Étape 4 : Configuration API

```
1. Menu → Configuration → Configuration Rexel
2. Compléter:
   - N° client Rexel
   - Mot client
3. ☑ Activer l'API
4. Tester la connexion
```

### Étape 5 : Réimport des données

```
1. Télécharger export Excel cloud Rexel
2. Import via le nouveau wizard
3. ✅ Les unités sont maintenant dans la colonne UOM !
```

## ❌ FONCTIONNALITÉS SUPPRIMÉES

1. **Scraping des unités sur rexel.fr**
   - Raison : Données maintenant dans UOM
   - Avantage : Plus rapide, plus fiable

2. **Connexion au site rexel.fr pour les prix**
   - Raison : API officielle disponible
   - Avantage : Plus stable, plus performant

3. **Wizard "Compléter les unités"**
   - Plus nécessaire avec la colonne UOM

## ✅ FONCTIONNALITÉS CONSERVÉES

1. ✅ Hiérarchie 5 niveaux
2. ✅ Historique des prix avec graphiques
3. ✅ Création produits Odoo (améliorée)
4. ✅ Exports Naviwest / QuickDevis
5. ✅ Filtres avancés

## 🆕 AMÉLIORATIONS FUTURES

### Prévues pour v4.1

- [ ] Import complet via API (sans Excel)
- [ ] Synchronisation automatique programmée
- [ ] API Stocks pour disponibilité temps réel
- [ ] API Quotes pour gestion devis
- [ ] Images produits depuis URL_IMAGE

## 📞 SUPPORT

En cas de problème :

1. Vérifier les logs : Menu → Configuration → Logs
2. Tester la connexion API
3. Vérifier le mapping des colonnes Excel
4. Consulter la documentation API Rexel

## 🎯 AVANTAGES v4.0

| Aspect              | v3.0                  | v4.0                      |
|---------------------|----------------------|---------------------------|
| Source des données  | CSV Esabora          | Excel Cloud + API         |
| Unités             | Scraping (lent)       | ✅ Colonne UOM (rapide)   |
| Prix               | Scraping site         | ✅ API officielle         |
| Écotaxe            | Non                   | ✅ Complète (D3E)         |
| Environnement      | Non                   | ✅ Ecoscore + Durable     |
| Images             | Non                   | ✅ URL disponible         |
| Fabricant          | Code seulement        | ✅ Code + Nom complet     |
| Mise à jour        | Manuelle              | ✅ API automatisable      |
| Fiabilité          | Moyenne (scraping)    | ✅ Élevée (API)           |
| Performance        | Lente (scraping)      | ✅ Rapide (API)           |

## 🚀 QUICK START

```bash
# 1. Installation
cp -r rexel_v4 /path/to/odoo/addons/rexel_article_manager
service odoo restart

# 2. Dans Odoo
# Applications → Installer "Rexel Article Manager v4.0"

# 3. Configuration
# Menu → Configuration Rexel
# Compléter N° client et activer API

# 4. Import
# Menu → Import / Export → Importer
# Charger fichier Excel cloud Rexel

# 5. ✅ Terminé !
```

---

**Version** : 4.0.0  
**Date** : Décembre 2025  
**Compatibilité** : Odoo 18  
**API** : Rexel Cloud API v2  
