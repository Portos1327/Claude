# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os

_logger = logging.getLogger(__name__)


class QdvOuvrageBase(models.Model):
    """Représente une base d'ouvrage QDV7 (fichier .grp)"""
    _name = 'qdv.ouvrage.base'
    _description = 'Base d\'ouvrage QDV7'
    _order = 'name'

    name = fields.Char(
        string='Nom de la base',
        required=True,
        help='Nom descriptif de la base d\'ouvrage (ex: Base Turquand)'
    )
    file_path = fields.Char(
        string='Chemin du fichier .grp',
        help='Chemin complet vers le fichier SQLite .grp sur le serveur'
    )
    file_version = fields.Float(
        string='Version fichier QDV',
        readonly=True
    )
    description = fields.Text(
        string='Description'
    )
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('imported', 'Importé'),
        ('modified', 'Modifié'),
        ('exported', 'Exporté'),
    ], string='État', default='draft', readonly=True)

    ouvrage_ids = fields.One2many(
        'qdv.ouvrage',
        'base_id',
        string='Ouvrages'
    )
    famille_ids = fields.One2many(
        'qdv.ouvrage.famille',
        'base_id',
        string='Familles'
    )

    ouvrage_count = fields.Integer(
        string='Nb ouvrages',
        compute='_compute_counts'
    )
    famille_count = fields.Integer(
        string='Nb familles',
        compute='_compute_counts'
    )
    modified_count = fields.Integer(
        string='Nb modifiés',
        compute='_compute_counts'
    )

    date_import = fields.Datetime(string='Date import', readonly=True)
    date_export = fields.Datetime(string='Dernier export', readonly=True)
    import_user_id = fields.Many2one('res.users', string='Importé par', readonly=True)

    active = fields.Boolean(default=True)

    @api.depends('ouvrage_ids', 'famille_ids')
    def _compute_counts(self):
        for rec in self:
            rec.ouvrage_count = len(rec.ouvrage_ids)
            rec.famille_count = len(rec.famille_ids)
            rec.modified_count = len(rec.ouvrage_ids.filtered(lambda o: o.is_modified))

    def action_view_ouvrages(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ouvrages - {self.name}',
            'res_model': 'qdv.ouvrage',
            'view_mode': 'list,form',
            'domain': [('base_id', '=', self.id)],
            'context': {'default_base_id': self.id},
        }

    def action_view_modified(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ouvrages modifiés - {self.name}',
            'res_model': 'qdv.ouvrage',
            'view_mode': 'list,form',
            'domain': [('base_id', '=', self.id), ('is_modified', '=', True)],
            'context': {'default_base_id': self.id},
        }

    def action_view_familles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Familles - {self.name}',
            'res_model': 'qdv.ouvrage.famille',
            'view_mode': 'list,form',
            'domain': [('base_id', '=', self.id)],
            'context': {'default_base_id': self.id},
        }

    def action_import_grp(self):
        """Ouvre le wizard d'import"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Importer base .grp',
            'res_model': 'qdv.import.grp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_base_id': self.id},
        }

    def action_export_json(self):
        """Ouvre le wizard d'export JSON"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Exporter vers QDV7',
            'res_model': 'qdv.export.grp.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_base_id': self.id},
        }

    def action_reset_modified(self):
        """Remet tous les ouvrages à l'état non modifié"""
        self.ensure_one()
        self.ouvrage_ids.write({'is_modified': False})
        self.state = 'imported'
        return True

    def _import_from_server_path(self, file_path):
        """Import direct depuis un chemin serveur (utilisé par CRON et découverte)"""
        self.ensure_one()
        if not os.path.exists(file_path):
            raise UserError(_('Fichier introuvable : %s') % file_path)

        # Mettre à jour le chemin
        self.file_path = file_path

        # Créer un faux wizard pour réutiliser la logique d'import
        wizard = self.env['qdv.import.grp.wizard'].new({
            'base_id': self.id,
            'import_mode': 'replace',
        })
        result = wizard._process_grp_file(file_path)
        _logger.info('Import depuis chemin serveur: %s → %d ouvrages', file_path, result['ouvrages_created'])
        return result
    def action_import_from_server(self):
        """Import direct depuis le chemin serveur configuré dans file_path"""
        self.ensure_one()
        if not self.file_path:
            raise UserError(_(
                'Aucun chemin de fichier configuré pour cette base.\n'
                'Renseignez le champ "Chemin du fichier .grp" ou utilisez\n'
                '"📥 Importer un fichier .grp" pour uploader le fichier.'
            ))

        fpath = os.path.normpath(self.file_path)
        if not os.path.exists(fpath):
            raise UserError(_(
                'Fichier introuvable :\n%s\n\n'
                'Vérifiez que :\n'
                '• Le chemin est correct\n'
                '• Google Drive est bien synchronisé\n'
                '• Le service Odoo a accès à ce chemin'
            ) % fpath)

        result = self._import_from_server_path(fpath)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Import réussi'),
                'message': _(
                    '%d ouvrages et %d familles importés depuis :\n%s'
                ) % (result['ouvrages_created'], result['familles'], fpath),
                'type': 'success',
                'sticky': True,
            }
        }
