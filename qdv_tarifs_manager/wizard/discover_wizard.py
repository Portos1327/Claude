# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Wizard de découverte des bases .qdb
Scanne le dossier Tarifs ID V2, lit BrowserFromLocal.txt, BrowserFromWeb.txt
et Rebates.qdbr pour enrichir les métadonnées de chaque base découverte.
Permet la sélection multiple avant import.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os
import sqlite3

_logger = logging.getLogger(__name__)


class QdvTarifDiscoverWizard(models.TransientModel):
    _name = 'qdv.tarif.discover.wizard'
    _description = 'Découverte des bases Tarifs QDV'

    config_id = fields.Many2one(
        'qdv.tarif.config',
        string='Configuration',
        required=True,
        ondelete='cascade'
    )
    tarifs_folder = fields.Char(
        string='Dossier',
        related='config_id.tarifs_folder',
        readonly=True
    )
    filter_manufacturer = fields.Char(
        string='Filtrer par fabricant',
        help='Code(s) fabricant à afficher séparés par espace ou virgule. Ex: BEG LEG SCH\n'
             'Laissez vide pour voir toutes les bases.'
    )

    # =========================================================================
    # RÉSULTATS DE LA DÉCOUVERTE
    # =========================================================================
    discovery_done = fields.Boolean(default=False)
    discovery_line_ids = fields.One2many(
        'qdv.tarif.discover.line',
        'wizard_id',
        string='Bases découvertes'
    )
    total_found = fields.Integer(string='Total bases', compute='_compute_totals')
    total_selected = fields.Integer(string='Sélectionnées', compute='_compute_totals')
    total_new = fields.Integer(string='Nouvelles', compute='_compute_totals')
    total_existing = fields.Integer(string='Existantes', compute='_compute_totals')

    # Log de découverte
    discovery_log = fields.Text(string='Journal de découverte', readonly=True)

    @api.depends('discovery_line_ids', 'discovery_line_ids.selected')
    def _compute_totals(self):
        for rec in self:
            lines = rec.discovery_line_ids
            rec.total_found = len(lines)
            rec.total_selected = len(lines.filtered('selected'))
            rec.total_new = len(lines.filtered(lambda l: l.status == 'new'))
            rec.total_existing = len(lines.filtered(lambda l: l.status == 'existing'))

    # =========================================================================
    # ACTIONS BOUTONS
    # =========================================================================
    def action_discover(self):
        """Lance la découverte des bases dans le dossier"""
        self.ensure_one()
        folder = self.config_id.tarifs_folder
        if not folder or not os.path.isdir(folder):
            raise UserError(_("Dossier inaccessible: %s") % folder)

        logs = []
        logs.append("=== DÉCOUVERTE: %s ===" % folder)

        # --- Lire BrowserFromLocal.txt ---
        browser_local = {}
        local_file = os.path.join(folder, 'BrowserFromLocal.txt')
        if os.path.isfile(local_file):
            browser_local = self._parse_browser_file(local_file)
            logs.append("BrowserFromLocal.txt: %d entrées lues" % len(browser_local))
        else:
            logs.append("BrowserFromLocal.txt: ABSENT")

        # --- Lire BrowserFromWeb.txt ---
        browser_web = {}
        web_file = os.path.join(folder, 'BrowserFromWeb.txt')
        if os.path.isfile(web_file):
            browser_web = self._parse_browser_file(web_file)
            logs.append("BrowserFromWeb.txt: %d entrées lues" % len(browser_web))
        else:
            logs.append("BrowserFromWeb.txt: ABSENT")

        # --- Lire Rebates.qdbr ---
        rebates_data = {}
        rebates_file = os.path.join(folder, 'Rebates.qdbr')
        if os.path.isfile(rebates_file):
            rebates_data = self._parse_rebates(rebates_file)
            logs.append("Rebates.qdbr: %d fabricants avec remises" % len(rebates_data))
        else:
            logs.append("Rebates.qdbr: ABSENT")

        # --- Scanner les fichiers .qdb ---
        qdb_files = []
        try:
            for fname in sorted(os.listdir(folder)):
                if fname.lower().endswith('.qdb'):
                    qdb_files.append(fname)
        except Exception as e:
            raise UserError(_("Erreur lecture dossier: %s") % str(e))

        logs.append("\nFichiers .qdb trouvés: %d" % len(qdb_files))

        # --- Fusionner les sources ---
        # Construire un dictionnaire unifié par code fabricant
        # Sources prioritaires: BrowserFromLocal > BrowserFromWeb > nom de fichier
        all_codes = set()
        all_codes.update(browser_local.keys())
        all_codes.update(browser_web.keys())

        # Aussi ajouter les codes depuis les noms de fichiers
        file_by_code = {}
        BaseModel = self.env['qdv.tarif.base']
        for fname in qdb_files:
            parsed = BaseModel.parse_filename(fname)
            if parsed:
                code = parsed['manufacturer_code']
                file_by_code[code] = {
                    'filename': fname,
                    'parsed': parsed,
                    'filepath': os.path.join(folder, fname),
                }
                all_codes.add(code)

        logs.append("Codes fabricants uniques: %d" % len(all_codes))

        # --- Appliquer filtre fabricant si renseigné ---
        if self.filter_manufacturer:
            # Accepte espaces, virgules ou points-virgules comme séparateurs
            import re as _re
            filter_codes = set(
                c.strip().upper()
                for c in _re.split(r'[,;\s]+', self.filter_manufacturer)
                if c.strip()
            )
            all_codes = all_codes.intersection(filter_codes)
            logs.append("Filtre fabricant actif: %s → %d code(s) correspondant(s)" % (
                ', '.join(sorted(filter_codes)), len(all_codes)
            ))

        # --- Créer les lignes de découverte ---
        # Supprimer les anciennes lignes
        self.discovery_line_ids.unlink()

        existing_bases = {b.manufacturer_code: b for b in self.env['qdv.tarif.base'].search([])}

        lines_to_create = []
        for code in sorted(all_codes):
            local_info = browser_local.get(code, {})
            web_info = browser_web.get(code, {})
            file_info = file_by_code.get(code, {})
            rebate_info = rebates_data.get(code, {})

            # Nom fabricant: local > web > rebates
            name = local_info.get('name') or web_info.get('name') or rebate_info.get('name') or code

            line_vals = {
                'wizard_id': self.id,
                'manufacturer_code': code,
                'manufacturer_name': name,
                'file_name': file_info.get('filename', ''),
                'file_path': file_info.get('filepath', ''),
                'file_exists': bool(file_info),
                # Depuis BrowserFromLocal
                'local_date': local_info.get('date', ''),
                'local_version': local_info.get('version', 0),
                'local_size': local_info.get('total_size', 0),
                'local_nb_parts': local_info.get('nb_parts', 1),
                # Depuis BrowserFromWeb
                'web_date': web_info.get('date', ''),
                'web_version': web_info.get('version', 0),
                'web_size': web_info.get('total_size', 0),
                # Remises
                'has_rebates': bool(rebate_info),
                'rebate_count': rebate_info.get('count', 0),
                'rebate_date': rebate_info.get('date', ''),
                # État
                'status': 'existing' if code in existing_bases else 'new',
                'existing_base_id': existing_bases.get(code, self.env['qdv.tarif.base']).id if code in existing_bases else False,
                # Sélection par défaut: sélectionner les nouvelles bases avec fichier présent
                'selected': bool(file_info) and code not in existing_bases,
            }
            lines_to_create.append(line_vals)

        if lines_to_create:
            self.env['qdv.tarif.discover.line'].create(lines_to_create)

        self.write({
            'discovery_done': True,
            'discovery_log': '\n'.join(logs),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.tarif.discover.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_select_all(self):
        """Sélectionne toutes les lignes avec fichier présent"""
        self.ensure_one()
        self.discovery_line_ids.filtered('file_exists').write({'selected': True})
        return {'type': 'ir.actions.act_window', 'res_model': 'qdv.tarif.discover.wizard',
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_deselect_all(self):
        """Désélectionne toutes les lignes"""
        self.ensure_one()
        self.discovery_line_ids.write({'selected': False})
        return {'type': 'ir.actions.act_window', 'res_model': 'qdv.tarif.discover.wizard',
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_select_new_only(self):
        """Sélectionne uniquement les nouvelles bases (non encore en base Odoo)"""
        self.ensure_one()
        for line in self.discovery_line_ids:
            line.selected = (line.status == 'new' and line.file_exists)
        return {'type': 'ir.actions.act_window', 'res_model': 'qdv.tarif.discover.wizard',
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_confirm_selection(self):
        """
        Valide la sélection:
        - Crée les nouvelles qdv.tarif.base
        - Met à jour les existantes
        - Importe les remises depuis Rebates.qdbr
        """
        self.ensure_one()
        selected = self.discovery_line_ids.filtered('selected')
        if not selected:
            raise UserError(_("Aucune base sélectionnée. Veuillez cocher au moins une base."))

        folder = self.config_id.tarifs_folder
        rebates_file = os.path.join(folder, 'Rebates.qdbr')
        rebates_data = {}
        if os.path.isfile(rebates_file):
            rebates_data = self._parse_rebates(rebates_file, include_lines=True)

        created = 0
        updated = 0
        rebates_imported = 0

        for line in selected:
            # Convertir la date tarif
            tarif_date = self._parse_date(line.local_date or line.web_date)

            base_vals = {
                'manufacturer_code': line.manufacturer_code,
                'manufacturer_name': line.manufacturer_name,
                'file_name': line.file_name,
                'file_path': line.file_path,
                'tarif_date': tarif_date,
                'version': line.local_version or line.web_version or 1,
                'total_size': line.local_size or line.web_size or 0,
                'nb_parts': line.local_nb_parts or 1,
                'part_size': line.local_size or 0,
                'local_size': line.local_size or 0,
                'web_size': line.web_size or 0,
            }

            if line.existing_base_id:
                line.existing_base_id.write(base_vals)
                base = line.existing_base_id
                updated += 1
            else:
                base = self.env['qdv.tarif.base'].create(base_vals)
                created += 1

            # Importer les remises si disponibles
            code = line.manufacturer_code
            if code in rebates_data and rebates_data[code].get('lines'):
                # Supprimer les anciennes remises
                base.rebate_ids.unlink()
                # Créer les nouvelles
                for rebate_line in rebates_data[code]['lines']:
                    rebate_line['base_id'] = base.id
                    self.env['qdv.tarif.rebate'].create(rebate_line)
                    rebates_imported += 1

                # Mettre à jour la date remise
                rebate_date = rebates_data[code].get('date')
                if rebate_date:
                    base.write({
                        'rebate_date': self._parse_julian_date(rebate_date),
                        'rebate_version': rebates_data[code].get('version', 1),
                    })

        message = _("Découverte terminée:\n- %d bases créées\n- %d bases mises à jour\n- %d familles remises importées") % (
            created, updated, rebates_imported
        )

        # Odoo 18: display_notification avec 'next' imbriqué n'est pas supporté
        # → on retourne directement l'action de navigation vers les bases
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bases Tarifs QDV'),
            'res_model': 'qdv.tarif.base',
            'view_mode': 'list,form',
        }

    # =========================================================================
    # MÉTHODES UTILITAIRES
    # =========================================================================
    def _parse_browser_file(self, filepath):
        """
        Parse BrowserFromLocal.txt ou BrowserFromWeb.txt
        Format: CODE;NOM;YYYYMMDD;VERSION;TAILLE_TOTALE;NB_PARTIES;FLAG;TAILLE_PARTIE
        Retourne: dict {CODE: {name, date, version, total_size, nb_parts, part_size}}
        """
        result = {}
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(';')
                    if len(parts) < 5:
                        continue
                    code = parts[0].strip()
                    result[code] = {
                        'name': parts[1].strip() if len(parts) > 1 else code,
                        'date': parts[2].strip() if len(parts) > 2 else '',
                        'version': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1,
                        'total_size': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                        'nb_parts': int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 1,
                        'part_size': int(parts[7]) if len(parts) > 7 and parts[7].isdigit() else 0,
                    }
        except Exception as e:
            _logger.warning("Erreur lecture %s: %s", filepath, str(e))
        return result

    def _parse_rebates(self, filepath, include_lines=False):
        """
        Parse Rebates.qdbr (base SQLite)
        Tables: Rebates, Rebates_Header, Rebates_SettingsTable
        Retourne: dict {CODE: {name, date, version, count, lines: [...]}}
        """
        result = {}
        try:
            conn = sqlite3.connect(filepath)
            cur = conn.cursor()

            # Lire les headers (1 ligne par fabricant)
            cur.execute("""
                SELECT ManufacturerCode, ManufacturerName, Date, Version
                FROM Rebates_Header
            """)
            for row in cur.fetchall():
                code, name, date_julian, version = row
                if code:
                    result[code] = {
                        'name': name or code,
                        'date': date_julian,
                        'version': version or 1,
                        'count': 0,
                        'lines': [],
                    }

            # Compter et lire les remises
            cur.execute("""
                SELECT ManufacturerCode, RebateCode, Rebate, DerogationRebate,
                       UseDerogation, RebateLabel, RebateComment
                FROM Rebates
                ORDER BY ManufacturerCode, RebateCode
            """)
            for row in cur.fetchall():
                (mfr_code, rebate_code, rebate_val, derog_val,
                 use_derog, label, comment) = row
                if mfr_code and mfr_code in result:
                    result[mfr_code]['count'] += 1
                    if include_lines:
                        result[mfr_code]['lines'].append({
                            'rebate_code': rebate_code or '',
                            'rebate_label': label or '',
                            'rebate_value': float(rebate_val or 0),
                            'negotiated_value': float(derog_val or 0),
                            'use_negotiated': bool(use_derog),
                            'rebate_comment': comment or '',
                        })

            conn.close()
        except Exception as e:
            _logger.error("Erreur lecture Rebates.qdbr: %s", str(e))
        return result

    def _parse_date(self, date_str):
        """Convertit YYYYMMDD en date Odoo ou None"""
        if not date_str or len(date_str) < 8:
            return False
        try:
            date_str = date_str.replace('.', '').replace('-', '')[:8]
            if len(date_str) == 8 and date_str.isdigit():
                return '%s-%s-%s' % (date_str[:4], date_str[4:6], date_str[6:8])
        except Exception:
            pass
        return False

    def _parse_julian_date(self, julian):
        """Convertit une date julienne (float SQLite) en date Odoo"""
        if not julian:
            return False
        try:
            # Date julienne SQLite: jours depuis 4714 av. J.-C.
            # 2415020.5 = 1900-01-00, mais on utilise une approximation
            # Plus simple: ignorer si on n'a pas la valeur YYYYMMDD
            julian = float(julian)
            # Approximation grossière pour les dates > 2400000
            if julian > 2400000:
                # Convertir en timestamp Unix approximatif
                days_from_epoch = julian - 2440587.5  # epoch Julian day
                import datetime
                d = datetime.date(1970, 1, 1) + datetime.timedelta(days=days_from_epoch)
                return d.strftime('%Y-%m-%d')
        except Exception:
            pass
        return False


class QdvTarifDiscoverLine(models.TransientModel):
    """Ligne de résultat de découverte - une ligne par base .qdb trouvée"""
    _name = 'qdv.tarif.discover.line'
    _description = 'Ligne découverte base QDV'
    _order = 'manufacturer_code'

    wizard_id = fields.Many2one('qdv.tarif.discover.wizard', required=True, ondelete='cascade')

    # =========================================================================
    # IDENTIFICATION
    # =========================================================================
    manufacturer_code = fields.Char(string='Code', required=True)
    manufacturer_name = fields.Char(string='Fabricant')
    file_name = fields.Char(string='Fichier .qdb')
    file_path = fields.Char(string='Chemin')
    file_exists = fields.Boolean(string='Fichier présent')

    # =========================================================================
    # MÉTADONNÉES LOCAL
    # =========================================================================
    local_date = fields.Char(string='Date (local)')
    local_version = fields.Integer(string='V. locale')
    local_size = fields.Integer(string='Taille locale')
    local_nb_parts = fields.Integer(string='Parties')

    # =========================================================================
    # MÉTADONNÉES WEB
    # =========================================================================
    web_date = fields.Char(string='Date (web)')
    web_version = fields.Integer(string='V. web')
    web_size = fields.Integer(string='Taille web')

    # =========================================================================
    # REMISES
    # =========================================================================
    has_rebates = fields.Boolean(string='Remises disponibles')
    rebate_count = fields.Integer(string='Nb familles remises')
    rebate_date = fields.Float(string='Date remises (julian)')

    # =========================================================================
    # ÉTAT ET SÉLECTION
    # =========================================================================
    status = fields.Selection([
        ('new', 'Nouvelle'),
        ('existing', 'Existante'),
    ], string='État', default='new')
    existing_base_id = fields.Many2one('qdv.tarif.base', string='Base existante')
    selected = fields.Boolean(string='Sélectionner', default=False)

    # Indicateur couleur
    status_color = fields.Integer(
        string='Couleur',
        compute='_compute_status_color'
    )

    @api.depends('status', 'file_exists', 'has_rebates')
    def _compute_status_color(self):
        for rec in self:
            if not rec.file_exists:
                rec.status_color = 2   # rouge: fichier absent
            elif rec.status == 'new':
                rec.status_color = 10  # vert: nouvelle base
            elif rec.status == 'existing':
                rec.status_color = 4   # bleu: déjà en base
            else:
                rec.status_color = 0
