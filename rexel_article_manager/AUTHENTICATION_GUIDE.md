# 🔐 GUIDE D'AUTHENTIFICATION API REXEL CLOUD

## 📋 Informations d'authentification

### 🌍 Environnement de Production

**OAuth2 Microsoft Azure**
```
Tenant ID: 822cd975-5643-4b7e-b398-69a164e55719
Client ID: 4036c6d5-fce1-4569-a177-072a4e45bd39
Client Secret: bhk8Q~vzGGx2rzDXnonyVVlkTAoYZ4tdu7.rmc38
Scope: aee2ba94-a840-453a-9151-1355638ac04e/.default
```

**API Rexel**
```
URL Base: https://api.rexel.fr
Clé d'abonnement: e9fa63ce8d934beb83c5a1f94817983a
Mot client: TURQUAND
```

## 🔄 Flux d'authentification

### 1. Obtention du Token OAuth2

```http
POST https://login.microsoftonline.com/822cd975-5643-4b7e-b398-69a164e55719/oauth2/v2.0/token/

Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
&client_id=4036c6d5-fce1-4569-a177-072a4e45bd39
&client_secret=bhk8Q~vzGGx2rzDXnonyVVlkTAoYZ4tdu7.rmc38
&scope=aee2ba94-a840-453a-9151-1355638ac04e/.default
```

**Réponse** :
```json
{
  "token_type": "Bearer",
  "expires_in": 3599,
  "ext_expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### 2. Utilisation du Token

**Headers requis pour chaque appel API** :
```http
Authorization: Bearer {access_token}
Ocp-Apim-Subscription-Key: e9fa63ce8d934beb83c5a1f94817983a
Content-Type: application/json
```

## ⚙️ Configuration dans Odoo

### Via l'interface

```
Menu → Configuration → Configuration Rexel

┌─────────────────────────────────────────────────────────────┐
│ 🔐 AUTHENTIFICATION OAUTH2 MICROSOFT                        │
├─────────────────────────────────────────────────────────────┤
│ Tenant ID Azure:                                            │
│ 822cd975-5643-4b7e-b398-69a164e55719                        │
│                                                             │
│ Client ID:                                                  │
│ 4036c6d5-fce1-4569-a177-072a4e45bd39                        │
│                                                             │
│ Client Secret: ⚠️ SENSIBLE                                  │
│ bhk8Q~vzGGx2rzDXnonyVVlkTAoYZ4tdu7.rmc38                    │
│                                                             │
│ Scope OAuth:                                                │
│ aee2ba94-a840-453a-9151-1355638ac04e/.default               │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ 🔌 API REXEL                                                │
├─────────────────────────────────────────────────────────────┤
│ URL de base API:                                            │
│ https://api.rexel.fr                                        │
│                                                             │
│ Clé d'abonnement:                                           │
│ e9fa63ce8d934beb83c5a1f94817983a                            │
│                                                             │
│ Mot client:                                                 │
│ TURQUAND                                                    │
│                                                             │
│ N° client Rexel:                                            │
│ [À compléter - 7 chiffres]                                  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [Tester la connexion API]                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Test de connexion

### Test réussi
```
✅ Connexion réussie
API Rexel opérationnelle
Client: [Nom du client]
Token OAuth2 valide jusqu'à 2025-12-17 14:30:00
```

### Erreurs possibles

#### Erreur OAuth2
```
❌ Erreur OAuth2: 401 - Unauthorized
→ Vérifier Client ID et Client Secret
→ Vérifier que le Tenant ID est correct
```

#### Erreur API
```
❌ Erreur HTTP 403 - Forbidden
→ Vérifier la clé d'abonnement
→ Vérifier que le scope est correct
```

#### Erreur Client
```
❌ Erreur HTTP 404 - Customer not found
→ Vérifier le N° client Rexel (7 chiffres)
→ Vérifier le mot client (TURQUAND)
```

## 🔄 Gestion automatique du Token

Le module gère automatiquement :

1. **Obtention du token** : Lors du premier appel API
2. **Rafraîchissement** : Automatique 5 minutes avant expiration
3. **Stockage sécurisé** : Token stocké dans la config
4. **Réutilisation** : Token réutilisé tant qu'il est valide

### Cycle de vie du token

```
┌──────────────────────────────────────────────────────────┐
│ 1. Premier appel API                                     │
│    → Pas de token ou token expiré                        │
│    → Appel OAuth2 Microsoft                              │
│    → Stockage token + expiration                         │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ 2. Appels suivants (< 55 minutes)                        │
│    → Token valide existant                               │
│    → Réutilisation directe                               │
└──────────────────────────────────────────────────────────┘
              ↓
┌──────────────────────────────────────────────────────────┐
│ 3. Après 55 minutes                                      │
│    → Token proche de l'expiration                        │
│    → Renouvellement automatique                          │
└──────────────────────────────────────────────────────────┘
```

## 🛡️ Sécurité

### ⚠️ Client Secret

Le Client Secret est **sensible** :
- ❌ Ne jamais le partager publiquement
- ❌ Ne jamais le commiter dans Git
- ✅ Le stocker uniquement dans la configuration Odoo
- ✅ Limiter l'accès au menu Configuration

### 🔒 Permissions Odoo

Restreindre l'accès à la configuration :

```xml
<record id="group_rexel_admin" model="res.groups">
    <field name="name">Rexel Administrator</field>
</record>
```

## 📊 Monitoring

### Statistiques API

La configuration Rexel enregistre :
- **Dernier appel API** : Date/heure du dernier appel
- **Nombre d'appels** : Compteur total d'appels
- **Dernière erreur** : Message d'erreur si échec
- **Token valide jusqu'à** : Date d'expiration du token actuel

### Logs

Les appels API sont loggés dans :
```
Menu → Configuration → Logs
Filtre : [rexel_config]
```

## 🔧 Dépannage

### Token non obtenu

```python
# Vérifier manuellement
from odoo import api, SUPERUSER_ID

env = api.Environment(cr, SUPERUSER_ID, {})
config = env['rexel.config'].get_config()
token = config._get_access_token()
print(f"Token: {token[:50]}...")
```

### Test direct OAuth2

```bash
curl -X POST \
  https://login.microsoftonline.com/822cd975-5643-4b7e-b398-69a164e55719/oauth2/v2.0/token/ \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'grant_type=client_credentials' \
  -d 'client_id=4036c6d5-fce1-4569-a177-072a4e45bd39' \
  -d 'client_secret=bhk8Q~vzGGx2rzDXnonyVVlkTAoYZ4tdu7.rmc38' \
  -d 'scope=aee2ba94-a840-453a-9151-1355638ac04e/.default'
```

### Test direct API Rexel

```bash
# 1. Obtenir le token
TOKEN="[token obtenu ci-dessus]"

# 2. Tester l'API Customers
curl -X GET \
  https://api.rexel.fr/external/customers/[NUMERO_CLIENT] \
  -H "Authorization: Bearer $TOKEN" \
  -H "Ocp-Apim-Subscription-Key: e9fa63ce8d934beb83c5a1f94817983a"
```

## 📚 Références

- [Documentation OAuth2 Microsoft](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
- [Documentation API Rexel](Documentation_API.pdf)
- [Postman Collection](get_token.json)

## 🎯 Checklist de configuration

- [ ] Tenant ID configuré
- [ ] Client ID configuré
- [ ] Client Secret configuré (⚠️ sensible)
- [ ] Scope OAuth configuré
- [ ] URL API configurée
- [ ] Clé d'abonnement configurée
- [ ] Mot client configuré (TURQUAND)
- [ ] N° client Rexel configuré
- [ ] API activée
- [ ] Test de connexion réussi

## 🚀 Utilisation

Une fois configuré, le module gère tout automatiquement :

1. **Import prix** : `Menu → Import / Export → Mettre à jour les prix`
2. **Token OAuth2** : Obtenu et rafraîchi automatiquement
3. **Headers API** : Construits automatiquement avec token + clé

Aucune intervention manuelle nécessaire ! 🎉
