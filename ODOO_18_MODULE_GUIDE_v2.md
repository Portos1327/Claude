# 🐍 Fondamentaux de la Création d'un Module Personnalisé Odoo 18

**Guide de Référence - BYes Centre GTB LA ROCHE/YON**  
**Version 2.0 - Janvier 2026**

> 📋 **Environnement de Référence** : Odoo 18 Community • Windows • Python Embarqué

---

## 📑 Table des Matières

1. [Architecture d'un Module](#1-architecture-dun-module-odoo-18)
2. [Définition des Modèles (ORM)](#2-définition-des-modèles-orm)
3. [Définition des Vues XML](#3-définition-des-vues-xml)
4. [Sécurité et Droits d'Accès](#4-sécurité-et-droits-daccès)
5. [Décorateurs et Méthodes API](#5-décorateurs-et-méthodes-api)
6. [Environnement Windows](#6-environnement-windows-avec-python-embarqué)
7. [Tests Unitaires et Validation](#7-tests-unitaires-et-validation) ⭐ NOUVEAU
8. [Optimisation des Performances](#8-optimisation-des-performances) ⭐ NOUVEAU
9. [Checklist de Validation](#9-checklist-de-validation)

---

## 1. Architecture d'un Module Odoo 18

### 1.1 Structure de Fichiers Obligatoire

```
mon_module/
├── __init__.py              # Import des sous-modules
├── __manifest__.py          # Métadonnées du module
├── models/
│   ├── __init__.py
│   └── mon_modele.py        # Définition des modèles
├── views/
│   ├── mon_modele_views.xml # Vues formulaire, liste, etc.
│   └── menu_views.xml       # Menus et actions
├── security/
│   └── ir.model.access.csv  # Droits d'accès
├── tests/                   # ⭐ Tests unitaires
│   ├── __init__.py
│   └── test_mon_modele.py
├── wizard/                  # Assistants (optionnel)
├── data/                    # Données initiales (optionnel)
├── static/                  # Ressources statiques
│   └── description/
│       └── icon.png         # Icône du module (128x128)
└── i18n/                    # Traductions (optionnel)
```

### 1.2 Le Fichier `__manifest__.py`

```python
# -*- coding: utf-8 -*-
{
    'name': 'Mon Module',
    'version': '18.0.1.0.0',  # Format: ODOO.MODULE.MAJOR.MINOR.PATCH
    'category': 'Sales',
    'summary': 'Description courte du module',
    'description': '''
        Description détaillée du module.
    ''',
    'author': 'BYes - Centre GTB',
    'website': 'https://www.byes.fr',
    'depends': ['base', 'product', 'purchase'],
    'data': [
        'security/ir.model.access.csv',  # TOUJOURS EN PREMIER
        'views/mon_modele_views.xml',
        'views/menu_views.xml',          # MENUS EN DERNIER
    ],
    'installable': True,
    'application': True,  # True = apparaît dans Apps
    'auto_install': False,
    'license': 'LGPL-3',
}
```

> ⚠️ **ORDRE CRITIQUE dans 'data':**
> 1. `security/` (droits d'accès)
> 2. `data/` (données de référence)
> 3. `wizard/` (assistants)
> 4. `views/` (vues des modèles)
> 5. `menu_views.xml` (menus EN DERNIER)

---

## 2. Définition des Modèles (ORM)

### 2.1 Structure de Base d'un Modèle

```python
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class MonModele(models.Model):
    _name = 'mon.modele'              # Nom technique (obligatoire)
    _description = 'Mon Modèle'       # Description (obligatoire)
    _inherit = ['mail.thread']        # Héritage (optionnel)
    _order = 'name asc'               # Tri par défaut
    _rec_name = 'name'                # Champ d'affichage

    # Champs
    name = fields.Char(string='Nom', required=True)
    active = fields.Boolean(default=True)
```

### 2.2 Types de Champs Disponibles

| Type | Exemple d'utilisation |
|------|----------------------|
| `Char` | `fields.Char(string='Nom', size=128)` |
| `Text` | `fields.Text(string='Description')` |
| `Integer` | `fields.Integer(string='Quantité', default=0)` |
| `Float` | `fields.Float(string='Prix', digits=(10, 2))` |
| `Monetary` | `fields.Monetary(string='Montant', currency_field='currency_id')` |
| `Boolean` | `fields.Boolean(string='Actif', default=True)` |
| `Date` | `fields.Date(string='Date', default=fields.Date.today)` |
| `Datetime` | `fields.Datetime(default=fields.Datetime.now)` |
| `Selection` | `fields.Selection([('draft','Brouillon'),('done','Fait')])` |
| `Many2one` | `fields.Many2one('res.partner', string='Client')` |
| `One2many` | `fields.One2many('ligne.modele', 'parent_id', string='Lignes')` |
| `Many2many` | `fields.Many2many('product.tag', string='Tags')` |

### 2.3 Champs Calculés et Dépendances

```python
# Champ calculé avec dépendances
total = fields.Float(
    string='Total',
    compute='_compute_total',
    store=True  # Stocker en base pour performance
)

@api.depends('quantity', 'price')
def _compute_total(self):
    for record in self:
        record.total = record.quantity * record.price
```

### ✅ ODOO 18 - Remplacer `name_get()` par `_compute_display_name`

```python
# ❌ ANCIEN (déprécié)
def name_get(self):
    return [(r.id, f'[{r.code}] {r.name}') for r in self]

# ✅ NOUVEAU (Odoo 18)
@api.depends('code', 'name')
def _compute_display_name(self):
    for record in self:
        record.display_name = f'[{record.code}] {record.name}'
```

---

## 3. Définition des Vues XML

### 3.1 Vue Liste (`list`)

> **Odoo 18** utilise `<list>` au lieu de `<tree>` (bien que `tree` fonctionne encore).

```xml
<record id="view_mon_modele_list" model="ir.ui.view">
    <field name="name">mon.modele.list</field>
    <field name="model">mon.modele</field>
    <field name="arch" type="xml">
        <list string="Mon Modèle">
            <field name="name"/>
            <field name="date"/>
            <field name="state" widget="badge"/>
            <field name="total" sum="Total"/>
        </list>
    </field>
</record>
```

### 3.2 Vue Formulaire (`form`)

```xml
<record id="view_mon_modele_form" model="ir.ui.view">
    <field name="name">mon.modele.form</field>
    <field name="model">mon.modele</field>
    <field name="arch" type="xml">
        <form string="Mon Modèle">
            <header>
                <button name="action_confirm" string="Confirmer"
                        type="object" class="btn-primary"/>
                <field name="state" widget="statusbar"/>
            </header>
            <sheet>
                <group>
                    <group string="Informations">
                        <field name="name"/>
                        <field name="partner_id"/>
                    </group>
                    <group string="Détails">
                        <field name="date"/>
                        <field name="total"/>
                    </group>
                </group>
                <notebook>
                    <page string="Lignes" name="lines">
                        <field name="line_ids"/>
                    </page>
                </notebook>
            </sheet>
            <chatter/> <!-- Si mail.thread hérité -->
        </form>
    </field>
</record>
```

### 3.3 Vue Recherche (`search`)

```xml
<record id="view_mon_modele_search" model="ir.ui.view">
    <field name="name">mon.modele.search</field>
    <field name="model">mon.modele</field>
    <field name="arch" type="xml">
        <search string="Recherche">
            <field name="name"/>
            <field name="partner_id"/>
            <filter name="filter_active" string="Actifs" domain="[('active','=',True)]"/>
            <group expand="0" string="Grouper par">
                <filter name="group_state" string="État" context="{'group_by':'state'}"/>
            </group>
        </search>
    </field>
</record>
```

### 📋 Widgets natifs Odoo 18 recommandés

- `widget="badge"` - Affichage en badge coloré
- `widget="statusbar"` - Barre d'état
- `widget="many2many_tags"` - Tags pour Many2many
- `widget="url"` - Lien cliquable
- `widget="image"` - Affichage d'image
- `widget="progressbar"` - Barre de progression
- `widget="float_time"` - Durée en heures:minutes

---

## 4. Sécurité et Droits d'Accès

### 4.1 Fichier `ir.model.access.csv`

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_mon_modele_user,mon.modele.user,model_mon_modele,base.group_user,1,1,1,0
access_mon_modele_manager,mon.modele.manager,model_mon_modele,base.group_system,1,1,1,1
```

| Colonne | Description |
|---------|-------------|
| `id` | Identifiant externe unique (ex: access_mon_modele_user) |
| `model_id:id` | Modèle concerné (model_nom_modele avec `.` remplacé par `_`) |
| `group_id:id` | Groupe Odoo (base.group_user, base.group_system, etc.) |
| `perm_read/write/create/unlink` | 1 = autorisé, 0 = refusé |

### 4.2 Contraintes SQL

```python
_sql_constraints = [
    ('unique_reference', 
     'UNIQUE(reference_fabricant)', 
     'La référence fabricant doit être unique !'),
    ('check_quantity_positive',
     'CHECK(quantity >= 0)',
     'La quantité doit être positive !'),
]
```

---

## 5. Décorateurs et Méthodes API

### 5.1 Décorateurs Principaux

| Décorateur | Usage |
|------------|-------|
| `@api.depends()` | Champs calculés - déclenche le recalcul quand les dépendances changent |
| `@api.onchange()` | Réaction temps réel dans le formulaire (avant sauvegarde) |
| `@api.constrains()` | Validation Python - lève ValidationError si invalide |
| `@api.model` | Méthode de classe (pas d'enregistrement spécifique) |
| `@api.model_create_multi` | **Odoo 18** : Surcharge de create() pour création batch |

### 5.2 Surcharge des Méthodes CRUD

```python
# Surcharge de create() - Odoo 18
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('mon.modele')
    return super().create(vals_list)

# Surcharge de write()
def write(self, vals):
    if 'state' in vals and vals['state'] == 'done':
        vals['date_done'] = fields.Datetime.now()
    return super().write(vals)

# Surcharge de unlink()
def unlink(self):
    for record in self:
        if record.state == 'done':
            raise UserError(_('Impossible de supprimer un enregistrement validé.'))
    return super().unlink()
```

### 5.3 Validation avec @api.constrains

```python
@api.constrains('quantity', 'price')
def _check_values(self):
    for record in self:
        if record.quantity < 0:
            raise ValidationError(_('La quantité doit être positive.'))
        if record.price < 0:
            raise ValidationError(_('Le prix doit être positif.'))
```

---

## 6. Environnement Windows avec Python Embarqué

### 6.1 Installation de Packages Python

Odoo Windows utilise un Python embarqué. Les packages doivent être installés dedans :

```cmd
# Chemin du Python Odoo 18 (à adapter selon version)
cd "C:\Program Files\Odoo 18.0.20251211\python"

# Installation d'un package (ex: phonenumbers)
.\python.exe -m pip install phonenumbers --break-system-packages

# Installation openpyxl pour Excel
.\python.exe -m pip install openpyxl --break-system-packages
```

> ⚠️ **IMPORTANT** : Exécuter en **Administrateur** car l'installation dans Program Files nécessite des droits élevés.

### 6.2 Redémarrage du Service Odoo

```cmd
# CMD en Administrateur
net stop "Odoo 18"
net start "Odoo 18"

# Ou via PowerShell
Restart-Service -Name "Odoo 18"
```

### 6.3 Mise à Jour d'un Module

1. Ouvrir Odoo : `http://localhost:8069`
2. Applications → Retirer le filtre "Apps"
3. Rechercher le module
4. Cliquer sur ⋮ (3 points) → **Mettre à jour**

### 6.4 Logs et Débogage

```cmd
# Voir les logs en temps réel
type "C:\Program Files\Odoo 18.0.20251211\server\odoo.log"

# Ou via PowerShell
Get-Content "C:\Program Files\Odoo 18.0.20251211\server\odoo.log" -Tail 100 -Wait
```

---

## 7. Tests Unitaires et Validation

### 7.1 Structure des Tests

Les tests doivent être placés dans le dossier `tests/` du module :

```
mon_module/
└── tests/
    ├── __init__.py
    ├── test_mon_modele.py
    └── test_api_sync.py
```

**Fichier `tests/__init__.py`** :
```python
from . import test_mon_modele
from . import test_api_sync
```

### 7.2 Classes de Test Odoo 18

| Classe | Usage |
|--------|-------|
| `TransactionCase` | **Recommandé** - Chaque test dans une transaction séparée (rollback automatique) |
| `HttpCase` | Tests d'interface web avec navigateur headless |
| `Form` | Simulation de formulaires côté serveur |

### 7.3 Exemple Complet de Test Unitaire

```python
# tests/test_mon_modele.py
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError
from unittest.mock import patch, MagicMock
import logging

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestMonModele(TransactionCase):
    """Tests pour le modèle mon.modele"""

    @classmethod
    def setUpClass(cls):
        """Configuration initiale - exécutée une seule fois"""
        super(TestMonModele, cls).setUpClass()
        
        # Créer des données de test
        cls.partner = cls.env['res.partner'].create({
            'name': 'Client Test',
            'email': 'test@example.com',
        })
        
        cls.product = cls.env['product.product'].create({
            'name': 'Produit Test',
            'default_code': 'TEST001',
            'list_price': 100.0,
        })

    def test_01_create_record(self):
        """Test de création d'un enregistrement"""
        record = self.env['mon.modele'].create({
            'name': 'Test Record',
            'partner_id': self.partner.id,
            'quantity': 10,
            'price': 50.0,
        })
        
        self.assertTrue(record.id, "L'enregistrement doit être créé")
        self.assertEqual(record.name, 'Test Record')
        self.assertEqual(record.total, 500.0, "Total = quantity * price")

    def test_02_compute_total(self):
        """Test du calcul automatique du total"""
        record = self.env['mon.modele'].create({
            'name': 'Test Compute',
            'quantity': 5,
            'price': 20.0,
        })
        
        self.assertEqual(record.total, 100.0)
        
        # Modifier la quantité
        record.write({'quantity': 10})
        self.assertEqual(record.total, 200.0, "Le total doit se recalculer")

    def test_03_validation_quantity_positive(self):
        """Test de la contrainte quantité positive"""
        with self.assertRaises(ValidationError):
            self.env['mon.modele'].create({
                'name': 'Test Négatif',
                'quantity': -5,
                'price': 10.0,
            })

    def test_04_unlink_protection(self):
        """Test de protection contre la suppression"""
        record = self.env['mon.modele'].create({
            'name': 'Test Delete',
            'state': 'done',  # Enregistrement validé
        })
        
        with self.assertRaises(UserError):
            record.unlink()

    def test_05_search_and_filter(self):
        """Test de recherche et filtrage"""
        # Créer plusieurs enregistrements
        records = self.env['mon.modele'].create([
            {'name': 'Record A', 'state': 'draft'},
            {'name': 'Record B', 'state': 'done'},
            {'name': 'Record C', 'state': 'draft'},
        ])
        
        # Rechercher les brouillons
        drafts = self.env['mon.modele'].search([('state', '=', 'draft')])
        self.assertGreaterEqual(len(drafts), 2)

    def test_06_display_name(self):
        """Test du nom d'affichage personnalisé"""
        record = self.env['mon.modele'].create({
            'name': 'Test Display',
            'code': 'TD001',
        })
        
        expected = '[TD001] Test Display'
        self.assertEqual(record.display_name, expected)


@tagged('post_install', '-at_install')
class TestApiSync(TransactionCase):
    """Tests pour la synchronisation API"""

    @classmethod
    def setUpClass(cls):
        super(TestApiSync, cls).setUpClass()
        cls.sync_model = cls.env['mon.modele.sync']

    @patch('requests.get')
    def test_01_api_call_success(self, mock_get):
        """Test d'appel API réussi avec mock"""
        # Simuler une réponse API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'articles': [
                {'code': 'ART001', 'name': 'Article 1', 'price': 10.0},
                {'code': 'ART002', 'name': 'Article 2', 'price': 20.0},
            ]
        }
        mock_get.return_value = mock_response
        
        # Exécuter la synchronisation
        result = self.sync_model.sync_articles()
        
        # Vérifier
        self.assertTrue(result.get('success'))
        self.assertEqual(result.get('count'), 2)

    @patch('requests.get')
    def test_02_api_call_error(self, mock_get):
        """Test de gestion d'erreur API"""
        mock_get.side_effect = Exception("Connection timeout")
        
        # La méthode doit gérer l'erreur gracieusement
        result = self.sync_model.sync_articles()
        
        self.assertFalse(result.get('success'))
        self.assertIn('error', result)

    def test_03_batch_create_performance(self):
        """Test de performance pour création batch"""
        import time
        
        # Préparer 100 enregistrements
        vals_list = [
            {'name': f'Batch Record {i}', 'code': f'BATCH{i:04d}'}
            for i in range(100)
        ]
        
        start_time = time.time()
        records = self.env['mon.modele'].create(vals_list)
        elapsed = time.time() - start_time
        
        self.assertEqual(len(records), 100)
        self.assertLess(elapsed, 5.0, "Création batch doit être < 5 secondes")
        _logger.info(f"Création de 100 enregistrements en {elapsed:.2f}s")
```

### 7.4 Test de Formulaire (Server-Side Form)

```python
from odoo.tests import Form

def test_form_onchange(self):
    """Test des onchange via formulaire"""
    with Form(self.env['mon.modele']) as form:
        form.name = 'Test Form'
        form.partner_id = self.partner
        
        # Vérifier que l'onchange a été déclenché
        self.assertEqual(form.partner_email, self.partner.email)
        
        # Sauvegarder
        record = form.save()
    
    self.assertTrue(record.id)
```

### 7.5 Lancer les Tests

**Via ligne de commande Windows :**

```cmd
# Tester un module spécifique
"C:\Program Files\Odoo 18.0.20251211\python\python.exe" ^
    "C:\Program Files\Odoo 18.0.20251211\server\odoo-bin" ^
    -c "C:\Program Files\Odoo 18.0.20251211\server\odoo.conf" ^
    -d ma_base ^
    --test-tags /mon_module ^
    --stop-after-init

# Tester avec filtre sur classe
--test-tags /mon_module:TestMonModele

# Tester une méthode spécifique
--test-tags /mon_module:TestMonModele.test_01_create_record
```

**Options importantes :**

| Option | Description |
|--------|-------------|
| `--test-enable` | Active les tests |
| `--test-tags` | Filtre les tests à exécuter |
| `--stop-after-init` | Arrête Odoo après les tests |
| `-d database` | Base de données de test |
| `--log-level=test` | Niveau de log pour voir les résultats |

### 7.6 Tags de Test

```python
from odoo.tests import tagged

# Test exécuté après installation de tous les modules
@tagged('post_install', '-at_install')
class TestPostInstall(TransactionCase):
    pass

# Test exécuté pendant l'installation du module
@tagged('at_install')
class TestAtInstall(TransactionCase):
    pass

# Tag personnalisé pour tests longs
@tagged('post_install', '-at_install', 'slow')
class TestSlow(TransactionCase):
    pass

# Exclure des tests standard
@tagged('-standard', 'custom')
class TestCustom(TransactionCase):
    pass
```

### 7.7 Bonnes Pratiques de Test

1. **Isolation** : Chaque test doit être indépendant
2. **Nommage** : Préfixer par numéro pour l'ordre (`test_01_`, `test_02_`)
3. **Assertions claires** : Messages explicites dans les asserts
4. **Mock API externes** : Ne jamais appeler de vraies API en test
5. **setUpClass** : Créer les données communes une seule fois
6. **Couverture** : Tester les cas normaux ET les erreurs

---

## 8. Optimisation des Performances

### 8.1 Problème N+1 Queries

Le problème le plus fréquent : exécuter une requête par enregistrement dans une boucle.

```python
# ❌ MAUVAIS - N+1 queries (1 requête par partenaire)
for partner in partners:
    orders = self.env['sale.order'].search([
        ('partner_id', '=', partner.id)
    ])
    partner.order_count = len(orders)

# ✅ BON - 1 seule requête avec read_group
data = self.env['sale.order']._read_group(
    domain=[('partner_id', 'in', partners.ids)],
    groupby=['partner_id'],
    aggregates=['__count'],
)
count_map = {partner.id: count for partner, count in data}
for partner in partners:
    partner.order_count = count_map.get(partner.id, 0)
```

### 8.2 Création en Batch

```python
# ❌ MAUVAIS - N créations = N transactions
for name in names:
    self.env['product.product'].create({'name': name})

# ✅ BON - 1 seule transaction
vals_list = [{'name': name} for name in names]
self.env['product.product'].create(vals_list)
```

### 8.3 Utiliser `search_read()` au lieu de `search()` + `read()`

```python
# ❌ MAUVAIS - 2 requêtes
records = self.env['product.product'].search([('active', '=', True)])
data = records.read(['name', 'default_code', 'list_price'])

# ✅ BON - 1 seule requête
data = self.env['product.product'].search_read(
    domain=[('active', '=', True)],
    fields=['name', 'default_code', 'list_price'],
    limit=500
)
```

### 8.4 Champs Calculés Stockés

```python
# ❌ MAUVAIS - Recalculé à chaque affichage
total = fields.Float(compute='_compute_total')

# ✅ BON - Stocké en base, recalculé uniquement si dépendances changent
total = fields.Float(
    compute='_compute_total',
    store=True  # Stocké en base de données
)

@api.depends('line_ids.price', 'line_ids.quantity')
def _compute_total(self):
    for record in self:
        record.total = sum(
            line.price * line.quantity 
            for line in record.line_ids
        )
```

### 8.5 Index sur les Champs Fréquemment Recherchés

```python
class MonModele(models.Model):
    _name = 'mon.modele'
    
    # Index simple pour recherches fréquentes
    reference = fields.Char(index=True)
    
    # Index pour les dates
    date_sync = fields.Datetime(index=True)
    
    # Index trigram pour recherche LIKE (PostgreSQL)
    name = fields.Char(index='trigram')
    
    # Index conditionnel (Odoo 18)
    state = fields.Selection([...], index='btree_not_null')
```

### 8.6 Prefetching et Cache ORM

```python
# L'ORM précharge automatiquement les champs simples
# Éviter de casser le prefetching avec .ids ou .browse()

# ❌ MAUVAIS - Casse le prefetching
for record in self.search([]).ids:
    rec = self.browse(record)
    print(rec.name)  # 1 requête par record

# ✅ BON - Préserve le prefetching
for record in self.search([]):
    print(record.name)  # 1 seule requête pour tous
```

### 8.7 Cache avec `@tools.ormcache`

```python
from odoo import tools

class MonModele(models.Model):
    _name = 'mon.modele'
    
    @tools.ormcache('self.env.uid', 'supplier_id')
    def _get_supplier_config(self, supplier_id):
        """Résultat mis en cache par utilisateur et fournisseur"""
        config = self.env['supplier.config'].search([
            ('supplier_id', '=', supplier_id)
        ], limit=1)
        return config.read()[0] if config else {}
    
    def clear_supplier_cache(self):
        """Vider le cache manuellement si nécessaire"""
        self._get_supplier_config.clear_cache(self)
```

### 8.8 Traitement par Lots (Chunking)

```python
def process_large_dataset(self, records):
    """Traiter un grand volume par lots de 100"""
    BATCH_SIZE = 100
    total = len(records)
    
    for i in range(0, total, BATCH_SIZE):
        batch = records[i:i + BATCH_SIZE]
        
        # Traiter le lot
        self._process_batch(batch)
        
        # Commit intermédiaire pour libérer les verrous
        self.env.cr.commit()
        
        # Log de progression
        _logger.info(f"Traité {min(i + BATCH_SIZE, total)}/{total}")

def _process_batch(self, batch):
    """Traitement d'un lot"""
    # Précharger les données liées en une requête
    batch.mapped('partner_id')
    batch.mapped('product_id')
    
    vals_list = []
    for record in batch:
        vals_list.append(self._prepare_values(record))
    
    # Création batch
    if vals_list:
        self.env['target.model'].create(vals_list)
```

### 8.9 SQL Direct pour Opérations Massives

```python
def archive_old_records(self, date_limit):
    """Archiver massivement avec SQL direct"""
    # Flush les changements en attente
    self.env.flush_all()
    
    query = """
        UPDATE mon_modele
        SET active = false,
            write_date = NOW(),
            write_uid = %(uid)s
        WHERE date_sync < %(date_limit)s
          AND active = true
    """
    
    self.env.cr.execute(query, {
        'uid': self.env.uid,
        'date_limit': date_limit,
    })
    
    # Invalider le cache ORM
    self.env.invalidate_all()
    
    return self.env.cr.rowcount
```

### 8.10 Profiling et Analyse des Performances

**Activer le profiler Odoo :**

```python
from odoo.tools.profiler import profile

class MonModele(models.Model):
    _name = 'mon.modele'
    
    @profile
    def method_to_analyze(self):
        """Cette méthode sera profilée"""
        # Code à analyser
        pass
```

**Logs SQL pour identifier les problèmes :**

```ini
# odoo.conf
log_level = debug_sql
```

**Test de comptage de requêtes :**

```python
from odoo.tests import TransactionCase

class TestPerformance(TransactionCase):
    
    def test_query_count(self):
        """Vérifier le nombre de requêtes"""
        records = self.env['mon.modele'].search([], limit=100)
        
        # Compter les requêtes
        with self.assertQueryCount(5):  # Maximum 5 requêtes attendues
            for record in records:
                _ = record.name
                _ = record.partner_id.name
```

### 8.11 Tableau Récapitulatif des Optimisations

| Problème | Solution | Gain |
|----------|----------|------|
| N+1 queries | `_read_group()`, `mapped()` | 90%+ |
| Créations multiples | `create(vals_list)` batch | 80%+ |
| Lectures répétées | `search_read()` avec fields | 50%+ |
| Champs calculés lents | `store=True` | Variable |
| Recherches lentes | `index=True` sur champs | 70%+ |
| Cache invalide | `@tools.ormcache` | Variable |
| Gros volumes | Chunking + commit | Mémoire |
| Mises à jour massives | SQL direct | 95%+ |

### 8.12 Checklist Performance

- [ ] Pas de `search()` dans une boucle `for`
- [ ] Utiliser `create(vals_list)` pour créations multiples
- [ ] `store=True` sur champs calculés affichés en liste
- [ ] Index sur champs de recherche/filtrage fréquents
- [ ] `search_read()` avec liste de `fields` explicite
- [ ] Traitement par lots pour volumes > 1000 enregistrements
- [ ] Profiler les méthodes critiques avant mise en production

---

## 9. Checklist de Validation

### ✅ Avant Installation

- [ ] `__manifest__.py` présent et valide
- [ ] `__init__.py` dans chaque dossier Python
- [ ] `security/ir.model.access.csv` avec tous les modèles
- [ ] Ordre correct dans 'data' du manifest
- [ ] `_description` sur tous les modèles

### ✅ Compatibilité Odoo 18

- [ ] `_compute_display_name` au lieu de `name_get()`
- [ ] `@api.model_create_multi` pour surcharge de `create()`
- [ ] Pas de directives OWL/QWeb personnalisées dans les formulaires
- [ ] Widgets natifs Odoo uniquement
- [ ] `<list>` au lieu de `<tree>` (recommandé)

### ✅ Bonnes Pratiques

- [ ] Noms de modèles en minuscules avec points (`mon.modele`)
- [ ] Noms de champs en snake_case (`mon_champ`)
- [ ] Utiliser `_('...')` pour les chaînes traduisibles
- [ ] Logging approprié avec `_logger`
- [ ] Gestion des erreurs avec `UserError` / `ValidationError`

### ✅ Intégration API

- [ ] Rate limiting avec Token Bucket
- [ ] Batch processing (50 articles/requête recommandé)
- [ ] External IDs pour éviter les doublons
- [ ] Logs complets des opérations

### ✅ Tests (NOUVEAU)

- [ ] Dossier `tests/` avec `__init__.py`
- [ ] Tests pour chaque fonctionnalité critique
- [ ] Tests des cas d'erreur (ValidationError, UserError)
- [ ] Mock des appels API externes
- [ ] Tag `@tagged('post_install', '-at_install')`
- [ ] Assertions avec messages explicites

### ✅ Performance (NOUVEAU)

- [ ] Pas de N+1 queries (vérifier avec `--log-level=debug_sql`)
- [ ] Créations en batch
- [ ] `store=True` sur champs calculés en liste
- [ ] Index sur champs fréquemment filtrés
- [ ] Chunking pour volumes > 1000 enregistrements
- [ ] Test de performance avec `assertQueryCount`

---

## 📚 Références

- [Documentation Officielle Odoo 18](https://www.odoo.com/documentation/18.0/developer/tutorials/server_framework_101.html)
- [ORM API Reference](https://www.odoo.com/documentation/18.0/developer/reference/backend/orm.html)
- [Testing Odoo](https://www.odoo.com/documentation/18.0/developer/reference/backend/testing.html)
- [Performance](https://www.odoo.com/documentation/18.0/developer/reference/backend/performance.html)
- [View Architectures](https://www.odoo.com/documentation/18.0/developer/reference/user_interface/view_architectures.html)
- [Module Manifests](https://www.odoo.com/documentation/18.0/developer/reference/backend/module.html)

---

**📚 Ce document est la référence pour tous les développements Odoo 18**

**BYes - Centre GTB LA ROCHE/YON** • Janvier 2026 • Version 2.0
