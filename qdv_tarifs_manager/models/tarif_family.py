# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Familles arborescentes QDV
Importées depuis TreeTable dans les bases .qdb
Format QDV: FamilyValue="449_4_46_461_4610" → hiérarchie par séparateur '_'
"""
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)


class QdvTarifFamily(models.Model):
    _name = 'qdv.tarif.family'
    _description = 'Famille article QDV'
    _order = 'base_id, family_code'

    base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Base Fabricant',
        required=True,
        ondelete='cascade',
        index=True
    )
    manufacturer_code = fields.Char(
        related='base_id.manufacturer_code',
        store=True, index=True, string='Code Fab.'
    )

    # =========================================================================
    # CODE ET LIBELLÉ (depuis TreeTable)
    # =========================================================================
    family_code = fields.Char(
        string='Code famille',
        required=True,
        index=True,
        help='Valeur FamilyValue depuis TreeTable (ex: 449_4_46_461)'
    )
    family_label = fields.Char(
        string='Libellé',
        help='Texte FamilyText depuis TreeTable (ex: Câblage cuivre Cat6)'
    )

    # =========================================================================
    # HIÉRARCHIE CALCULÉE
    # =========================================================================
    depth = fields.Integer(
        string='Niveau',
        compute='_compute_hierarchy',
        store=True,
        help='0 = racine (fabricant), 1 = famille, 2 = sous-famille, etc.'
    )
    parent_code = fields.Char(
        string='Code parent',
        compute='_compute_hierarchy',
        store=True,
        index=True
    )
    parent_id = fields.Many2one(
        'qdv.tarif.family',
        string='Famille parente',
        compute='_compute_parent_id',
        store=True
    )
    # Libellés des niveaux 0→4 (aplatis pour filtres et affichage)
    level0_label = fields.Char(string='Niveau 0 (Fabricant)', compute='_compute_level_labels', store=True, recursive=True)
    level1_label = fields.Char(string='Niveau 1 (Famille)', compute='_compute_level_labels', store=True, recursive=True)
    level2_label = fields.Char(string='Niveau 2 (Sous-famille)', compute='_compute_level_labels', store=True, recursive=True)
    level3_label = fields.Char(string='Niveau 3', compute='_compute_level_labels', store=True, recursive=True)
    level4_label = fields.Char(string='Niveau 4', compute='_compute_level_labels', store=True, recursive=True)
    breadcrumb = fields.Char(
        string='Arborescence',
        compute='_compute_level_labels',
        store=True,
        recursive=True,
        help='Ex: ACOME / Systèmes / Câblage cuivre / Cat6'
    )

    # Articles liés
    article_count = fields.Integer(
        string='Articles',
        compute='_compute_article_count'
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('family_code')
    def _compute_hierarchy(self):
        for rec in self:
            code = rec.family_code or ''
            parts = [p for p in code.split('_') if p]
            rec.depth = max(0, len(parts) - 1)
            if len(parts) > 1:
                rec.parent_code = '_'.join(parts[:-1]) + '_'
            elif len(parts) == 1:
                rec.parent_code = False
            else:
                rec.parent_code = False

    @api.depends('parent_code', 'base_id')
    def _compute_parent_id(self):
        for rec in self:
            if rec.parent_code and rec.base_id:
                parent = self.env['qdv.tarif.family'].search([
                    ('base_id', '=', rec.base_id.id),
                    ('family_code', '=', rec.parent_code),
                ], limit=1)
                rec.parent_id = parent
            else:
                rec.parent_id = False

    @api.depends('family_code', 'family_label', 'parent_id',
                 'parent_id.level0_label', 'parent_id.level1_label',
                 'parent_id.level2_label', 'parent_id.level3_label')
    def _compute_level_labels(self):
        for rec in self:
            depth = rec.depth
            label = rec.family_label or rec.family_code or ''

            # Récupérer la chaîne complète en remontant les parents
            labels = []
            current = rec
            visited = set()
            while current and current.id not in visited:
                visited.add(current.id)
                lbl = current.family_label or current.family_code or ''
                labels.insert(0, lbl)
                current = current.parent_id

            # Assigner les niveaux
            rec.level0_label = labels[0] if len(labels) > 0 else ''
            rec.level1_label = labels[1] if len(labels) > 1 else ''
            rec.level2_label = labels[2] if len(labels) > 2 else ''
            rec.level3_label = labels[3] if len(labels) > 3 else ''
            rec.level4_label = labels[4] if len(labels) > 4 else ''
            rec.breadcrumb = ' / '.join(l for l in labels if l)

    def _compute_article_count(self):
        for rec in self:
            rec.article_count = self.env['qdv.tarif.article'].search_count([
                ('base_id', '=', rec.base_id.id),
                ('family_code', '=', rec.family_code),
            ])

    _sql_constraints = [
        ('unique_family_per_base', 'UNIQUE(base_id, family_code)',
         'Le code famille doit être unique par base fabricant.'),
    ]

    def action_view_articles(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articles - %s') % (self.family_label or self.family_code),
            'res_model': 'qdv.tarif.article',
            'view_mode': 'list,form',
            'domain': [('base_id', '=', self.base_id.id), ('family_code', '=', self.family_code)],
        }
