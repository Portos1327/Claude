# -*- coding: utf-8 -*-
"""
Gestion des familles QDV - Structure hiérarchique
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class QdvFamily(models.Model):
    """Famille d'articles QDV (structure hiérarchique)"""
    _name = 'qdv.family'
    _description = 'Famille QDV'
    _order = 'supplier_id, code'
    _parent_name = 'parent_id'
    _parent_store = True

    supplier_id = fields.Many2one('qdv.supplier', string='Fournisseur', required=True, ondelete='cascade')
    
    code = fields.Char(string='Code', required=True, help='Code famille QDV (ex: A, Aa, 48, 48Aa)')
    name = fields.Char(string='Description', required=True)
    
    # Hiérarchie
    parent_id = fields.Many2one('qdv.family', string='Famille parente', ondelete='cascade', 
        domain="[('supplier_id', '=', supplier_id)]")
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many('qdv.family', 'parent_id', string='Sous-familles')
    
    # Niveau calculé
    level = fields.Integer(string='Niveau', compute='_compute_level', store=True)
    
    # Mapping Odoo - liste de valeurs séparées par virgule
    odoo_families = fields.Text(string='Familles Odoo', 
        help='Valeurs Odoo séparées par des virgules (ex: U1000R2V, R2V, U-1000 R2V)')
    
    # Affichage
    display_name = fields.Char(compute='_compute_display_name', store=True)
    full_path = fields.Char(string='Chemin complet', compute='_compute_full_path', store=True, recursive=True)
    
    _sql_constraints = [
        ('code_supplier_unique', 'UNIQUE(code, supplier_id)', 'Le code famille doit être unique par fournisseur!')
    ]

    @api.depends('parent_id')
    def _compute_level(self):
        for rec in self:
            level = 0
            parent = rec.parent_id
            while parent:
                level = level + 1
                parent = parent.parent_id
            rec.level = level

    @api.depends('name', 'code', 'level')
    def _compute_display_name(self):
        for rec in self:
            indent = "  " * rec.level
            rec.display_name = "%s%s [%s]" % (indent, rec.name or '', rec.code or '')

    @api.depends('name', 'parent_id', 'parent_id.full_path')
    def _compute_full_path(self):
        for rec in self:
            if rec.parent_id:
                rec.full_path = (rec.parent_id.full_path or '') + ' > ' + (rec.name or '')
            else:
                rec.full_path = rec.name or ''

    @api.onchange('code', 'supplier_id')
    def _onchange_code(self):
        """Détecte automatiquement le parent basé sur le code"""
        if self.code and self.supplier_id:
            code = self.code
            if len(code) > 1:
                for i in range(len(code) - 1, 0, -1):
                    parent_code = code[:i]
                    parent = self.env['qdv.family'].search([
                        ('code', '=', parent_code),
                        ('supplier_id', '=', self.supplier_id.id)
                    ], limit=1)
                    if parent:
                        self.parent_id = parent
                        break

    def get_odoo_values_list(self):
        """Retourne la liste des valeurs Odoo mappées"""
        if not self.odoo_families:
            return []
        return [v.strip() for v in self.odoo_families.split(',') if v.strip()]
