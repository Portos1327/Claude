# -*- coding: utf-8 -*-
"""
QDV Sync v7.4 - Avec champs famille configurables et arborescence
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os

_logger = logging.getLogger(__name__)

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False

DEFAULT_QDV_FOLDER = r"C:\Users\dimitri\Mon Drive\Base QDV\Base article et ouvrage"


class QdvSupplier(models.Model):
    _name = 'qdv.supplier'
    _description = 'Fournisseur QDV'
    _order = 'name'

    name = fields.Char(string='Nom', required=True)
    code = fields.Char(string='Code', required=True)
    active = fields.Boolean(default=True)
    supplier_type = fields.Selection([
        ('cable', 'Câbles (€/m)'),
        ('materiel', 'Matériel (€/unité)'),
    ], string='Type', default='cable', required=True)
    
    sql_table_name = fields.Char(compute='_compute_sql_table', store=True)
    sql_table_created = fields.Boolean(default=False)
    
    # =========================================================================
    # SOURCE ODOO
    # =========================================================================
    source_model = fields.Selection([
        ('cable.pricelist.line', 'Cable Pricelist'),
        ('rexel.article', 'Rexel Article Manager'),
        ('product.product', 'Produits Odoo'),
    ], default='cable.pricelist.line', string='Modèle source')
    
    source_model_custom = fields.Char(string='Modèle personnalisé',
        help='Nom technique du modèle si non listé (ex: my.custom.model)')
    
    # Filtres pour Cable Pricelist
    filter_supplier_codes = fields.Char(string='Codes fournisseur/tarif',
        help='Codes séparés par virgule (ex: ELEN, SERMES)')
    filter_by_supplier = fields.Boolean(string='Filtrer par fournisseur', default=True)
    
    # =========================================================================
    # CHAMPS FAMILLE CONFIGURABLES
    # =========================================================================
    family_field = fields.Char(string='Champ Famille', default='family',
        help='Nom du champ Odoo pour la famille (ex: family, famille_libelle)')
    subfamily_field = fields.Char(string='Champ Sous-famille', default='subfamily',
        help='Nom du champ Odoo pour la sous-famille (ex: subfamily, sous_famille_libelle)')
    function_field = fields.Char(string='Champ Fonction',
        help='Nom du champ Odoo pour la fonction/sous-sous-famille (ex: fonction_libelle)')
    
    # Champs codes famille (pour Rexel)
    family_code_field = fields.Char(string='Champ Code Famille',
        help='Nom du champ code famille (ex: famille_code)')
    subfamily_code_field = fields.Char(string='Champ Code Sous-famille',
        help='Nom du champ code sous-famille (ex: sous_famille_code)')
    function_code_field = fields.Char(string='Champ Code Fonction',
        help='Nom du champ code fonction (ex: fonction_code)')
    
    # Filtre par familles
    filter_by_family = fields.Boolean(string='Filtrer par famille', default=False)
    family_filter_ids = fields.One2many('qdv.family.filter', 'supplier_id', string='Filtres familles')
    
    # =========================================================================
    # QDV
    # =========================================================================
    qdv_folder = fields.Char(string='Dossier bases QDV', default=DEFAULT_QDV_FOLDER)
    qdv_pattern = fields.Char(string='Pattern nom fichier')
    qdv_detected_file = fields.Char(compute='_compute_qdv_detected')
    
    # Mapping et familles
    field_mapping_ids = fields.One2many('qdv.field.mapping', 'supplier_id')
    family_ids = fields.One2many('qdv.family', 'supplier_id', string='Familles QDV')
    family_count = fields.Integer(compute='_compute_family_count')
    
    user_field_template = fields.Char(default='Prix Odoo - Tarif {date_tarif}')
    obsolete_text = fields.Char(default='Référence obsolète')
    
    # Stats
    last_sync_date = fields.Datetime(readonly=True)
    last_sync_count = fields.Integer(readonly=True)
    last_qdv_update = fields.Datetime(readonly=True)
    last_qdv_count = fields.Integer(readonly=True)
    last_qdv_obsolete = fields.Integer(readonly=True)
    
    sync_log_ids = fields.One2many('qdv.sync.log', 'supplier_id')

    _sql_constraints = [('code_unique', 'UNIQUE(code)', 'Code unique!')]

    @api.depends('code')
    def _compute_sql_table(self):
        for r in self:
            r.sql_table_name = (str(r.code) + '_Prices') if r.code else ''

    @api.depends('family_ids')
    def _compute_family_count(self):
        for r in self:
            r.family_count = len(r.family_ids)

    @api.depends('qdv_folder', 'qdv_pattern')
    def _compute_qdv_detected(self):
        for r in self:
            found = r._find_qdv_file()
            r.qdv_detected_file = os.path.basename(found) if found else 'Non trouvé'

    @api.onchange('source_model')
    def _onchange_source_model(self):
        """Pré-remplit les champs famille selon le modèle"""
        if self.source_model == 'cable.pricelist.line':
            self.family_field = 'family'
            self.subfamily_field = 'subfamily'
            self.function_field = ''
            self.family_code_field = ''
            self.subfamily_code_field = ''
            self.function_code_field = ''
        elif self.source_model == 'rexel.article':
            self.family_field = 'famille_libelle'
            self.subfamily_field = 'sous_famille_libelle'
            self.function_field = 'fonction_libelle'
            self.family_code_field = 'famille_code'
            self.subfamily_code_field = 'sous_famille_code'
            self.function_code_field = 'fonction_code'
        elif self.source_model == 'product.product':
            self.family_field = 'categ_id'
            self.subfamily_field = ''
            self.function_field = ''
            self.family_code_field = ''
            self.subfamily_code_field = ''
            self.function_code_field = ''

    def _find_qdv_file(self):
        if not self.qdv_folder or not self.qdv_pattern:
            return None
        folder = self.qdv_folder
        pattern = str(self.qdv_pattern or '').strip()
        if not pattern or not os.path.isdir(folder):
            return None
        matching = [os.path.join(folder, f) for f in os.listdir(folder) 
                   if f.lower().endswith('.qdb') and pattern.upper() in f.upper()]
        if not matching:
            return None
        return max(matching, key=os.path.getmtime)

    # =========================================================================
    # DÉTECTION DES FAMILLES
    # =========================================================================
    def action_detect_families(self):
        """Détecte les familles/sous-familles/fonctions avec arborescence"""
        self.ensure_one()
        
        records = self._get_source_data()
        if not records:
            raise UserError(_("Aucun enregistrement trouvé!"))
        
        # Collecter avec arborescence
        families = {}  # {(fam, subfam, func, fam_code, subfam_code, func_code): count}
        
        fam_field = self.family_field or 'family'
        subfam_field = self.subfamily_field
        func_field = self.function_field
        fam_code_field = self.family_code_field
        subfam_code_field = self.subfamily_code_field
        func_code_field = self.function_code_field
        
        for rec in records:
            data = self._extract_record_data(rec)
            
            fam = str(data.get(fam_field, '') or '').strip()
            subfam = str(data.get(subfam_field, '') or '').strip() if subfam_field else ''
            func = str(data.get(func_field, '') or '').strip() if func_field else ''
            
            fam_code = str(data.get(fam_code_field, '') or '').strip() if fam_code_field else ''
            subfam_code = str(data.get(subfam_code_field, '') or '').strip() if subfam_code_field else ''
            func_code = str(data.get(func_code_field, '') or '').strip() if func_code_field else ''
            
            if fam or subfam or func:
                key = (fam, subfam, func, fam_code, subfam_code, func_code)
                families[key] = families.get(key, 0) + 1
        
        # Supprimer les anciens filtres
        self.family_filter_ids.unlink()
        
        # Créer avec arborescence
        created = 0
        for (fam, subfam, func, fam_code, subfam_code, func_code), count in sorted(families.items()):
            # Calculer le code complet
            full_code_parts = []
            if fam_code:
                full_code_parts.append(fam_code)
            if subfam_code:
                full_code_parts.append(subfam_code)
            if func_code:
                full_code_parts.append(func_code)
            
            self.env['qdv.family.filter'].create({
                'supplier_id': self.id,
                'family_name': fam,
                'subfamily_name': subfam,
                'function_name': func,
                'family_code': fam_code,
                'subfamily_code': subfam_code,
                'function_code': func_code,
                'article_count': count,
                'selected': True,
            })
            created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Familles détectées',
                'message': '%d familles/sous-familles/fonctions' % created,
                'type': 'success',
                'sticky': False
            }
        }

    # =========================================================================
    # LECTURE DES DONNÉES ODOO
    # =========================================================================
    def _get_source_data(self):
        """Récupère les enregistrements avec filtres"""
        if not self.source_model or self.source_model not in self.env:
            raise UserError(_("Modèle source '%s' non disponible!") % self.source_model)
        
        domain = []
        
        # Filtre par fournisseur pour Cable Pricelist
        if self.source_model == 'cable.pricelist.line' and self.filter_by_supplier:
            codes = self._get_filter_codes()
            if codes:
                domain_codes = []
                for code in codes:
                    domain_codes.append(('pricelist_id.supplier_id.code', 'ilike', code))
                    domain_codes.append(('pricelist_id.supplier_id.name', 'ilike', code))
                    domain_codes.append(('manufacturer_name', 'ilike', code))
                    domain_codes.append(('distributor_name', 'ilike', code))
                if len(domain_codes) > 1:
                    domain = ['|'] * (len(domain_codes) - 1) + domain_codes
        
        # Filtre par famille si activé
        if self.filter_by_family and self.family_filter_ids:
            selected = self.family_filter_ids.filtered(lambda f: f.selected)
            if selected:
                fam_field = self.family_field or 'family'
                subfam_field = self.subfamily_field
                func_field = self.function_field
                
                # Construire les conditions pour chaque filtre sélectionné
                filter_domains = []
                
                for f in selected:
                    if f.function_name and func_field:
                        # 3 niveaux : famille + sous-famille + fonction
                        filter_domains.append([
                            (fam_field, '=', f.family_name),
                            (subfam_field, '=', f.subfamily_name),
                            (func_field, '=', f.function_name)
                        ])
                    elif f.subfamily_name and subfam_field:
                        # 2 niveaux : famille + sous-famille
                        filter_domains.append([
                            (fam_field, '=', f.family_name),
                            (subfam_field, '=', f.subfamily_name)
                        ])
                    elif f.family_name:
                        # 1 niveau : famille seulement
                        filter_domains.append([
                            (fam_field, '=', f.family_name)
                        ])
                
                # Combiner avec OR entre les filtres, AND à l'intérieur de chaque filtre
                if filter_domains:
                    from odoo.osv import expression
                    family_domain = expression.OR(filter_domains)
                    
                    if domain:
                        domain = expression.AND([domain, family_domain])
                    else:
                        domain = family_domain
        
        _logger.info("Domain: %s", domain)
        return self.env[self.source_model].search(domain, limit=100000)

    def _get_filter_codes(self):
        if not self.filter_supplier_codes:
            return [self.code] if self.code else []
        return [c.strip() for c in self.filter_supplier_codes.split(',') if c.strip()]

    def _extract_record_data(self, record):
        """Extrait TOUS les champs d'un enregistrement"""
        data = {}
        for field_name in record._fields:
            try:
                value = getattr(record, field_name, None)
                if value is None:
                    continue
                if hasattr(value, 'id') and hasattr(value, 'name'):
                    data[field_name] = str(value.name or '')
                elif hasattr(value, 'ids'):
                    continue
                elif isinstance(value, bool):
                    data[field_name] = value
                elif isinstance(value, (int, float)):
                    data[field_name] = value
                else:
                    data[field_name] = str(value or '')
            except Exception:
                pass
        return data

    def _get_reference_field(self):
        for m in self.field_mapping_ids:
            if m.is_key and m.odoo_field:
                return m.odoo_field
        return 'reference'

    # =========================================================================
    # GESTION CODE FAMILLE QDV (fonction > sous-famille > famille)
    # =========================================================================
    def _get_qdv_family_code(self, data, family_mapping, cur_qdv):
        """
        Retourne le code QDV avec PRIORITÉ: fonction > sous-famille > famille
        Utilise les champs configurés et les codes composés
        """
        fam_field = self.family_field or 'family'
        subfam_field = self.subfamily_field
        func_field = self.function_field
        
        fam_code_field = self.family_code_field
        subfam_code_field = self.subfamily_code_field
        func_code_field = self.function_code_field
        
        # Récupérer les valeurs
        famille = str(data.get(fam_field, '') or '').strip()
        sous_famille = str(data.get(subfam_field, '') or '').strip() if subfam_field else ''
        fonction = str(data.get(func_field, '') or '').strip() if func_field else ''
        
        # Récupérer les codes sources
        fam_code = str(data.get(fam_code_field, '') or '').strip() if fam_code_field else ''
        subfam_code = str(data.get(subfam_code_field, '') or '').strip() if subfam_code_field else ''
        func_code = str(data.get(func_code_field, '') or '').strip() if func_code_field else ''
        
        # 1. PRIORITÉ: Fonction (niveau 3)
        if fonction or func_code:
            # Chercher par code complet
            if fam_code and subfam_code and func_code:
                full_code = fam_code + subfam_code + func_code
                code = self._find_family_code_in_filters(full_code=full_code)
                if code:
                    return code
            # Chercher par nom
            code = self._find_family_code(fonction, family_mapping, cur_qdv)
            if code:
                return code
        
        # 2. Sous-famille (niveau 2)
        if sous_famille or subfam_code:
            if fam_code and subfam_code:
                full_code = fam_code + subfam_code
                code = self._find_family_code_in_filters(full_code=full_code)
                if code:
                    return code
            code = self._find_family_code(sous_famille, family_mapping, cur_qdv)
            if code:
                return code
        
        # 3. Famille (niveau 1)
        if famille or fam_code:
            if fam_code:
                code = self._find_family_code_in_filters(full_code=fam_code)
                if code:
                    return code
            code = self._find_family_code(famille, family_mapping, cur_qdv)
            if code:
                return code
        
        return ''

    def _find_family_code_in_filters(self, full_code=None):
        """Cherche le code QDV dans les filtres famille"""
        for f in self.family_filter_ids:
            if f.qdv_family_code:
                if full_code and f.full_code == full_code:
                    return f.qdv_family_code
        return ''

    def _find_family_code(self, value, mapping, cur_qdv):
        """Cherche le code QDV pour une valeur"""
        if not value:
            return ''
        
        val_lower = str(value).lower().strip()
        if val_lower.startswith('{fr}'):
            val_lower = val_lower[4:]
        
        # 1. Mapping Odoo
        if val_lower in mapping:
            return mapping[val_lower]
        
        # 2. Correspondance partielle
        for k, v in mapping.items():
            if k in val_lower or val_lower in k:
                return v
        
        # 3. Filtres famille
        for f in self.family_filter_ids:
            if f.qdv_family_code:
                if f.function_name and f.function_name.lower() == val_lower:
                    return f.qdv_family_code
                elif f.subfamily_name and f.subfamily_name.lower() == val_lower:
                    return f.qdv_family_code
                elif f.family_name and f.family_name.lower() == val_lower:
                    return f.qdv_family_code
        
        # 4. TreeTable QDV
        if cur_qdv:
            try:
                cur_qdv.execute("SELECT FamilyValue FROM TreeTable WHERE LOWER(FamilyText) LIKE ?", 
                               ('%' + val_lower + '%',))
                r = cur_qdv.fetchone()
                if r:
                    return r[0]
            except Exception:
                pass
        
        return ''

    def _build_family_mapping(self):
        """Construit le mapping famille Odoo → code QDV"""
        mapping = {}
        
        for f in self.family_ids:
            if f.name:
                mapping[f.name.lower().strip()] = f.code
            if f.odoo_families:
                for v in f.odoo_families.split(','):
                    v = v.strip()
                    if v:
                        mapping[v.lower()] = f.code
        
        for f in self.family_filter_ids:
            if f.qdv_family_code:
                if f.function_name:
                    mapping[f.function_name.lower().strip()] = f.qdv_family_code
                if f.subfamily_name:
                    mapping[f.subfamily_name.lower().strip()] = f.qdv_family_code
                if f.family_name:
                    mapping[f.family_name.lower().strip()] = f.qdv_family_code
        
        return mapping

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_view_families(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Familles QDV - ' + self.name,
            'res_model': 'qdv.family',
            'view_mode': 'list,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id},
        }

    # =========================================================================
    # SCAN COLONNES QDV DISPONIBLES
    # =========================================================================
    def action_scan_qdv_columns(self):
        """Scanne la base QDV et détecte les colonnes disponibles"""
        self.ensure_one()
        qdv_path = self._find_qdv_file()
        if not qdv_path:
            raise UserError(_("Base QDV non trouvée!"))
        
        import sqlite3
        conn = sqlite3.connect(qdv_path)
        cur = conn.cursor()
        
        # Lire les colonnes depuis FieldNames
        cur.execute("""
            SELECT FieldName, TableIndex, ColumnTitle 
            FROM FieldNames 
            WHERE Visible = -1
            ORDER BY TableIndex, FieldName
        """)
        
        columns_found = []
        table_names = {0: 'articles', 1: 'columns_data_mt', 2: 'columns_data_wf', 3: 'extended_data'}
        
        for row in cur.fetchall():
            field_name = row[0]
            table_idx = row[1]
            title = row[2] or field_name
            
            # Extraire le titre FR
            if '{FR}' in title:
                title = title.split('{FR}')[1].split('{')[0].strip()
            
            table_name = table_names.get(table_idx, 'articles')
            columns_found.append({
                'field': field_name,
                'table': table_name,
                'title': title
            })
        
        conn.close()
        
        # Créer/mettre à jour les mappings manquants
        existing_cols = {(m.qdv_table, m.qdv_column): m for m in self.field_mapping_ids}
        created = 0
        
        for col in columns_found:
            key = (col['table'], col['field'])
            if key not in existing_cols:
                # Créer un nouveau mapping inactif
                self.env['qdv.field.mapping'].create({
                    'supplier_id': self.id,
                    'qdv_table': col['table'],
                    'qdv_column': col['field'],
                    'qdv_column_title': col['title'],
                    'active': False,  # Inactif par défaut
                    'sync_direction': 'none',
                    'sequence': 100,
                })
                created += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Colonnes QDV scannées',
                'message': '%d colonnes détectées, %d nouvelles ajoutées' % (len(columns_found), created),
                'type': 'success',
                'sticky': False
            }
        }

    def action_scan_material_kinds(self):
        """Scanne les MaterialKindID existants dans QDV et crée les correspondances"""
        self.ensure_one()
        qdv_path = self._find_qdv_file()
        if not qdv_path:
            raise UserError(_("Base QDV non trouvée!"))
        
        import sqlite3
        conn = sqlite3.connect(qdv_path)
        cur = conn.cursor()
        
        # Récupérer les familles utilisées avec leur MaterialKindID
        cur.execute("""
            SELECT DISTINCT a.Family, m.MaterialKindID
            FROM Articles a
            JOIN ColumnsDataMT m ON m.IDInArticles = a.RowID
            WHERE a.Family IS NOT NULL AND a.Family != ''
            AND m.MaterialKindID IS NOT NULL AND m.MaterialKindID != ''
        """)
        
        family_to_kind = {}
        for family, kind_id in cur.fetchall():
            if family and kind_id:
                family_to_kind[family] = kind_id
        
        conn.close()
        
        # Mettre à jour les filtres famille avec les MaterialKindID
        updated = 0
        for f in self.family_filter_ids:
            # Chercher une correspondance
            for family, kind_id in family_to_kind.items():
                if f.family_name and (f.family_name in family or family in f.family_name):
                    if not f.material_kind_id:
                        f.material_kind_id = kind_id
                        updated += 1
                        break
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'MaterialKindID scannés',
                'message': '%d familles QDV trouvées, %d correspondances créées' % (len(family_to_kind), updated),
                'type': 'success',
                'sticky': False
            }
        }

    def action_create_sql_table(self):
        self.ensure_one()
        config = self.env['qdv.sql.config'].get_config()
        if not config:
            raise UserError(_("Configurez SQL Server!"))
        
        columns = self._get_sql_columns_from_mapping()
        
        try:
            conn = pyodbc.connect(config._get_connection_string(), timeout=10)
            cur = conn.cursor()
            table_name = str(self.sql_table_name)
            
            cur.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = ?", (table_name,))
            if cur.fetchone()[0] > 0:
                raise UserError(_("Table %s existe déjà!") % table_name)
            
            col_defs = ["id INT IDENTITY(1,1) PRIMARY KEY"]
            for col_name, col_type in columns.items():
                col_defs.append("[" + col_name + "] " + col_type)
            col_defs.append("active BIT DEFAULT 1")
            col_defs.append("date_maj DATETIME DEFAULT GETDATE()")
            
            sql = "CREATE TABLE [" + table_name + "] (" + ", ".join(col_defs) + ")"
            cur.execute(sql)
            
            if 'reference' in columns:
                cur.execute("CREATE INDEX IX_" + str(self.code) + "_Ref ON [" + table_name + "](reference)")
            
            conn.commit()
            conn.close()
            
            self.sql_table_created = True
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Table créée!', 'message': table_name, 'type': 'success', 'sticky': False}
            }
        except Exception as e:
            raise UserError(str(e))

    def _get_sql_columns_from_mapping(self):
        columns = {}
        for m in self.field_mapping_ids:
            if not m.active or not m.odoo_field:
                continue
            col_name = m.odoo_field.replace('.', '_')
            if 'price' in col_name.lower() or col_name in ('discount', 'remise', 'weight', 'poids'):
                col_type = 'DECIMAL(18,6) DEFAULT 0'
            else:
                col_type = 'NVARCHAR(500)'
            columns[col_name] = col_type
        if 'reference' not in columns:
            columns['reference'] = 'NVARCHAR(100) NOT NULL'
        return columns

    def action_add_column_to_sql(self):
        self.ensure_one()
        config = self.env['qdv.sql.config'].get_config()
        if not config:
            raise UserError(_("Configurez SQL Server!"))
        
        columns_needed = self._get_sql_columns_from_mapping()
        
        try:
            conn = pyodbc.connect(config._get_connection_string(), timeout=10)
            cur = conn.cursor()
            table_name = str(self.sql_table_name)
            
            cur.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", (table_name,))
            existing = [row[0].lower() for row in cur.fetchall()]
            
            added = []
            for col_name, col_type in columns_needed.items():
                if col_name.lower() not in existing:
                    cur.execute("ALTER TABLE [" + table_name + "] ADD [" + col_name + "] " + col_type)
                    added.append(col_name)
            
            conn.commit()
            conn.close()
            
            msg = str(len(added)) + " colonnes ajoutées" if added else "Tout est à jour"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'OK', 'message': msg, 'type': 'success', 'sticky': False}
            }
        except Exception as e:
            raise UserError(str(e))

    def action_create_default_mapping(self):
        self.ensure_one()
        self.field_mapping_ids.unlink()
        
        mappings = [
            {'qdv_column': 'Reference', 'odoo_field': 'reference', 'is_key': True, 'sequence': 10},
            {'qdv_column': 'Description', 'odoo_field': 'designation', 'sequence': 20},
            {'qdv_column': 'Family', 'odoo_field': 'family', 'convert_family_to_code': True, 'sequence': 30},
            {'qdv_column': 'Manufacturer', 'odoo_field': 'manufacturer_name', 'sequence': 40},
            {'qdv_column': 'UserDefinedField', 'odoo_field': '_template', 'value_source': 'template', 'sequence': 50},
            {'qdv_column': 'CostPerUnitMT', 'odoo_field': 'price_net', 'sequence': 60},
            {'qdv_column': 'Rebate', 'odoo_field': 'discount', 'sequence': 70, 'sync_direction': 'none'},
        ]
        
        for m in mappings:
            vals = dict(m)
            vals['supplier_id'] = self.id
            vals['qdv_table'] = 'columns_data_mt' if vals['qdv_column'] in ('CostPerUnitMT', 'Rebate') else 'articles'
            if 'sync_direction' not in vals:
                vals['sync_direction'] = 'odoo_to_qdv'
            if 'value_source' not in vals:
                vals['value_source'] = 'odoo_field'
            self.env['qdv.field.mapping'].create(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {'title': 'Mapping créé', 'message': str(len(mappings)) + ' champs', 'type': 'success', 'sticky': False}
        }

    def action_show_available_fields(self):
        self.ensure_one()
        
        if not self.source_model:
            raise UserError(_("Sélectionnez d'abord un modèle source!"))
        if self.source_model not in self.env:
            raise UserError(_("Le modèle '%s' n'est pas installé!") % self.source_model)
        
        model = self.env[self.source_model]
        fields_info = model.fields_get()
        
        lines = ["=" * 60, "CHAMPS: " + str(self.source_model), "=" * 60, "",
                 "SPÉCIAUX: _template, _static, _date_now", "", "-" * 60]
        
        sorted_fields = sorted(fields_info.items(), key=lambda x: (x[1].get('type', ''), x[0]))
        current_type = None
        
        for field_name, field_data in sorted_fields:
            if field_name.startswith('_') or field_name in ('id', 'create_uid', 'create_date', 'write_uid', 'write_date', '__last_update', 'display_name'):
                continue
            field_type = field_data.get('type', 'unknown')
            field_label = field_data.get('string', field_name)
            if field_type != current_type:
                current_type = field_type
                lines.append("")
                lines.append("[" + str(field_type).upper() + "]")
            lines.append("  %-30s  %s" % (field_name, field_label))
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Champs - ' + str(self.source_model),
            'res_model': 'qdv.fields.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_content': "\n".join(lines), 'default_supplier_id': self.id},
        }

    # =========================================================================
    # SYNC ODOO → SQL
    # =========================================================================
    def action_sync_sql(self):
        self.ensure_one()
        config = self.env['qdv.sql.config'].get_config()
        if not config:
            raise UserError(_("Configurez SQL Server!"))
        
        # IMPORTANT: Ne prendre QUE les mappings avec direction vers QDV/SQL
        active_mappings = self.field_mapping_ids.filtered(
            lambda m: m.active and m.odoo_field and m.sync_direction in ('odoo_to_qdv', 'bidirectional'))
        if not active_mappings:
            raise UserError(_("Aucun mapping actif avec direction 'Odoo → QDV'!"))
        
        import time
        start_time = time.time()
        
        log = self.env['qdv.sync.log'].create({
            'supplier_id': self.id,
            'sync_start': fields.Datetime.now(),
            'status': 'running',
            'log_type': 'sql'
        })
        
        try:
            records = self._get_source_data()
            if not records:
                raise UserError(_("Aucun enregistrement trouvé!"))
            
            conn = pyodbc.connect(config._get_connection_string(), timeout=30)
            cur = conn.cursor()
            table_name = str(self.sql_table_name)
            
            # S'assurer que les colonnes existent AVANT de commencer
            self._ensure_sql_columns(cur, table_name, active_mappings)
            conn.commit()  # Commit les ALTER TABLE
            
            ref_field = self._get_reference_field()
            created = 0
            updated = 0
            errors = 0
            
            for record in records:
                try:
                    data = self._extract_record_data(record)
                    ref = data.get(ref_field, '')
                    if not ref:
                        errors += 1
                        continue
                    
                    cols = ['reference']
                    vals = [ref]
                    
                    for m in active_mappings:
                        if m.is_key:
                            continue
                        
                        # Gérer les valeurs spéciales
                        if m.value_source == 'static':
                            value = m.static_value or ''
                        elif m.value_source == 'template' or m.odoo_field == '_template':
                            value = self._format_template(data)
                        elif m.odoo_field == '_date_now':
                            from datetime import datetime
                            value = datetime.now().strftime("%Y-%m-%d")
                        else:
                            value = data.get(m.odoo_field, '')
                        
                        col_name = m.odoo_field.replace('.', '_')
                        # Ne pas ajouter les champs spéciaux comme noms de colonnes
                        if col_name.startswith('_'):
                            col_name = m.qdv_column.lower().replace(' ', '_') if m.qdv_column else 'field_' + str(m.id)
                        cols.append(col_name)
                        vals.append(value if value is not None else '')
                    
                    cur.execute("SELECT id FROM [" + table_name + "] WHERE [reference] = ?", (ref,))
                    
                    if cur.fetchone():
                        set_cols = cols[1:]
                        set_vals = vals[1:]
                        if set_cols:
                            set_clause = ", ".join(["[" + c + "]=?" for c in set_cols])
                            cur.execute("UPDATE [" + table_name + "] SET " + set_clause + ", date_maj=GETDATE(), active=1 WHERE [reference]=?", set_vals + [ref])
                        updated += 1
                    else:
                        cols_str = ", ".join(["[" + c + "]" for c in cols])
                        placeholders = ", ".join(["?"] * len(vals))
                        cur.execute("INSERT INTO [" + table_name + "] (" + cols_str + ", active, date_maj) VALUES (" + placeholders + ", 1, GETDATE())", vals)
                        created += 1
                except Exception as rec_error:
                    _logger.warning("Erreur sur record: %s", str(rec_error))
                    errors += 1
            
            conn.commit()
            conn.close()
            
            duration = time.time() - start_time
            msg = "%d traités, %d créés, %d MAJ" % (len(records), created, updated)
            if errors:
                msg += ", %d erreurs" % errors
            
            log.write({
                'sync_end': fields.Datetime.now(),
                'duration': duration,
                'records_processed': len(records),
                'records_created': created,
                'records_updated': updated,
                'status': 'success',
                'error_message': msg
            })
            self.write({'last_sync_date': fields.Datetime.now(), 'last_sync_count': created + updated})
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'Sync SQL', 'message': msg, 'type': 'success', 'sticky': False}
            }
        except Exception as e:
            log.write({'sync_end': fields.Datetime.now(), 'status': 'error', 'error_message': str(e)})
            raise UserError(str(e))

    def _ensure_sql_columns(self, cursor, table_name, mappings=None):
        """S'assure que les colonnes SQL existent pour les mappings actifs"""
        cursor.execute("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?", (table_name,))
        existing = [row[0].lower() for row in cursor.fetchall()]
        
        # S'assurer que 'reference' existe toujours
        if 'reference' not in existing:
            cursor.execute("ALTER TABLE [" + table_name + "] ADD [reference] NVARCHAR(100)")
            existing.append('reference')
        
        # Utiliser les mappings fournis ou tous les mappings actifs
        if mappings is None:
            mappings = self.field_mapping_ids.filtered(
                lambda m: m.active and m.odoo_field and m.sync_direction in ('odoo_to_qdv', 'bidirectional'))
        
        for m in mappings:
            if not m.odoo_field:
                continue
            if m.is_key:
                continue
            
            col_name = m.odoo_field.replace('.', '_')
            # Pour les champs spéciaux, utiliser le nom de colonne QDV
            if col_name.startswith('_'):
                col_name = m.qdv_column.lower().replace(' ', '_') if m.qdv_column else 'field_' + str(m.id)
            
            if col_name.lower() not in existing:
                if 'price' in col_name.lower() or 'prix' in col_name.lower() or col_name in ('discount', 'weight', 'remise'):
                    col_type = 'DECIMAL(18,6) DEFAULT 0'
                else:
                    col_type = 'NVARCHAR(500)'
                try:
                    cursor.execute("ALTER TABLE [" + table_name + "] ADD [" + col_name + "] " + col_type)
                    existing.append(col_name.lower())
                    _logger.info("Colonne SQL ajoutée: %s", col_name)
                except Exception as e:
                    _logger.warning("Impossible d'ajouter la colonne %s: %s", col_name, str(e))

    def _format_template(self, data):
        from datetime import datetime
        template = str(self.user_field_template or 'Prix Odoo - {date_tarif}')
        date_str = datetime.now().strftime("%d/%m/%Y")
        return template.replace('{date_tarif}', date_str).replace('{supplier}', str(self.code or '')).replace('{sync_date}', date_str)

    # =========================================================================
    # MAJ QDV
    # =========================================================================
    def action_update_qdv(self):
        self.ensure_one()
        qdv_path = self._find_qdv_file()
        if not qdv_path:
            raise UserError(_("Base QDV non trouvée!"))
        
        config = self.env['qdv.sql.config'].get_config()
        if not config:
            raise UserError(_("Configurez SQL Server!"))
        
        import time
        start_time = time.time()
        
        log = self.env['qdv.sync.log'].create({
            'supplier_id': self.id,
            'sync_start': fields.Datetime.now(),
            'status': 'running',
            'log_type': 'qdv'
        })
        
        try:
            result = self._sync_sql_to_qdv(qdv_path, config)
            duration = time.time() - start_time
            msg = "%d MAJ, %d obsolètes" % (result['updated'], result['obsolete'])
            
            log.write({
                'sync_end': fields.Datetime.now(),
                'duration': duration,
                'records_processed': result['total'],
                'records_updated': result['updated'],
                'records_errors': result['obsolete'],
                'status': 'success',
                'error_message': msg
            })
            self.write({
                'last_qdv_update': fields.Datetime.now(),
                'last_qdv_count': result['updated'],
                'last_qdv_obsolete': result['obsolete']
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {'title': 'MAJ QDV', 'message': msg, 'type': 'success', 'sticky': False}
            }
        except Exception as e:
            log.write({'sync_end': fields.Datetime.now(), 'status': 'error', 'error_message': str(e)})
            raise UserError(str(e))

    def _sync_sql_to_qdv(self, qdv_path, config):
        import sqlite3
        
        map_art = {}
        map_mt = {}
        for m in self.field_mapping_ids:
            if not m.active or m.sync_direction in ('qdv_to_odoo', 'none', False, None, ''):
                continue
            if m.qdv_table == 'articles':
                map_art[m.qdv_column] = m
            elif m.qdv_table == 'columns_data_mt':
                map_mt[m.qdv_column] = m
        
        if not map_art and not map_mt:
            raise UserError(_("Aucun mapping actif!"))
        
        conn_sql = pyodbc.connect(config._get_connection_string(), timeout=30)
        cur_sql = conn_sql.cursor()
        table_name = str(self.sql_table_name)
        
        cur_sql.execute("SELECT * FROM [" + table_name + "] WHERE active=1")
        columns = [desc[0] for desc in cur_sql.description]
        
        sql_data = {}
        for row in cur_sql.fetchall():
            data = dict(zip(columns, row))
            # Toujours utiliser 'reference' comme colonne SQL
            ref = str(data.get('reference', '') or '')
            if ref:
                sql_data[ref] = data
        
        conn_sql.close()
        
        user_field = self._format_template({})
        family_mapping = self._build_family_mapping()
        
        conn_qdv = sqlite3.connect(qdv_path)
        cur_qdv = conn_qdv.cursor()
        cur_qdv.execute("SELECT RowID, Reference FROM Articles")
        qdv_articles = {str(ref): row_id for row_id, ref in cur_qdv.fetchall() if ref}
        
        updated = 0
        obsolete = 0
        
        for ref, row_id in qdv_articles.items():
            if ref in sql_data:
                data = sql_data[ref]
                
                if map_art:
                    upd = []
                    vals = []
                    for col, m in map_art.items():
                        if m.is_key:
                            continue
                        v = self._get_value_from_mapping(m, data, user_field, family_mapping, cur_qdv)
                        if v is not None:
                            upd.append(str(col) + "=?")
                            vals.append(v)
                    if upd:
                        vals.append(row_id)
                        cur_qdv.execute("UPDATE Articles SET " + ",".join(upd) + " WHERE RowID=?", vals)
                
                if map_mt:
                    upd = []
                    vals = []
                    for col, m in map_mt.items():
                        v = self._get_value_from_mapping(m, data, user_field, family_mapping, cur_qdv)
                        upd.append(str(col) + "=?")
                        vals.append(v if v is not None else 0)
                    if upd:
                        vals_upd = list(vals) + [row_id]
                        cur_qdv.execute("UPDATE ColumnsDataMT SET " + ",".join(upd) + " WHERE IDInArticles=?", vals_upd)
                        if cur_qdv.rowcount == 0:
                            cur_qdv.execute("INSERT INTO ColumnsDataMT (IDInArticles, " + ",".join(map_mt.keys()) + ") VALUES (?" + ",?" * len(vals) + ")", [row_id] + list(vals))
                
                updated += 1
            else:
                cur_qdv.execute("UPDATE Articles SET UserDefinedField=? WHERE RowID=?", (self.obsolete_text, row_id))
                obsolete += 1
        
        conn_qdv.commit()
        conn_qdv.close()
        
        return {'total': len(qdv_articles), 'updated': updated, 'obsolete': obsolete}

    def _get_value_from_mapping(self, mapping, data, user_field, family_mapping, cur_qdv):
        if mapping.value_source == 'static':
            return mapping.static_value or ''
        if mapping.value_source == 'template' or mapping.odoo_field in ('_template', '_user_field_template'):
            return user_field
        if mapping.odoo_field == '_date_now':
            from datetime import datetime
            return datetime.now().strftime("%Y-%m-%d")
        if mapping.convert_family_to_code:
            return self._get_qdv_family_code(data, family_mapping, cur_qdv)
        if mapping.odoo_field:
            col_name = mapping.odoo_field.replace('.', '_')
            return data.get(col_name, data.get(mapping.odoo_field, ''))
        return ''
