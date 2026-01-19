# Rexel Article Manager v4.0 - Cloud Ready

Module Odoo 18 pour la gestion des articles Rexel avec support de l'API Cloud officielle.

## 🚀 Fonctionnalités

### Import des articles
- **Import Excel** : Import depuis les fichiers Excel exportés du cloud Rexel (Esabora)
- **Import API** : Mise à jour des prix via l'API ProductPrice officielle

### 29 Colonnes Cloud Rexel supportées

| Colonne Excel | Libellé dans Odoo | Description |
|---------------|-------------------|-------------|
| CODE_LIDIC | Trigramme fabricant | Code 3 lettres du fabricant |
| REF | Référence fabricant | Référence fabricant de l'article |
| REF_REXEL | Référence commerciale Rexel | Référence commerciale Rexel |
| CODE_LIDIC_AND_REF | Référence Rexel complète | Trigramme + référence fabricant |
| DESIGNATION | Désignation | Désignation de l'article |
| CODE_EAN13 | Code EAN13 | Code GTIN ou EAN13 |
| LIBELLE_FABRICANT | Nom du fabricant | Nom complet du fabricant |
| PRIX_BASE | Prix de base | Tarif de base (sans conditions commerciales) |
| PRIX_NET | Prix net client | Tarif client appliqué |
| PRIX_VENTE | Prix de vente | Tarif selon conditions commerciales classiques |
| REMISE | Remise (%) | Condition commerciale sur l'article |
| DATE_TARIF | Date de tarif | Date de référence du tarif |
| DATE_PEREMPTION | Date de péremption | Date de péremption éventuelle |
| CONDITIONNEMENT | Conditionnement de vente | Conditionnement de vente Rexel |
| UOM | Unité de mesure | Unité de mesure (U, M, KG, BOI...) |
| FAMILLE | Code famille | Code famille Rexel |
| SOUS_FAMILLE | Code sous-famille | Code sous-famille Rexel |
| FONCTION | Code fonction | Code fonction Rexel |
| LIBELLE_FAMILLE | Famille | Libellé famille Rexel |
| LIBELLE_SOUS_FAMILLE | Sous-famille | Libellé sous-famille Rexel |
| LIBELLE_FONCTION | Fonction | Libellé fonction Rexel |
| REF_D3E | Référence écotaxe | Référence de l'écotaxe |
| LIBELLE_D3E | Libellé écotaxe | Désignation de l'écotaxe |
| CODE_D3E | Code écotaxe | Code de l'écotaxe |
| UNITE_D3E | Unité écotaxe | Unité d'écotaxe dans l'article |
| MONTANT_D3E | Montant écotaxe | Montant de l'écotaxe |
| ECOSCORE | Ecoscore | Ecoscore de l'article |
| SELECTION_DURABLE | Sélection durable | Choix sélection durable |
| URL_IMAGE | URL image | URL de l'image article |

## 🔧 Configuration API

### Paramètres Pack Découverte (pré-configurés)

| Paramètre | Valeur |
|-----------|--------|
| URL Token | https://login.microsoftonline.com/822cd975-5643-4b7e-b398-69a164e55719/oauth2/v2.0/token/ |
| Client ID | 4036c6d5-fce1-4569-a177-072a4e45bd39 |
| Scope | aee2ba94-a840-453a-9151-1355638ac04e/.default |
| Clé d'abonnement | e9fa63ce8d934beb83c5a1f94817983a |
| URL API | https://api.rexel.fr |

### À configurer par l'utilisateur

- **Client Secret** : `bhk8Q~vzGGx2rzDXnonyVVlkTAoYZ4tdu7.rmc38`
- **N° client Rexel** : Votre numéro de compte client (7 chiffres)
- **Mot client** : TURQUAND (ou votre mot client spécifique)

## 📡 APIs Rexel utilisées

### ProductPrice (Pack Découverte + Premium)
- **URL** : `https://api.rexel.fr/external/productprices/productSalePrices`
- **Méthode** : POST
- **Usage** : Récupération des prix (base, net, remise, écotaxe)

### Customers (Pack Découverte + Premium)
- **URL** : `https://api.rexel.fr/external/customers/{idCustomer}`
- **Méthode** : GET
- **Usage** : Test de connexion et informations client

## 📦 Installation

1. Copier le dossier `rexel_article_manager` dans le répertoire addons d'Odoo :
   ```
   C:\Program Files\Odoo 18.0.20251211\server\odoo\addons\
   ```

2. Redémarrer le serveur Odoo

3. Activer le mode développeur

4. Aller dans Apps → Mettre à jour la liste des applications

5. Rechercher "Rexel" et installer le module

## 🔄 Utilisation

### Import depuis Excel

1. Aller dans **Rexel Articles → Import/Export → Importer depuis Excel/API**
2. Sélectionner le mode "Importer depuis un fichier Excel"
3. Charger votre fichier Excel cloud Rexel
4. Cliquer sur "Importer"

### Mise à jour des prix via API

1. Configurer l'API dans **Rexel Articles → Configuration**
2. Activer l'API et saisir le Client Secret
3. Tester la connexion
4. Aller dans **Import/Export → Mettre à jour les prix (API)**
5. Sélectionner les articles à mettre à jour
6. Lancer la mise à jour

## ❌ Fonctionnalités supprimées (v4.0)

- ~~Scraping des unités sur rexel.fr~~ → Remplacé par colonne UOM du fichier Excel
- ~~Connexion/scraping sur le site rexel.fr~~ → Remplacé par API OAuth2 officielle

## 📋 Dépendances

- Python : `openpyxl`, `requests`
- Odoo : `base`, `stock`, `sale`, `purchase`

## 🔒 Sécurité

Les informations sensibles (Client Secret, Token) sont stockées de manière sécurisée dans Odoo et ne sont accessibles qu'aux administrateurs système.

## 📞 Support

Pour toute question concernant l'API Rexel, contactez votre commercial Rexel ou le support technique Rexel.
