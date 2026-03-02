# -*- coding: utf-8 -*-
"""
Filtre de familles/sous-familles/fonctions avec arborescence
"""
from odoo import models, fields, api


class QdvFamilyFilter(models.Model):
    """Filtre de familles avec arborescence et codes composés"""
    _name = 'qdv.family.filter'
    _description = 'Filtre famille QDV'
    _order = 'family_name, subfamily_name, function_name'

    supplier_id = fields.Many2one('qdv.supplier', required=True, ondelete='cascade')
    
    # Niveaux de famille (3 niveaux possibles)
    family_name = fields.Char(string='Famille', index=True)
    subfamily_name = fields.Char(string='Sous-famille', index=True)
    function_name = fields.Char(string='Fonction', index=True,
        help='Sous-sous-famille (3ème niveau)')
    
    # Codes sources (pour Rexel par exemple)
    family_code = fields.Char(string='Code famille source')
    subfamily_code = fields.Char(string='Code sous-famille source')
    function_code = fields.Char(string='Code fonction source')
    
    # Code composé calculé
    full_code = fields.Char(string='Code complet', compute='_compute_full_code', store=True,
        help='Code composé: famille + sous-famille + fonction')
    
    # Sélection pour la sync
    selected = fields.Boolean(string='Sync', default=True, 
        help='Cocher pour synchroniser cette famille')
    
    # Code famille QDV correspondant
    qdv_family_code = fields.Char(string='Code QDV',
        help='Code famille QDV à utiliser (ex: Ga, H, 84Dg)')
    
    # MaterialKindID pour les nouveaux articles
    material_kind_id = fields.Char(string='MaterialKindID',
        help='ID Type matériel QDV (ex: CFO0401 pour câbles)')
    
    # Niveau dans l'arborescence
    level = fields.Integer(string='Niveau', compute='_compute_level', store=True)
    
    # Stats
    article_count = fields.Integer(string='Articles', readonly=True)
    
    # Affichage
    display_name = fields.Char(compute='_compute_display_name', store=True)

    @api.depends('family_code', 'subfamily_code', 'function_code')
    def _compute_full_code(self):
        for r in self:
            parts = []
            if r.family_code:
                parts.append(r.family_code)
            if r.subfamily_code:
                parts.append(r.subfamily_code)
            if r.function_code:
                parts.append(r.function_code)
            r.full_code = ''.join(parts) if parts else ''

    @api.depends('family_name', 'subfamily_name', 'function_name')
    def _compute_level(self):
        for r in self:
            if r.function_name:
                r.level = 3
            elif r.subfamily_name:
                r.level = 2
            elif r.family_name:
                r.level = 1
            else:
                r.level = 0

    @api.depends('family_name', 'subfamily_name', 'function_name', 'level')
    def _compute_display_name(self):
        for r in self:
            parts = []
            indent = ''
            if r.level == 2:
                indent = '  └─ '
            elif r.level == 3:
                indent = '    └─ '
            
            if r.function_name:
                parts.append(indent + r.function_name)
            elif r.subfamily_name:
                parts.append(indent + r.subfamily_name)
            elif r.family_name:
                parts.append(r.family_name)
            
            r.display_name = ''.join(parts) if parts else 'Sans famille'
