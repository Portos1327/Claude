# VST Article Manager v2.0

Module Odoo 18 pour la gestion des articles du distributeur VST.

## Fonctionnalités

### Import
- ✅ Lancement de l'exécutable BATIGEST.exe
- ✅ Import automatique depuis le fichier BATIGEST généré
- ✅ Mise à jour ou création des articles
- ✅ Calcul automatique des remises
- ✅ Détection des articles supprimés du catalogue
- ✅ Historique des changements de prix

### Produits Odoo
- ✅ Création de produits Odoo à partir des articles VST
- ✅ Recherche et liaison avec les produits existants (par référence fabricant)
- ✅ Ajout automatique de VST comme fournisseur
- ✅ Dissociation des produits

### Visualisation
- ✅ Vue liste avec toutes les colonnes essentielles
- ✅ Arborescence navigable des familles (5 niveaux)
- ✅ Filtres multiples sur toutes les colonnes
- ✅ Groupements par Famille, Sous-famille, Fabricant, Marque

### Export
- ✅ **Export Naviwest** : 3 formats (BEG, NIEDAX, CÂBLES)
- ✅ **Export QuickDevis 7** : Format compatible avec 2 onglets (Articles + Structure)
- ✅ Sélection multiple d'articles pour export
- ✅ Téléchargement direct des fichiers Excel

## Installation

### Prérequis
```bash
pip install openpyxl --break-system-packages
```

### Installation du module
1. Copier le dossier `vst_article_manager` dans le répertoire `addons` d'Odoo
2. Redémarrer le service Odoo
3. Aller dans Apps → Mettre à jour la liste des apps
4. Rechercher "VST Article Manager"
5. Cliquer sur "Installer"

## Configuration

### 1. Configurer les chemins
Menu **VST Articles → Configuration → Configuration VST**

- **Chemin de l'exécutable** : `C:\Program Files\Odoo 18.0.20251211\server\odoo\addons\VST\BATIGEST.exe`
- **Dossier de sortie** : `C:\TARIFVST\`
- **Nom du fichier** : `BATIGEST`

### 2. Configurer le fournisseur
Dans la même page de configuration :
- Sélectionner le **Fournisseur VST** (doit être créé au préalable dans les contacts)
- Définir le **Délai de livraison** par défaut

### 3. Templates d'export (optionnel)
Pour les exports Naviwest, configurer les chemins des templates Excel.

## Utilisation

### Importer des articles
1. Menu **VST Articles → Import / Export → Importer depuis BATIGEST**
2. Choisir le mode :
   - **Importer depuis le fichier existant** : utilise le fichier BATIGEST déjà présent
   - **Lancer l'exécutable puis importer** : lance BATIGEST.exe puis importe
3. Configurer les options
4. Cliquer sur "Lancer l'import"

### Créer des produits Odoo
1. Sélectionner les articles dans la liste
2. Menu **Action → 🏭 Créer produits Odoo**
3. Configurer les options
4. Cliquer sur "Créer les produits"

### Exporter vers Naviwest
1. Sélectionner les articles dans la liste
2. Menu **Action → 📤 Export vers Naviwest**
3. Choisir le type (BEG, NIEDAX ou CÂBLES)
4. Cliquer sur "Exporter"
5. Télécharger le fichier Excel généré

### Exporter vers QuickDevis 7
1. Sélectionner les articles dans la liste
2. Menu **Action → 📤 Export vers QuickDevis**
3. Cliquer sur "Exporter"
4. Télécharger le fichier Excel généré

## Structure du fichier BATIGEST

Le fichier BATIGEST est un fichier texte avec des colonnes séparées par des tabulations :

| Index | Colonne | Description |
|-------|---------|-------------|
| 0 | Code Article | Code article VST unique |
| 1 | Famille Code | Code hiérarchique de la famille |
| 2 | Source | Source (VST) |
| 3 | Désignation | Description de l'article |
| 4 | Code Alpha | Code alphabétique |
| 5 | Prix Achat Adhérent | Prix d'achat pour les adhérents |
| 6 | Prix Public HT | Prix public hors taxes |
| 7 | Prix Public TTC | Prix public TTC |
| 8 | Écotaxe HT | Écotaxe hors taxes |
| 9 | Écotaxe TTC | Écotaxe TTC |
| 10 | Code Fabricant | Code du fabricant |
| 11 | Nom Fabricant | Nom du fabricant |
| 12 | Référence Fabricant | Référence chez le fabricant |
| 13 | Date Dernier Prix | Date au format jjmmaaaa |
| 14 | Désignation Majuscule | Désignation en majuscules |
| 15 | Nouvelle Famille Code | Nouveau code hiérarchique |
| 16 | Libellé Activité | Nom de l'activité |
| 17 | Libellé Marque | Nom de la marque |
| 18 | Libellé Famille | Nom de la famille |
| 19 | Libellé Sous-Famille | Nom de la sous-famille |
| 20 | Unité | Unité de mesure |
| 21 | Type Article | Type (DIV, ART, KIT, LOV) |

## Changelog

### Version 2.0.0
- Refonte complète du module
- Ajout des exports Naviwest et QuickDevis
- Création de produits Odoo avec fournisseur
- Détection des articles supprimés du catalogue
- Historique des prix
- Hiérarchie des familles à 5 niveaux
- Actions serveur pour les opérations en masse

### Version 1.0.0
- Version initiale

---

**Auteur** : BYes - Centre GTB LA ROCHE/YON  
**Version** : 2.0.0  
**Compatible** : Odoo 18 Community & Enterprise
