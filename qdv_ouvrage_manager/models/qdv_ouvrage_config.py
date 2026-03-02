# -*- coding: utf-8 -*-
import os
import sqlite3
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

# Chemin par défaut (Google Drive Dimitri)
DEFAULT_FOLDER = r'C:\Users\dimitri\Mon Drive\Base QDV\Base article et ouvrage'


class QdvOuvrageConfig(models.Model):
    """Configuration du module QDV Ouvrage Manager"""
    _name = 'qdv.ouvrage.config'
    _description = 'Configuration QDV Ouvrage Manager'
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        default='Configuration QDV Ouvrages',
        readonly=True
    )

    # =========================================================
    # Dossier de découverte
    # =========================================================
    discovery_folder = fields.Char(
        string='Dossier de découverte',
        default=DEFAULT_FOLDER,
        required=True,
        help='Dossier racine où sont stockés les fichiers .grp (bases d\'ouvrage QDV7).\n'
             'Ex: C:\\Users\\dimitri\\Mon Drive\\Base QDV\\Base article et ouvrage\n'
             'La recherche est récursive dans les sous-dossiers.'
    )
    scan_recursive = fields.Boolean(
        string='Recherche récursive',
        default=True,
        help='Si coché, recherche les fichiers .grp dans tous les sous-dossiers'
    )
    auto_import_new = fields.Boolean(
        string='Import automatique des nouveaux fichiers',
        default=False,
        help='Si coché, importe automatiquement les nouveaux fichiers .grp détectés'
    )

    # =========================================================
    # CRON
    # =========================================================
    cron_active = fields.Boolean(
        string='Surveillance automatique active',
        default=False,
        help='Active la surveillance périodique du dossier'
    )
    cron_interval = fields.Selection([
        ('hourly', 'Toutes les heures'),
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
    ], string='Fréquence surveillance', default='daily')

    # =========================================================
    # Statistiques
    # =========================================================
    last_scan_date = fields.Datetime(string='Dernier scan', readonly=True)
    last_scan_found = fields.Integer(string='Fichiers trouvés', readonly=True)
    last_scan_log = fields.Text(string='Log dernier scan', readonly=True)

    # =========================================================
    # Actions
    # =========================================================
    def action_test_folder(self):
        """Vérifie que le dossier de découverte est accessible"""
        self.ensure_one()
        folder = self.discovery_folder
        if not folder:
            raise UserError(_('Le dossier de découverte n\'est pas configuré.'))

        # Normaliser le chemin (Windows/Linux)
        folder = os.path.normpath(folder)

        if not os.path.exists(folder):
            raise UserError(_(
                'Le dossier n\'est pas accessible :\n%s\n\n'
                'Vérifiez que :\n'
                '• Le chemin est correct\n'
                '• Google Drive est synchronisé\n'
                '• Le service Odoo a accès à ce dossier'
            ) % folder)

        if not os.path.isdir(folder):
            raise UserError(_('Le chemin indiqué n\'est pas un dossier : %s') % folder)

        # Compter les .grp présents
        count = self._count_grp_files(folder)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Dossier accessible'),
                'message': _('%d fichier(s) .grp trouvé(s) dans ce dossier.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_open_discovery_wizard(self):
        """Ouvre le wizard de découverte des fichiers .grp"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': '🔍 Découverte des bases d\'ouvrage',
            'res_model': 'qdv.discovery.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id},
        }

    def _count_grp_files(self, folder):
        """Compte les fichiers .grp dans le dossier"""
        count = 0
        try:
            if self.scan_recursive:
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        if f.lower().endswith('.grp'):
                            count += 1
            else:
                for f in os.listdir(folder):
                    if f.lower().endswith('.grp'):
                        count += 1
        except Exception as e:
            _logger.warning('Erreur comptage fichiers .grp: %s', e)
        return count

    def scan_folder(self):
        """
        Scanne le dossier de découverte et retourne la liste des fichiers .grp trouvés.
        Retourne une liste de dicts avec les infos de chaque fichier.
        """
        self.ensure_one()
        folder = os.path.normpath(self.discovery_folder or DEFAULT_FOLDER)
        results = []

        if not os.path.exists(folder):
            _logger.warning('Dossier de découverte inaccessible: %s', folder)
            return results

        try:
            if self.scan_recursive:
                file_paths = []
                for root, dirs, files in os.walk(folder):
                    for fname in files:
                        if fname.lower().endswith('.grp'):
                            file_paths.append(os.path.join(root, fname))
            else:
                file_paths = [
                    os.path.join(folder, f)
                    for f in os.listdir(folder)
                    if f.lower().endswith('.grp')
                ]

            for fpath in sorted(file_paths):
                info = self._get_grp_file_info(fpath)
                if info:
                    results.append(info)

        except Exception as e:
            _logger.error('Erreur scan dossier %s: %s', folder, e)

        # Mise à jour stats
        self.write({
            'last_scan_date': fields.Datetime.now(),
            'last_scan_found': len(results),
            'last_scan_log': f'Scan du {fields.Datetime.now()}: {len(results)} fichier(s) trouvé(s)',
        })

        return results

    def _get_grp_file_info(self, fpath):
        """
        Analyse un fichier .grp et retourne ses métadonnées.
        Retourne None si le fichier n'est pas un .grp QDV7 valide.
        """
        try:
            stat = os.stat(fpath)
            fname = os.path.basename(fpath)
            folder = self.discovery_folder or DEFAULT_FOLDER
            rel_path = os.path.relpath(fpath, folder)

            info = {
                'file_path': fpath,
                'file_name': fname,
                'relative_path': rel_path,
                'file_size': stat.st_size,
                'file_mtime': stat.st_mtime,
                'is_valid_qdv': False,
                'file_version': 0.0,
                'ouvrage_count': 0,
                'famille_count': 0,
                'already_imported': False,
                'existing_base_id': None,
                'existing_base_name': None,
                'needs_update': False,
            }

            # Vérifier si c'est un SQLite valide avec les tables QDV7
            try:
                conn = sqlite3.connect(fpath)
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = {r[0] for r in cur.fetchall()}

                if {'Groups', 'TreeTable', 'SettingsTable'}.issubset(tables):
                    info['is_valid_qdv'] = True

                    # Version
                    cur.execute("SELECT VariableValue FROM SettingsTable WHERE VariableName = '#FILEVERSION#'")
                    row = cur.fetchone()
                    info['file_version'] = row[0] if row else 0.0

                    # Nombre d'ouvrages et familles
                    cur.execute("SELECT COUNT(*) FROM Groups")
                    info['ouvrage_count'] = cur.fetchone()[0]

                    cur.execute("SELECT COUNT(*) FROM TreeTable")
                    info['famille_count'] = cur.fetchone()[0]

                conn.close()
            except Exception:
                info['is_valid_qdv'] = False

            # Vérifier si déjà importé dans Odoo
            existing = self.env['qdv.ouvrage.base'].search([
                ('file_path', '=', fpath)
            ], limit=1)
            if existing:
                info['already_imported'] = True
                info['existing_base_id'] = existing.id
                info['existing_base_name'] = existing.name
                # Vérifier si le fichier a été modifié depuis le dernier import
                if existing.date_import:
                    import datetime
                    import_ts = existing.date_import.timestamp()
                    info['needs_update'] = stat.st_mtime > import_ts

            return info

        except Exception as e:
            _logger.warning('Erreur analyse fichier %s: %s', fpath, e)
            return None

    @api.model
    def cron_scan_and_import(self):
        """Méthode appelée par le CRON de surveillance"""
        config = self.search([], limit=1)
        if not config or not config.cron_active:
            return

        _logger.info('QDV Ouvrage Manager: scan automatique du dossier %s', config.discovery_folder)
        files = config.scan_folder()

        if config.auto_import_new:
            for f in files:
                if not f['already_imported'] and f['is_valid_qdv']:
                    try:
                        # Créer la base et importer automatiquement
                        base_name = os.path.splitext(f['file_name'])[0]
                        base = self.env['qdv.ouvrage.base'].create({
                            'name': base_name,
                            'file_path': f['file_path'],
                        })
                        # Lancer l'import depuis le chemin serveur
                        base._import_from_server_path(f['file_path'])
                        _logger.info('Auto-import: %s → base "%s"', f['file_name'], base_name)
                    except Exception as e:
                        _logger.error('Erreur auto-import %s: %s', f['file_name'], e)

    @api.model
    def get_or_create_config(self):
        """Retourne la configuration unique, la crée si nécessaire"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({'name': 'Configuration QDV Ouvrages'})
        return config
