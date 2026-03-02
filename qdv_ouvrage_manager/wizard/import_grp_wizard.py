# -*- coding: utf-8 -*-
import base64
import tempfile
import os
import sqlite3
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QdvImportGrpWizard(models.TransientModel):
    """Wizard d'import d'une base d'ouvrage QDV7 (.grp)"""
    _name = 'qdv.import.grp.wizard'
    _description = 'Import base d\'ouvrage QDV7 (.grp)'

    base_id = fields.Many2one(
        'qdv.ouvrage.base',
        string='Base d\'ouvrage',
        required=True
    )
    grp_file = fields.Binary(
        string='Fichier .grp',
        required=True,
        help='Sélectionnez le fichier SQLite .grp de votre base d\'ouvrage QDV7'
    )
    grp_filename = fields.Char(string='Nom du fichier')

    import_mode = fields.Selection([
        ('replace', 'Remplacer (efface et réimporte tout)'),
        ('update', 'Mettre à jour (ajoute/modifie, ne supprime pas)'),
    ], string='Mode d\'import', default='replace', required=True)

    # Résultats
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('done', 'Terminé'),
    ], default='draft')

    result_log = fields.Text(string='Résultats', readonly=True)
    familles_count = fields.Integer(string='Familles importées', readonly=True)
    ouvrages_count = fields.Integer(string='Ouvrages importés', readonly=True)
    ouvrages_updated = fields.Integer(string='Ouvrages mis à jour', readonly=True)

    def action_import(self):
        """Importer le fichier .grp"""
        self.ensure_one()

        if not self.grp_file:
            raise UserError(_('Veuillez sélectionner un fichier .grp'))

        # Décoder le fichier base64 et écrire dans un fichier temporaire
        file_data = base64.b64decode(self.grp_file)

        with tempfile.NamedTemporaryFile(suffix='.grp', delete=False) as tmp:
            tmp.write(file_data)
            tmp_path = tmp.name

        try:
            result = self._process_grp_file(tmp_path)
        finally:
            os.unlink(tmp_path)

        self.write({
            'state': 'done',
            'result_log': result['log'],
            'familles_count': result['familles'],
            'ouvrages_count': result['ouvrages_created'],
            'ouvrages_updated': result['ouvrages_updated'],
        })

        # Retourner la vue résultat
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.import.grp.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _process_grp_file(self, file_path):
        """Traitement du fichier SQLite .grp"""
        log_lines = []
        familles_count = 0
        ouvrages_created = 0
        ouvrages_updated = 0

        try:
            conn = sqlite3.connect(file_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Vérifier que c'est bien un fichier QDV7
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            required_tables = {'Groups', 'TreeTable', 'SettingsTable'}
            if not required_tables.issubset(set(tables)):
                raise UserError(
                    _('Le fichier ne semble pas être une base d\'ouvrage QDV7 valide.\n'
                      'Tables attendues : %s\nTables trouvées : %s') % (
                        ', '.join(required_tables), ', '.join(tables)
                    )
                )

            # Lire la version
            cur.execute("SELECT VariableValue FROM SettingsTable WHERE VariableName = '#FILEVERSION#'")
            row = cur.fetchone()
            file_version = row[0] if row else 0.0
            log_lines.append(f'✅ Fichier QDV7 version {file_version} détecté')

            base = self.base_id
            base.write({
                'file_version': file_version,
                'date_import': fields.Datetime.now(),
                'import_user_id': self.env.uid,
            })

            # ================================================
            # 1. Import des familles (TreeTable)
            # ================================================
            if self.import_mode == 'replace':
                # Supprimer d'abord les ouvrages pour éviter les contraintes FK
                base.ouvrage_ids.unlink()
                base.famille_ids.unlink()

            cur.execute("SELECT RowID, FamilyValue, FamilyText FROM TreeTable ORDER BY FamilyValue")
            famille_rows = cur.fetchall()
            log_lines.append(f'\n📁 Import des familles ({len(famille_rows)} lignes)...')

            famille_vals_list = []
            for row in famille_rows:
                row_id = row['RowID']
                code = row['FamilyValue'] or ''
                # Nettoyer le libellé : retirer le préfixe {FR}
                text = row['FamilyText'] or ''
                if '{FR}' in text:
                    text = text.split('{FR}')[-1]

                if not code:
                    continue

                if self.import_mode == 'update':
                    existing = self.env['qdv.ouvrage.famille'].search([
                        ('base_id', '=', base.id),
                        ('code', '=', code)
                    ], limit=1)
                    if existing:
                        existing.write({'name': text, 'qdv_row_id': row_id})
                        continue

                famille_vals_list.append({
                    'base_id': base.id,
                    'qdv_row_id': row_id,
                    'code': code,
                    'name': text,
                })

            if famille_vals_list:
                self.env['qdv.ouvrage.famille'].create(famille_vals_list)

            familles_count = len(famille_rows)
            log_lines.append(f'  ✅ {familles_count} familles importées')

            # ================================================
            # 2. Import des ouvrages (Groups)
            # ================================================
            cur.execute("""
                SELECT RowID, Description, Reference, Family, Manufacturer,
                       UserDefinedField, Unit, ForcedSellingPricePerUnit,
                       TakeForcedSellingPrice, LockTheGroup,
                       ArticleDate, AlterDate, LastUserInformation
                FROM Groups
                ORDER BY RowID
            """)
            ouvrage_rows = cur.fetchall()
            log_lines.append(f'\n🔧 Import des ouvrages ({len(ouvrage_rows)} ouvrages)...')

            vals_list = []
            for row in ouvrage_rows:
                row_id = row['RowID']
                vals = {
                    'base_id': base.id,
                    'qdv_row_id': row_id,
                    'description': row['Description'] or '',
                    'reference': row['Reference'] or '',
                    'famille_code': row['Family'] or '',
                    'manufacturer': row['Manufacturer'] or '',
                    'user_defined_field': row['UserDefinedField'] or '',
                    'unit': row['Unit'] or 'U',
                    'forced_selling_price': row['ForcedSellingPricePerUnit'] or 0.0,
                    'take_forced_price': bool(row['TakeForcedSellingPrice']),
                    'lock_the_group': bool(row['LockTheGroup']),
                    'article_date': row['ArticleDate'] or 0.0,
                    'alter_date': row['AlterDate'] or 0.0,
                    'last_user_information': row['LastUserInformation'] or '',
                    'is_modified': False,
                }

                if self.import_mode == 'update':
                    existing = self.env['qdv.ouvrage'].search([
                        ('base_id', '=', base.id),
                        ('qdv_row_id', '=', row_id)
                    ], limit=1)
                    if existing:
                        # Ne pas écraser si modifié dans Odoo
                        if not existing.is_modified:
                            # Utiliser super().write pour ne pas déclencher le tracking
                            existing.with_context(skip_modification_tracking=True).write(vals)
                            ouvrages_updated += 1
                        continue

                vals_list.append(vals)

            if vals_list:
                # Création en batch
                BATCH_SIZE = 100
                for i in range(0, len(vals_list), BATCH_SIZE):
                    batch = vals_list[i:i + BATCH_SIZE]
                    self.env['qdv.ouvrage'].with_context(
                        skip_modification_tracking=True
                    ).create(batch)
                    ouvrages_created += len(batch)

            log_lines.append(f'  ✅ {ouvrages_created} ouvrages créés, {ouvrages_updated} mis à jour')

            conn.close()

            # Mettre à jour l'état de la base
            base.state = 'imported'
            log_lines.append('\n✅ Import terminé avec succès !')

        except UserError:
            raise
        except Exception as e:
            _logger.exception('Erreur lors de l\'import .grp')
            log_lines.append(f'\n❌ ERREUR : {str(e)}')
            raise UserError(_('Erreur lors de l\'import : %s') % str(e))

        return {
            'log': '\n'.join(log_lines),
            'familles': familles_count,
            'ouvrages_created': ouvrages_created,
            'ouvrages_updated': ouvrages_updated,
        }
