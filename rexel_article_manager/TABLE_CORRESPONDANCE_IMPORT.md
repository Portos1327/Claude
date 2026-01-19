# Table de Correspondance - Import Excel

## Colonnes Excel acceptées pour l'import d'articles

Le module accepte plusieurs formats d'en-têtes Excel. Utilisez l'un des noms de colonne listés pour chaque champ.

| Champ Odoo | Colonnes Excel acceptées | Description |
|------------|--------------------------|-------------|
| `reference_fabricant` | **Référence Fabricant**, Référence, REF | Référence du produit chez le fabricant **(OBLIGATOIRE)** |
| `trigramme_fabricant` | **Trigramme Fabricant**, Code Lidic, CODE_LIDIC | Code 3 lettres (BE4, SCH, LEG, NDX...) |
| `reference_rexel` | **Référence Rexel**, REF_REXEL | Référence complète Rexel (ex: BE491028) |
| `designation` | **Désignation**, DESIGNATION | Libellé du produit |
| `prix_base` | **Prix Base**, Prix de Base, PRIX_BASE | Prix de base (tarif public) |
| `prix_net` | **Prix Net**, PRIX_NET | Prix net client |
| `remise` | **Remise %**, REMISE | Pourcentage de remise |
| `unite_mesure` | **Unité Mesure**, UOM | Unité de mesure (U, ML...) |
| `conditionnement` | **Conditionnement**, CONDITIONNEMENT | Conditionnement de vente |
| `code_ean13` | **Code EAN**, Code EAN13, CODE_EAN13 | Code-barres EAN13 |
| `famille_libelle` | **Famille**, Libellé Famille, LIBELLE_FAMILLE | Libellé de la famille |
| `sous_famille_libelle` | **Sous-Famille**, Libellé Sous Famille, LIBELLE_SOUS_FAMILLE | Libellé de la sous-famille |
| `fonction_libelle` | **Fonction**, Libellé Fonction, LIBELLE_FONCTION | Libellé de la fonction |
| `famille_code` | **Code Famille**, Famille (si numérique), FAMILLE | Code numérique de la famille |
| `sous_famille_code` | **Code Sous-Famille**, Sous Famille, SOUS_FAMILLE | Code numérique de la sous-famille |
| `fonction_code` | **Code Fonction**, Fonction (si numé