# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Modèle Base Tarif
Représente une base article fournisseur .qdb découverte dans le dossier Tarifs ID V2
Format du nom de fichier: CODE [DATE - VXXXXXXX].qdb   ex: LEG [2026.02.02 - 0000002].qdb
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os
import re
import sqlite3

_logger = logging.getLogger(__name__)


class QdvTarifBase(models.Model):
    _name = 'qdv.tarif.base'
    _description = 'Base Tarif QDV Fournisseur'
    _order = 'manufacturer_code'
    _rec_name = 'manufacturer_code'  # Affiche "BEG" au lieu de "qdv.tarif.base,4"

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    manufacturer_code = fields.Char(
        string='Code Fabricant',
        required=True,
        index=True,
        help='Code 3 lettres du fabricant (ex: LEG, HAG, SCH)'
    )
    manufacturer_name = fields.Char(
        string='Nom Fabricant',
        required=True,
        help='Nom complet du fabricant (ex: LEGRAND)'
    )
    file_name = fields.Char(
        string='Nom du fichier',
        help='Nom du fichier .qdb (ex: LEG [2026.02.02 - 0000002].qdb)'
    )
    file_path = fields.Char(
        string='Chemin complet',
        help='Chemin absolu vers le fichier .qdb'
    )

    # =========================================================================
    # MÉTADONNÉES (depuis BrowserFromLocal / BrowserFromWeb)
    # =========================================================================
    tarif_date = fields.Date(
        string='Date tarif',
        help='Date de mise à jour du tarif (format YYYYMMDD dans les fichiers Browser)'
    )
    version = fields.Integer(
        string='Version',
        default=1,
        help='Numéro de version de la base'
    )
    total_size = fields.Integer(
        string='Taille totale (octets)',
        help='Taille totale de la base'
    )
    nb_parts = fields.Integer(
        string='Nb parties',
        default=1,
        help='Nombre de parties si base multi-parties'
    )
    part_size = fields.Integer(
        string='Taille partie (octets)',
        help='Taille de la partie principale'
    )

    # Différence local vs web
    local_size = fields.Integer(string='Taille locale', help='Taille selon BrowserFromLocal.txt')
    web_size = fields.Integer(string='Taille web', help='Taille selon BrowserFromWeb.txt')
    size_differs = fields.Boolean(
        string='Différence local/web',
        compute='_compute_size_differs',
        store=True,
        help='Indique si la taille diffère entre la version locale et web'
    )

    # =========================================================================
    # REMISES (depuis Rebates.qdbr)
    # =========================================================================
    rebate_count = fields.Integer(
        string='Nb familles remises',
        compute='_compute_rebate_count'
    )
    rebate_ids = fields.One2many(
        'qdv.tarif.rebate',
        'base_id',
        string='Remises par famille'
    )
    rebate_date = fields.Date(
        string='Date remises',
        help='Date de mise à jour des remises dans Rebates.qdbr'
    )
    rebate_version = fields.Integer(
        string='Version remises',
        default=1
    )

    # =========================================================================
    # SÉLECTION POUR IMPORT
    # =========================================================================
    selected = fields.Boolean(
        string='Sélectionné',
        default=False,
        help='Sélectionner cette base pour import dans Odoo'
    )
    import_state = fields.Selection([
        ('not_imported', 'Non importé'),
        ('imported', 'Importé'),
        ('partial', 'Partiel'),
        ('error', 'Erreur'),
    ], string='État import', default='not_imported')
    last_import_date = fields.Datetime(string='Dernier import', readonly=True)
    import_error = fields.Text(string='Erreur import', readonly=True)

    # =========================================================================
    # ARTICLES IMPORTÉS
    # =========================================================================
    article_count = fields.Integer(
        string='Articles importés',
        compute='_compute_article_count'
    )
    article_ids = fields.One2many(
        'qdv.tarif.article',
        'base_id',
        string='Articles'
    )
    derogation_ids = fields.One2many(
        'qdv.tarif.derogation',
        'base_id',
        string='Dérogations'
    )
    derogation_count = fields.Integer(
        string='Nb dérogations',
        compute='_compute_derogation_count'
    )
    family_ids = fields.One2many(
        'qdv.tarif.family',
        'base_id',
        string='Familles'
    )
    family_count = fields.Integer(
        string='Nb familles',
        compute='_compute_family_count'
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('local_size', 'web_size')
    def _compute_size_differs(self):
        for rec in self:
            rec.size_differs = bool(rec.local_size and rec.web_size and rec.local_size != rec.web_size)

    def _compute_rebate_count(self):
        for rec in self:
            rec.rebate_count = len(rec.rebate_ids)

    def _compute_article_count(self):
        for rec in self:
            rec.article_count = len(rec.article_ids)

    def _compute_derogation_count(self):
        for rec in self:
            rec.derogation_count = len(rec.derogation_ids)

    def _compute_family_count(self):
        for rec in self:
            rec.family_count = len(rec.family_ids)

    # =========================================================================
    # PARSING NOM DE FICHIER
    # =========================================================================
    @api.model
    def parse_filename(self, filename):
        """
        Parse le nom d'un fichier .qdb et retourne les métadonnées
        Format attendu: CODE [YYYY.MM.DD - NNNNNNN].qdb
        Exemple: LEG [2026.02.02 - 0000002].qdb
        Retourne: dict avec code, date_str, version_num ou None si non parsable
        """
        # Enlever l'extension
        basename = os.path.splitext(filename)[0]
        # Pattern: CODE [YYYY.MM.DD - NNNNNNN]
        pattern = r'^([A-Z0-9]{2,5})\s*\[(\d{4}\.\d{2}\.\d{2})\s*-\s*(\d+)\]$'
        match = re.match(pattern, basename.strip())
        if match:
            code = match.group(1)
            date_str = match.group(2).replace('.', '-')  # -> YYYY-MM-DD
            version_num = int(match.group(3))
            return {
                'manufacturer_code': code,
                'date_str': date_str,
                'version_num': version_num,
            }
        # Format alternatif sans crochets: juste CODE
        simple = re.match(r'^([A-Z0-9]{2,5})$', basename.strip())
        if simple:
            return {'manufacturer_code': simple.group(1), 'date_str': None, 'version_num': 1}
        return None

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_import_articles(self):
        """Lance le wizard d'import pour cette base"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Import articles - %s') % self.manufacturer_name,
            'res_model': 'qdv.tarif.import.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_base_ids': [self.id],
                'default_single_base_id': self.id,
            },
        }

    def action_view_articles(self):
        """Ouvre la liste des articles de cette base"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articles - %s') % self.manufacturer_name,
            'res_model': 'qdv.tarif.article',
            'view_mode': 'list,form',
            'domain': [('base_id', '=', self.id)],
        }

    def action_view_rebates(self):
        """Ouvre les remises de cette base"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Remises - %s') % self.manufacturer_name,
            'res_model': 'qdv.tarif.rebate',
            'view_mode': 'list',
            'domain': [('base_id', '=', self.id)],
        }

    def action_view_derogations(self):
        """Ouvre les dérogations de cette base"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Dérogations - %s') % self.manufacturer_name,
            'res_model': 'qdv.tarif.derogation',
            'view_mode': 'list,form',
            'domain': [('manufacturer_code', '=', self.manufacturer_code)],
            'context': {'default_manufacturer_code': self.manufacturer_code},
        }

    def action_view_families(self):
        """Ouvre les familles de cette base"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Familles - %s') % self.manufacturer_name,
            'res_model': 'qdv.tarif.family',
            'view_mode': 'list,form',
            'domain': [('base_id', '=', self.id)],
            'context': {'search_default_group_lvl1': 1},
        }

    def action_scan_qdb(self):
        """Scanne le fichier .qdb pour obtenir des informations sur la structure"""
        self.ensure_one()
        if not self.file_path or not os.path.isfile(self.file_path):
            raise UserError(_("Fichier .qdb introuvable: %s") % (self.file_path or 'Non défini'))

        try:
            conn = sqlite3.connect(self.file_path)
            cur = conn.cursor()

            # Lister les tables
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cur.fetchall()]

            info_lines = [
                "=== SCAN BASE: %s ===" % self.manufacturer_name,
                "Fichier: %s" % os.path.basename(self.file_path),
                "Taille: %s octets" % self.total_size,
                "",
                "Tables trouvées: %s" % ', '.join(tables),
            ]

            # Pour chaque table, compter les lignes et lister les colonnes
            for table in tables:
                try:
                    cur.execute("SELECT COUNT(*) FROM %s" % table)
                    count = cur.fetchone()[0]
                    cur.execute("PRAGMA table_info(%s)" % table)
                    cols = [row[1] for row in cur.fetchall()]
                    info_lines.append("")
                    info_lines.append("  Table [%s] - %d lignes" % (table, count))
                    info_lines.append("  Colonnes: %s" % ', '.join(cols))
                    # Aperçu 2 premières lignes
                    cur.execute("SELECT * FROM %s LIMIT 2" % table)
                    rows = cur.fetchall()
                    for row in rows:
                        info_lines.append("    > %s" % str(row)[:200])
                except Exception as e:
                    info_lines.append("  [%s] Erreur: %s" % (table, str(e)))

            conn.close()
            content = '\n'.join(info_lines)

            # Afficher dans un wizard de résultat
            return {
                'type': 'ir.actions.act_window',
                'name': _('Scan QDB - %s') % self.manufacturer_name,
                'res_model': 'qdv.tarif.scan.result',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_base_id': self.id,
                    'default_content': content,
                },
            }

        except Exception as e:
            raise UserError(_("Erreur lors du scan: %s") % str(e))

    # =========================================================================
    # SÉLECTION EN MASSE (appelées depuis la liste)
    # =========================================================================
    @api.model
    def action_select_all(self):
        """Sélectionne toutes les bases"""
        self.search([]).write({'selected': True})
        return True

    @api.model
    def action_deselect_all(self):
        """Désélectionne toutes les bases"""
        self.search([]).write({'selected': False})
        return True

    def action_toggle_selected(self):
        """Bascule la sélection des enregistrements courants"""
        for rec in self:
            rec.selected = not rec.selected
