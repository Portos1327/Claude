# QuickDevis 7 - Intégration CRM Complète (v5)

## 🎯 Nouvelle Version - 111 Champs

Cette version **v5** du module ajoute **61 nouveaux champs** pour la synchronisation complète bidirectionnelle.

### 📊 Répartition des champs

| Direction | Nombre | Rôle | Dans Odoo |
|-----------|--------|------|-----------|
| **Odoo → QuickDevis** | 50 | Contexte pour chiffrage | ✏️ Modifiable |
| **QuickDevis → Odoo** | 58 | **NOUVEAU** - Résultats chiffrage | 👁️ Lecture seule |
| **Bidirectionnel** | 2 | Synchronisé 2 sens | ✏️ Modifiable |
| **QuickDevis only** | 1 | Interne QuickDevis | - |
| **TOTAL** | **111** | Synchronisation complète | |

---

## 🔄 PRINCIPE DE FONCTIONNEMENT

### Workflow complet :

```
┌─────────────────────────────────────────────────────────────────┐
│                    1. CRÉATION OPPORTUNITÉ                       │
│   Monday.com → Zapier → Odoo CRM                                │
│   Remplir les 50 champs de contexte (client, projet, contacts)  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              2. SYNCHRONISATION VERS QUICKDEVIS                  │
│   Odoo : Cliquer "Synchroniser vers QuickDevis"                 │
│   → Envoie 50 champs via API REST                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 3. CHIFFRAGE DANS QUICKDEVIS                     │
│   QuickDevis 7 : Entrer le numéro d'opportunité                 │
│   La macro récupère automatiquement les 50 champs d'Odoo        │
│   Utilisateur effectue le chiffrage                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              4. RETOUR RÉSULTATS VERS ODOO                       │
│   QuickDevis : La macro envoie les 58 champs de résultats       │
│   (Prix, quantités, délais, modalités, etc.)                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                5. CONSULTATION DANS ODOO                         │
│   Odoo : Cliquer "Rafraîchir depuis QuickDevis"                 │
│   → Affiche les 58 champs de résultats en lecture seule         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📥 CHAMPS ODOO → QUICKDEVIS (50 champs)

**Ces champs sont remplis dans Odoo et envoyés à QuickDevis au début du devis.**

### Informations Opportunité (11 champs)
- Utilisateur Windows
- Nom opportunité
- Email/Téléphone/Nom du porteur
- Numéro de lot, Référence client
- Monnaie du devis
- Dates début/fin chantier

### Organisation (11 champs)
- Identité SF organisation
- Adresse organisation (lignes 1 & 2)
- Nom agence, Ville, Code postal
- Téléphone, Région
- Unité opérationnelle, Centre de profit

### Contact Principal (14 champs)
- Compte, Nom, Email, Téléphone
- Adresse complète (rue, ville, pays, code postal)
- Département, Fonction, Salutation, État

### Contact Secondaire (14 champs)
- Structure identique au contact principal

---

## 📤 CHAMPS QUICKDEVIS → ODOO (58 champs) **NOUVEAU**

**Ces champs sont remplis par QuickDevis et envoyés à Odoo à la fin du devis.**
**Ils sont en lecture seule dans Odoo.**

### Informations Fichier (3 champs)
- `qdv_sys_filepath` : Répertoire du devis
- `qdv_sys_filename` : Emplacement du fichier devis
- `qdv_sys_version_num` : Version du devis

### Conditions Commerciales (10 champs)
- `qdv_vat` : Taux de TVA
- `qdv_expirationdate` : Date d'expiration
- `qdv_billingmilestone1/2/3` : Modalités de règlement (1, 2, 3)
- `qdv_paymentmethod` : Mode de règlement
- `qdv_paymentterm` : Délai de règlement
- `qdv_warranty` : Garantie
- `qdv_deliverymethod` : Mode de livraison
- `qdv_deliveryterm` : Délai de livraison

### Prix et Quantités (15+ champs)
- `qdv_totalexcltax` : Total HT
- `qdv_totaltax` : Total TVA
- `qdv_totalincltax` : Total TTC
- `qdv_discount` : Remise
- `qdv_margin` : Marge
- `qdv_marginrate` : Taux de marge
- Quantités par catégorie (main d'œuvre, matériaux, équipements, etc.)

### Informations Techniques (15+ champs)
- Durées (heures, jours)
- Surfaces (m², m³)
- Poids (kg, tonnes)
- Longueurs (m, km)
- Et autres unités spécifiques au chiffrage

### Notes et Documents (10+ champs)
- Notes techniques
- Notes commerciales
- Pièces jointes
- Références documents
- Commentaires

---

## 🔧 INSTALLATION

### ⚠️ IMPORTANT - Méthode d'installation

Ce module **NE PEUT PAS** être installé via l'interface "Importer un module" d'Odoo.
Il **DOIT** être installé manuellement dans le répertoire `addons/`.

### Étapes d'installation

1. **Décompresser le ZIP** dans le répertoire addons d'Odoo :

**Windows :**
```
C:\Program Files\Odoo 19.0.20251203\server\addons\qdv_crm_integration\
```

**Linux :**
```
/opt/odoo/addons/qdv_crm_integration/
```

**Docker :**
```
/mnt/extra-addons/qdv_crm_integration/
```

2. **Redémarrer Odoo** (OBLIGATOIRE) :

**Windows :**
```cmd
net stop odoo-server-19.0
net start odoo-server-19.0
```

**Linux :**
```bash
sudo systemctl restart odoo
```

**Docker :**
```bash
docker restart odoo
```

3. **Installer le module** :
   - Applications → Menu ⋮ → Mettre à jour la liste
   - Rechercher : "QuickDevis"
   - Cliquer "Installer"

4. **Vérifier** :
   - CRM → Opportunité → Vérifier onglet "QuickDevis 7"
   - Vérifier les 2 boutons dans le header
   - Vérifier les 3 sections de champs

---

## 📱 UTILISATION

### Dans Odoo

1. **Créer/Ouvrir une opportunité**
2. **Remplir l'onglet "QuickDevis 7"** → Section "📥 Données envoyées à QuickDevis"
3. **Cliquer "Synchroniser vers QuickDevis"**
4. Attendre que QuickDevis envoie les résultats
5. **Cliquer "Rafraîchir depuis QuickDevis"** pour voir les résultats

### Dans QuickDevis 7

1. **Créer un nouveau devis**
2. **Entrer le numéro d'opportunité Odoo**
3. La macro `Communication_With_SalesForce.qdvmacro` récupère automatiquement les données
4. **Effectuer le chiffrage**
5. La macro envoie automatiquement les résultats à Odoo

---

## 🔍 INTERFACE ODOO

### Onglet "QuickDevis 7" - 3 Sections

#### 📥 Section 1 : Données envoyées à QuickDevis (50 champs)
- Alerte bleue : "Ces champs sont remplis dans Odoo et envoyés à QuickDevis"
- Champs **modifiables** dans Odoo
- Organisés en 2 colonnes

#### 📤 Section 2 : Données reçues de QuickDevis (58 champs)
- Alerte verte : "Ces champs sont remplis par QuickDevis (résultats du chiffrage)"
- Champs **en lecture seule** dans Odoo
- Organisés en 2 colonnes

#### ↔️ Section 3 : Champs bidirectionnels (2 champs)
- Modifiables dans Odoo et QuickDevis
- Synchronisés dans les deux sens

### Boutons de synchronisation

Dans le header de l'opportunité :

🔵 **"Synchroniser vers QuickDevis"** (bouton bleu)
- Envoie les 50 champs de contexte
- À utiliser avant de commencer le chiffrage dans QuickDevis

⚪ **"Rafraîchir depuis QuickDevis"** (bouton gris)
- Récupère les 58 champs de résultats
- À utiliser après le chiffrage dans QuickDevis

---

## 🆕 NOUVEAUTÉS VERSION 5

### Ajouts par rapport à v4

✅ **+58 nouveaux champs** QuickDevis → Odoo  
✅ **+2 champs bidirectionnels**  
✅ **+1 champ QuickDevis only**  
✅ Organisation en **3 sections** distinctes  
✅ Champs résultats en **lecture seule** dans Odoo  
✅ Alertes informatives dans chaque section  
✅ **Workflow complet bidirectionnel**  

### Ancien vs Nouveau

| Version | Champs | Direction | Usage |
|---------|--------|-----------|-------|
| **v4** | 50 | Odoo → QuickDevis | Contexte uniquement |
| **v5** | 111 | Bidirectionnel | **Contexte + Résultats** |

---

## 📋 CHECKLIST POST-INSTALLATION

- [ ] Module installé et actif dans Apps
- [ ] Onglet "QuickDevis 7" visible dans opportunités
- [ ] 3 sections visibles (📥 📤 ↔️)
- [ ] 2 boutons dans le header (bleu et gris)
- [ ] Section "Données envoyées" : champs modifiables
- [ ] Section "Données reçues" : champs en lecture seule
- [ ] Test bouton "Synchroniser" : notification verte
- [ ] Test bouton "Rafraîchir" : notification bleue

---

## 🔧 CONFIGURATION TECHNIQUE

### Structure du module

```
qdv_crm_integration/
├── __init__.py
├── __manifest__.py
├── README.md
├── models/
│   ├── __init__.py
│   └── crm_lead.py          # 111 champs + 2 méthodes
└── views/
    └── crm_lead_views.xml   # 3 sections + 2 boutons
```

### Champs dans la base de données

Tous les champs ont le préfixe `qdv_` dans Odoo :

- `qdv_opportunityname` (de GLV_SF_opportunityName)
- `qdv_sys_filepath` (de SYS_FilePath)
- etc.

### API REST

Tous les 111 champs sont accessibles via l'API REST Odoo :

```python
# Lecture
GET /web/dataset/call_kw
model: crm.lead
method: read
fields: [tous les 111 champs qdv_*]

# Écriture
POST /web/dataset/call_kw
model: crm.lead
method: write
args: [[id], {qdv_field: value}]
```

---

## 🚀 PROCHAINES ÉTAPES

### Phase 2 : Adaptation macro QuickDevis (3-5 jours)

1. Créer `ObjFromOdoo.vb` (remplace `ObjFromSF.vb`)
2. Mapper les 111 variables
3. Implémenter :
   - Récupération 50 champs au début
   - Envoi 58 champs à la fin
4. Adapter l'interface utilisateur

### Phase 3 : Tests (2 jours)

1. Test flux complet Odoo → QuickDevis → Odoo
2. Validation des 111 champs
3. Tests de performance

### Phase 4 : Production (1 jour)

1. Déploiement
2. Formation utilisateurs
3. Mise en production

---

## 📞 SUPPORT

### Logs

Les actions de synchronisation sont loguées dans Odoo :

```
Paramètres → Technique → Journaux
Rechercher : "QuickDevis"
```

### Dépannage

**Problème : Les champs "Données reçues" ne se mettent pas à jour**
→ Vérifier que la macro QuickDevis envoie bien les données
→ Cliquer sur "Rafraîchir depuis QuickDevis"

**Problème : Erreur lors de la synchronisation**
→ Vérifier que le module est bien installé (pas juste importé)
→ Vérifier les logs Odoo

---

## 📄 LICENCE

LGPL-3

---

**Version :** 2.0.0  
**Date :** 2025-12-03  
**Auteur :** Votre Entreprise  
