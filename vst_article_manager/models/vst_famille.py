# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class VstFamille(models.Model):
    _name = 'vst.famille'
    _description = 'Famille VST'
    _parent_name = 'parent_id'
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Nom', required=True, index=True)
    code = fields.Char(string='Code', index=True)
    complete_name = fields.Char(
        string='Nom complet',
        compute='_compute_complete_name',
        store=True,
        recursive=True
    )
    
    # Hiérarchie
    parent_id = fields.Many2one(
        'vst.famille',
        string='Famille parente',
        index=True,
        ondelete='cascade'
    )
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'vst.famille',
        'parent_id',
        string='Sous-familles'
    )
    
    # Type de niveau
    level = fields.Selection([
        ('activite', 'Activité'),
        ('marque', 'Marque'),
        ('famille', 'Famille'),
        ('sous_famille', 'Sous-Famille'),
        ('sous_sous_famille', 'Sous-Sous-Famille'),
    ], string='Niveau', default='famille')
    
    # Compteur d'articles
    article_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_article_count',
        store=False
    )
    
    # Articles liés
    article_ids = fields.One2many(
        'vst.article',
        'famille_id',
        string='Articles'
    )
    
    # Couleur pour la vue kanban
    color = fields.Integer(string='Couleur')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for famille in self:
            if famille.parent_id:
                famille.complete_name = f"{famille.parent_id.complete_name} / {famille.name}"
            else:
                famille.complete_name = famille.name

    def _compute_article_count(self):
        for famille in self:
            all_famille_ids = self.search([('id', 'child_of', famille.id)]).ids
            famille.article_count = self.env['vst.article'].search_count([
                ('famille_id', 'in', all_famille_ids)
            ])

    @api.model
    def get_or_create(self, code, name, parent_id=None, level='famille'):
        """Récupère ou crée une famille par son code"""
        if not code:
            return False
        
        famille = self.search([('code', '=', code)], limit=1)
        if not famille:
            famille = self.create({
                'code': code,
                'name': name or code,
                'parent_id': parent_id,
                'level': level,
            })
        elif name and famille.name != name:
            famille.write({'name': name})
        
        return famille.id

    @api.model
    def parse_famille_code(self, famille_code, nouvelle_famille_code=None, 
                           libelle_activite=None, libelle_marque=None,
                           libelle_famille=None, libelle_sous_famille=None):
        """
        Parse le code famille VST et crée la hiérarchie
        """
        if not famille_code and not nouvelle_famille_code:
            return False
        
        code_to_parse = nouvelle_famille_code or famille_code
        parts = code_to_parse.split('.') if code_to_parse else []
        
        if not parts:
            return False
        
        parent_id = None
        famille_id = None
        
        levels_info = [
            ('activite', libelle_activite),
            ('marque', libelle_marque) if nouvelle_famille_code else ('famille', libelle_famille),
            ('famille', libelle_famille) if nouvelle_famille_code else ('sous_famille', libelle_sous_famille),
            ('sous_famille', libelle_sous_famille) if nouvelle_famille_code else ('sous_sous_famille', None),
        ]
        
        cumul_code = ''
        for i, part in enumerate(parts):
            if not part:
                continue
            
            cumul_code = f"{cumul_code}.{part}" if cumul_code else part
            
            level = levels_info[i][0] if i < len(levels_info) else 'sous_sous_famille'
            libelle = levels_info[i][1] if i < len(levels_info) else None
            
            famille_id = self.get_or_create(
                code=cumul_code,
                name=libelle or part,
                parent_id=parent_id,
                level=level
            )
            parent_id = famille_id
        
        return famille_id

    def action_view_articles(self):
        """Action pour voir les articles de la famille"""
        self.ensure_one()
        all_famille_ids = self.search([('id', 'child_of', self.id)]).ids
        return {
            'name': _('Articles - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'vst.article',
            'view_mode': 'list,form',
            'domain': [('famille_id', 'in', all_famille_ids)],
            'context': {'default_famille_id': self.id},
        }

    def action_rebuild_hierarchy(self):
        """Reconstruit la hiérarchie des familles"""
        articles = self.env['vst.article'].search([])
        count = 0
        
        for article in articles:
            if article.famille_code or article.nouvelle_famille_code:
                famille_id = self.parse_famille_code(
                    famille_code=article.famille_code,
                    nouvelle_famille_code=article.nouvelle_famille_code,
                    libelle_activite=article.libelle_activite,
                    libelle_marque=article.libelle_marque,
                    libelle_famille=article.libelle_famille,
                    libelle_sous_famille=article.libelle_sous_famille,
                )
                if famille_id and article.famille_id.id != famille_id:
                    article.write({'famille_id': famille_id})
                    count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Hiérarchie reconstruite'),
                'message': _('%d articles mis à jour.') % count,
                'type': 'success',
                'sticky': False,
            }
        }
