# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class QdvOuvrageFamille(models.Model):
    """Famille d'ouvrage QDV7 - correspond à TreeTable dans le .grp"""
    _name = 'qdv.ouvrage.famille'
    _description = 'Famille d\'ouvrage QDV7'
    _order = 'code'
    _rec_name = 'display_name_full'

    base_id = fields.Many2one(
        'qdv.ouvrage.base',
        string='Base d\'ouvrage',
        required=True,
        ondelete='cascade'
    )
    qdv_row_id = fields.Integer(
        string='ID QDV (RowID)',
        help='RowID d\'origine dans la table TreeTable du fichier .grp'
    )
    code = fields.Char(
        string='Code famille',
        required=True,
        help='Ex: A, Aa, Ab, Ab1, Ab11...'
    )
    name = fields.Char(
        string='Libellé',
        required=True
    )
    level = fields.Integer(
        string='Niveau',
        compute='_compute_level',
        store=True,
        help='Profondeur dans l\'arborescence (basée sur la longueur du code)'
    )
    parent_code = fields.Char(
        string='Code parent',
        compute='_compute_parent_code',
        store=True
    )
    parent_id = fields.Many2one(
        'qdv.ouvrage.famille',
        string='Famille parente',
        compute='_compute_parent_id',
        store=True
    )
    child_ids = fields.One2many(
        'qdv.ouvrage.famille',
        'parent_id',
        string='Sous-familles'
    )
    ouvrage_ids = fields.One2many(
        'qdv.ouvrage',
        'famille_id',
        string='Ouvrages'
    )
    ouvrage_count = fields.Integer(
        string='Nb ouvrages',
        compute='_compute_ouvrage_count'
    )
    display_name_full = fields.Char(
        string='Famille',
        compute='_compute_display_name_full',
        store=True
    )

    @api.depends('code')
    def _compute_level(self):
        for rec in self:
            rec.level = len(rec.code) if rec.code else 0

    @api.depends('code')
    def _compute_parent_code(self):
        for rec in self:
            if rec.code and len(rec.code) > 1:
                # Trouver le code parent en retirant le dernier segment
                # Ex: Ab11 -> Ab1 -> Ab -> A
                # La logique QDV est : code parent = trouver la famille dont
                # le code est le préfixe le plus long
                rec.parent_code = rec.code[:-1]
            else:
                rec.parent_code = False

    @api.depends('code', 'base_id', 'parent_code')
    def _compute_parent_id(self):
        for rec in self:
            if rec.parent_code and rec.base_id:
                parent = self.search([
                    ('base_id', '=', rec.base_id.id),
                    ('code', '=', rec.parent_code)
                ], limit=1)
                rec.parent_id = parent or False
            else:
                rec.parent_id = False

    @api.depends('code', 'name')
    def _compute_display_name_full(self):
        for rec in self:
            rec.display_name_full = f'[{rec.code}] {rec.name}' if rec.code else rec.name

    def _compute_ouvrage_count(self):
        for rec in self:
            rec.ouvrage_count = len(rec.ouvrage_ids)

    _sql_constraints = [
        ('unique_code_base', 'UNIQUE(base_id, code)',
         'Le code de famille doit être unique par base d\'ouvrage.'),
    ]
