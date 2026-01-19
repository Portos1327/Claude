# 🚀 DÉMARRAGE RAPIDE - REXEL v4.0 AVEC OAuth2

## ⚡ Installation en 5 minutes

### 1️⃣ Installer le module (2 min)

```bash
# Extraire l'archive
unzip rexel_v4_cloud_oauth.zip

# Copier vers Odoo
cp -r rexel_v4 /path/to/odoo/addons/rexel_article_manager

# Redémarrer Odoo
sudo service odoo restart
```

### 2️⃣ Activer dans Odoo (1 min)

```
1. Applications → Mettre à jour la liste
2. Rechercher "Rexel"
3. Cliquer "Installer"
```

### 3️⃣ Configurer l'API (2 min)

```
Menu → Configuration → Configuration Rexel
```

**Copier-coller ces valeurs** (PRODUCTION - Pack Découverte) :

```
☑ API activée

┌─ OAUTH2 MICROSOFT ────────────────────────────────────┐
│ Tenant ID:                                            │
│ 822cd975-5643-4b7e-b398-69a164e55719                  │
│                                                       │
│ Client ID:                                            │
│ 4036c6d5-fce1-4569-a177-072a4e45bd39                  │
│                                                       │
│ Client Secret: ⚠️                                     │
│ bhk8Q~vzGGx2rzDXnonyVVlkTAoYZ4tdu7.rmc38              │
│                                                       │
│ Scope OAuth:                                          │
│ aee2ba94-a840-453a-9151-1355638ac04e/.default         │
└───────────────────────────────────────────────────────┘

┌─ API REXEL ───────────────────────────────────────────┐
│ URL de base API:                                      │
│ https://api.rexel.fr                                  │
│                                                       │
│ Clé d'abonnement:                                     │
│ e9fa63ce8d934beb83c5a1f94817983a                      │
│                                                       │
│ Mot client:                                           │
│ TURQUAND                                              │
│                                                       │
│ N° client Rexel: (⚠️ À COMPLÉTER)                     │
│ [Votre numéro à 7 chiffres]                           │
└───────────────────────────────────────────────────────┘

[Tester la connexion API]
```

### 4️⃣ Tester (30 sec)

Cliquer sur **"Tester la connexion API"**

✅ **Si succès** :
```
✅ Connexion réussie
API Rexel opérationnelle
Client: [Votre nom]
Token OAuth2 valide jusqu'à [date/heure]
```

❌ **Si erreur** :
- Vérifier le N° client Rexel (7 chiffres)
- Vérifier que tous les champs sont bien copiés

---

## 📥 Premier Import

### Depuis Excel Cloud Rexel

```
1. Menu → Import / Export → Importer depuis Excel/API

2. Mode: "Importer depuis un fichier Excel"

3. [Sélectionner votre fichier cloud Rexel]

4. Options:
   ☑ Mettre à jour les articles existants
   ☐ Créer automatiquement les produits Odoo

5. [Importer]

6. ✅ Résultats:
   - Articles importés: X
   - Articles mis à jour: Y
   - Hiérarchie reconstruite automatiquement
```

---

## 💰 Mise à jour des Prix via API

### Automatique via API Rexel

```
1. Menu → Import / Export → Mettre à jour les prix

2. Mode: "Tous les articles"

3. Options:
   ☑ Créer historique des prix
   ☐ Mettre à jour les produits Odoo

4. [Mettre à jour]

5. ✅ Résultats:
   - Articles mis à jour: X
   - Prix modifiés: Y
   - Token OAuth2 géré automatiquement !
```

---

## 🌳 Visualiser la Hiérarchie

```
1. Menu → Articles → Hiérarchie des familles

2. Cliquer sur ⚙️ (Actions)

3. Sélectionner "🔄 Reconstruire la hiérarchie"

4. ✅ Explorer l'arborescence à 5 niveaux
```

---

## 📊 Format du Fichier Excel Cloud

Votre fichier doit contenir ces colonnes :

| Obligatoires     | Optionnelles          |
|------------------|-----------------------|
| REF              | REF_REXEL             |
| DESIGNATION      | CODE_EAN13            |
| PRIX_NET         | DATE_TARIF            |
| UOM ⭐            | CONDITIONNEMENT       |
| CODE_LIDIC       | ECOSCORE              |
| LIBELLE_FABRICANT| SELECTION_DURABLE     |
|                  | URL_IMAGE             |
|                  | Écotaxe D3E (5 cols)  |

⭐ **UOM** = Unité de mesure (U, M, KG, L, BOI, ROU, SAC...)

---

## 🔐 Authentification OAuth2

### C'est automatique ! 🎉

Le module gère **tout seul** :
1. ✅ Obtention du token OAuth2
2. ✅ Rafraîchissement avant expiration
3. ✅ Ajout des headers API
4. ✅ Gestion des erreurs

**Vous n'avez rien à faire !**

### Vérifier le token actuel

```
Menu → Configuration → Configuration Rexel

Voir en bas:
- Access Token: eyJ0eXAiOiJKV1Q...
- Token expire le: 2025-12-17 14:30:00
```

---

## ⚙️ Chemins Templates (pour exports)

Si vous voulez utiliser les exports Naviwest/QuickDevis :

```
1. Créer le dossier:
   C:\Program Files\Odoo 18.0.20251211\server\templates\

2. Y copier les 4 fichiers template:
   - MAJ Base_Article - BEG avec formules V1.xlsx
   - MAJ Base_Article - NIEDAX avec formules V1.xlsx
   - MAJ Base_Article - CABLES avec formules V1.xlsx
   - Tarif câbles net rexel oct 2025 V2.xlsx

3. Dans Configuration Rexel:
   [Vérifier les templates]
```

---

## 🎯 Cas d'usage courants

### Import initial
```
Excel → Import → Tous les articles importés
```

### Mise à jour quotidienne des prix
```
API → Mise à jour prix → Historique créé automatiquement
```

### Créer les produits Odoo
```
Articles → Sélectionner → Action → Créer produits Odoo
```

### Export vers Naviwest
```
Articles → Sélectionner → Exporter vers Naviwest → BEG
```

---

## 🆘 Dépannage Express

### Erreur OAuth2 401
```
→ Vérifier Client ID et Client Secret
→ Recopier exactement (pas d'espace)
```

### Erreur API 403
```
→ Vérifier la clé d'abonnement
→ Vérifier le mot client (TURQUAND)
```

### Erreur 404 Customer
```
→ Vérifier le N° client Rexel (7 chiffres)
```

### Unités manquantes
```
→ Vérifier la colonne UOM dans l'Excel
→ Valeurs acceptées: U, M, KG, L, BOI, ROU, SAC, PAQ, ENS
```

---

## 📚 Documentation Complète

- [README.md](README.md) - Guide utilisateur complet
- [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md) - Détails OAuth2
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration v3→v4
- [SYNTHESE_TECHNIQUE.md](SYNTHESE_TECHNIQUE.md) - Pour développeurs

---

## ✅ Checklist Installation

- [ ] Module installé dans Odoo
- [ ] Configuration OAuth2 complétée
- [ ] N° client Rexel configuré
- [ ] Test connexion API réussi
- [ ] Premier import Excel effectué
- [ ] Hiérarchie reconstruite
- [ ] Test mise à jour prix API OK

---

## 🎉 Vous êtes prêt !

**Le module est maintenant opérationnel.**

### Prochaines étapes

1. Importer votre catalogue complet
2. Programmer la mise à jour quotidienne des prix
3. Créer les produits Odoo pour les ventes
4. Explorer la hiérarchie

### Support

En cas de problème :
1. Consulter [AUTHENTICATION_GUIDE.md](AUTHENTICATION_GUIDE.md)
2. Vérifier les logs Odoo
3. Tester la connexion API
4. Vérifier le format du fichier Excel

---

**Version** : 4.0.0 OAuth2  
**Date** : Décembre 2025  
**Pack** : Découverte (Production)  
**Mot client** : TURQUAND  
