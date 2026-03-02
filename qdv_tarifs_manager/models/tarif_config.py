# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Configuration globale
Gère le chemin vers le dossier des bases QDV et les fichiers associés
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os

_logger = logging.getLogger(__name__)

DEFAULT_TARIFS_FOLDER = r"C:\Users\dimitri\Mon Drive\Base QDV\Tarifs ID V2"


class QdvTarifConfig(models.Model):
    _name = 'qdv.tarif.config'
    _description = 'Configuration QDV Tarifs Manager'
    _rec_name = 'tarifs_folder'

    # =========================================================================
    # CHEMINS
    # =========================================================================
    tarifs_folder = fields.Char(
        string='Dossier Tarifs ID V2',
        default=DEFAULT_TARIFS_FOLDER,
        required=True,
        help='Chemin vers le dossier contenant les bases .qdb des tarifs fournisseurs QDV'
    )
    rebates_file = fields.Char(
        string='Fichier Rebates',
        compute='_compute_file_paths',
        help='Chemin vers Rebates.qdbr (base SQLite des remises)'
    )
    browser_local_file = fields.Char(
        string='BrowserFromLocal',
        compute='_compute_file_paths',
        help='Fichier BrowserFromLocal.txt (liste bases locales avec métadonnées)'
    )
    browser_web_file = fields.Char(
        string='BrowserFromWeb',
        compute='_compute_file_paths',
        help='Fichier BrowserFromWeb.txt (liste bases web avec métadonnées)'
    )

    # =========================================================================
    # STATUT DES FICHIERS
    # =========================================================================
    rebates_ok = fields.Boolean(string='Rebates.qdbr présent', compute='_compute_file_status')
    browser_local_ok = fields.Boolean(string='BrowserFromLocal.txt présent', compute='_compute_file_status')
    browser_web_ok = fields.Boolean(string='BrowserFromWeb.txt présent', compute='_compute_file_status')
    folder_ok = fields.Boolean(string='Dossier accessible', compute='_compute_file_status')

    # =========================================================================
    # COMPTEURS
    # =========================================================================
    base_count = fields.Integer(
        string='Bases découvertes',
        compute='_compute_base_count'
    )
    article_count = fields.Integer(
        string='Articles importés',
        compute='_compute_article_count'
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('tarifs_folder')
    def _compute_file_paths(self):
        for rec in self:
            folder = rec.tarifs_folder or ''
            rec.rebates_file = os.path.join(folder, 'Rebates.qdbr') if folder else ''
            rec.browser_local_file = os.path.join(folder, 'BrowserFromLocal.txt') if folder else ''
            rec.browser_web_file = os.path.join(folder, 'BrowserFromWeb.txt') if folder else ''

    @api.depends('tarifs_folder')
    def _compute_file_status(self):
        for rec in self:
            folder = rec.tarifs_folder or ''
            rec.folder_ok = bool(folder and os.path.isdir(folder))
            rec.rebates_ok = bool(folder and os.path.isfile(os.path.join(folder, 'Rebates.qdbr')))
            rec.browser_local_ok = bool(folder and os.path.isfile(os.path.join(folder, 'BrowserFromLocal.txt')))
            rec.browser_web_ok = bool(folder and os.path.isfile(os.path.join(folder, 'BrowserFromWeb.txt')))

    def _compute_base_count(self):
        for rec in self:
            rec.base_count = self.env['qdv.tarif.base'].search_count([])

    def _compute_article_count(self):
        for rec in self:
            rec.article_count = self.env['qdv.tarif.article'].search_count([])

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_discover_bases(self):
        """Lance la découverte des bases .qdb dans le dossier configuré"""
        self.ensure_one()
        if not self.folder_ok:
            raise UserError(_("Le dossier '%s' n'est pas accessible.\nVérifiez le chemin configuré.") % self.tarifs_folder)

        return {
            'type': 'ir.actions.act_window',
            'name': _('Découverte des bases QDV'),
            'res_model': 'qdv.tarif.discover.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_config_id': self.id},
        }

    def action_view_bases(self):
        """Ouvre la liste des bases découvertes"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bases Tarifs QDV'),
            'res_model': 'qdv.tarif.base',
            'view_mode': 'list,form',
        }

    def action_view_articles(self):
        """Ouvre la liste des articles importés"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articles QDV importés'),
            'res_model': 'qdv.tarif.article',
            'view_mode': 'list,form',
        }

    def action_run_cron_now(self):
        """Lance immédiatement la vérification CRON (identique au passage automatique)"""
        self.ensure_one()
        self.env['qdv.tarif.cron.mixin'].run_daily_check()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Journal synchronisation'),
            'res_model': 'qdv.tarif.sync.log',
            'view_mode': 'list,form',
        }

    @api.model
    def get_config(self):
        """Retourne ou crée la configuration unique"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({'tarifs_folder': DEFAULT_TARIFS_FOLDER})
        return config
