# -*- coding: utf-8 -*-
import os
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QdvDiscoveryWizard(models.TransientModel):
    """Wizard de découverte automatique des bases d'ouvrage .grp"""
    _name = 'qdv.discovery.wizard'
    _description = 'Découverte des bases d\'ouvrage QDV7'

    config_id = fields.Many2one(
        'qdv.ouvrage.config',
        string='Configuration',
        required=True
    )
    state = fields.Selection([
        ('scan', 'Scan'),
        ('results', 'Résultats'),
        ('done', 'Terminé'),
    ], default='scan')

    discovered_ids = fields.One2many(
        'qdv.discovered.file',
        'wizard_id',
        string='Fichiers découverts'
    )
    total_found = fields.Integer(string='Total trouvés', readonly=True)
    total_new = fields.Integer(string='Nouveaux', readonly=True)
    total_update = fields.Integer(string='À mettre à jour', readonly=True)
    total_already = fields.Integer(string='Déjà importés', readonly=True)
    result_log = fields.Text(string='Journal', readonly=True)

    # ── CORRECTION BUG #1 : default_get sur la bonne classe ─────────────
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if 'config_id' in fields_list and not res.get('config_id'):
            config = self.env['qdv.ouvrage.config'].get_or_create_config()
            res['config_id'] = config.id
        return res

    def action_scan(self):
        """Lance le scan du dossier configuré"""
        self.ensure_one()
        config = self.config_id

        folder = config.discovery_folder
        if not folder or not os.path.exists(os.path.normpath(folder)):
            raise UserError(_(
                'Le dossier de découverte est inaccessible :\n%s\n\n'
                'Configurez le bon chemin dans QDV Ouvrages → Configuration.'
            ) % (folder or '(non défini)'))

        self.discovered_ids.unlink()
        files = config.scan_folder()

        if not files:
            raise UserError(_(
                'Aucun fichier .grp trouvé dans :\n%s\n\n'
                'Vérifiez que des bases d\'ouvrage QDV7 sont présentes dans ce dossier.'
            ) % folder)

        lines = []
        new_count = update_count = already_count = 0

        for f in files:
            if not f.get('is_valid_qdv'):
                status, action = 'invalid', 'skip'
            elif f.get('already_imported') and not f.get('needs_update'):
                status, action = 'imported', 'skip'
                already_count += 1
            elif f.get('already_imported') and f.get('needs_update'):
                status, action = 'update', 'update'
                update_count += 1
            else:
                status, action = 'new', 'import'
                new_count += 1

            lines.append({
                'wizard_id': self.id,
                'file_path': f['file_path'],
                'file_name': f['file_name'],
                'relative_path': f['relative_path'],
                'file_size': f['file_size'],
                'file_version': f['file_version'],
                'ouvrage_count': f['ouvrage_count'],
                'famille_count': f['famille_count'],
                'status': status,
                'action': action,
                'existing_base_id': f.get('existing_base_id'),
                'existing_base_name': f.get('existing_base_name') or '',
                'selected': action in ('import', 'update'),
            })

        if lines:
            self.env['qdv.discovered.file'].create(lines)

        log_lines = [
            f'📁 Dossier : {folder}',
            f'🔍 Fichiers .grp trouvés : {len(files)}',
            f'  🆕 Nouveaux à importer : {new_count}',
            f'  🔄 À mettre à jour : {update_count}',
            f'  ✅ Déjà à jour : {already_count}',
        ]

        self.write({
            'state': 'results',
            'total_found': len(files),
            'total_new': new_count,
            'total_update': update_count,
            'total_already': already_count,
            'result_log': '\n'.join(log_lines),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.discovery.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_import_selected(self):
        """Importe les fichiers sélectionnés"""
        self.ensure_one()
        to_process = self.discovered_ids.filtered(
            lambda l: l.selected and l.status in ('new', 'update')
        )

        if not to_process:
            raise UserError(_('Aucun fichier sélectionné pour l\'import.'))

        imported_count = updated_count = 0
        error_lines = []
        log_lines = [f'\n🚀 Import de {len(to_process)} fichier(s)...\n']

        for line in to_process:
            try:
                if line.status == 'new':
                    base_name = os.path.splitext(line.file_name)[0]
                    base = self.env['qdv.ouvrage.base'].create({
                        'name': base_name,
                        'file_path': line.file_path,
                    })
                    result = base._import_from_server_path(line.file_path)
                    log_lines.append(
                        f'  🆕 {line.file_name} → "{base_name}" '
                        f'({result["ouvrages_created"]} ouvrages, {result["familles"]} familles)'
                    )
                    imported_count += 1

                elif line.status == 'update' and line.existing_base_id:
                    base = self.env['qdv.ouvrage.base'].browse(line.existing_base_id)
                    result = base._import_from_server_path(line.file_path)
                    log_lines.append(
                        f'  🔄 {line.file_name} → "{base.name}" mis à jour '
                        f'({result["ouvrages_created"]} ouvrages recréés)'
                    )
                    updated_count += 1

            except Exception as e:
                error_lines.append(f'  ❌ {line.file_name}: {str(e)}')
                _logger.error('Erreur import découverte %s: %s', line.file_path, e)

        if error_lines:
            log_lines.append('\n⚠️ Erreurs :')
            log_lines.extend(error_lines)

        log_lines.append(
            f'\n✅ Terminé : {imported_count} importé(s), {updated_count} mis à jour'
        )

        self.write({
            'state': 'done',
            'result_log': '\n'.join(log_lines),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.discovery.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_select_all_new(self):
        self.discovered_ids.filtered(lambda l: l.status == 'new').write({'selected': True})
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_select_all_update(self):
        self.discovered_ids.filtered(lambda l: l.status == 'update').write({'selected': True})
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}

    def action_deselect_all(self):
        self.discovered_ids.write({'selected': False})
        return {'type': 'ir.actions.act_window', 'res_model': self._name,
                'res_id': self.id, 'view_mode': 'form', 'target': 'new'}


class QdvDiscoveredFile(models.TransientModel):
    """Ligne de résultat de découverte"""
    _name = 'qdv.discovered.file'
    _description = 'Fichier .grp découvert'
    _order = 'status, file_name'

    wizard_id = fields.Many2one('qdv.discovery.wizard', ondelete='cascade')
    selected = fields.Boolean(string='✓', default=False)
    file_name = fields.Char(string='Fichier', readonly=True)
    relative_path = fields.Char(string='Chemin relatif', readonly=True)
    file_path = fields.Char(string='Chemin complet', readonly=True)
    file_size = fields.Integer(string='Taille (octets)', readonly=True)
    file_version = fields.Float(string='Version QDV', readonly=True)
    ouvrage_count = fields.Integer(string='Ouvrages', readonly=True)
    famille_count = fields.Integer(string='Familles', readonly=True)
    status = fields.Selection([
        ('new', 'Nouveau'),
        ('update', 'À mettre à jour'),
        ('imported', 'Déjà importé'),
        ('invalid', 'Invalide'),
    ], string='Statut', readonly=True)
    action = fields.Selection([
        ('import', 'Importer'),
        ('update', 'Mettre à jour'),
        ('skip', 'Ignorer'),
    ], string='Action', readonly=True)
    existing_base_id = fields.Integer(string='ID base existante', readonly=True)
    existing_base_name = fields.Char(string='Base existante', readonly=True)
    file_size_kb = fields.Float(string='Taille (Ko)', compute='_compute_size_kb', readonly=True)

    @api.depends('file_size')
    def _compute_size_kb(self):
        for rec in self:
            rec.file_size_kb = round(rec.file_size / 1024, 1) if rec.file_size else 0.0
