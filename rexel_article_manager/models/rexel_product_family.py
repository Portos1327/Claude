# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class RexelProductFamily(models.Model):
    _name = 'rexel.product.family'
    _description = 'Famille de produits Rexel'
    _order = 'sequence, name'
    _parent_store = True
    _parent_name = "parent_id"

    name = fields.Char(string='Nom', required=True, index=True)
    code = fields.Char(string='Code', index=True, help='Code de la famille/sous-famille/fonction')
    parent_id = fields.Many2one('rexel.product.family', string='Parent', ondelete='cascade', index=True)
    parent_path = fields.Char(index=True)  # Supprimé uniq=True (invalide)
    child_ids = fields.One2many('rexel.product.family', 'parent_id', string='Enfants')
    
    level = fields.Selection([
        ('famille', 'Famille'),
        ('sous_famille', 'Sous-famille'),
        ('fonction', 'Fonction'),
        ('lidic', 'Lidic'),
        ('gamme', 'Gamme de vente'),
    ], string='Niveau', default='famille', index=True)
    
    sequence = fields.Integer(string='Séquence', default=10)
    
    article_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_article_count',
        store=False
    )
    
    article_ids = fields.One2many('rexel.article', 'family_node_id', string='Articles')
    
    active = fields.Boolean(string='Actif', default=True)
    
    @api.depends('article_ids', 'child_ids')
    def _compute_article_count(self):
        """Compte le nombre d'articles dans cette famille et ses enfants"""
        for record in self:
            # Articles directs
            count = len(record.article_ids)
            
            # Articles des enfants
            for child in record.child_ids:
                count += child.article_count
            
            record.article_count = count

    @api.depends('name', 'article_count')
    def _compute_display_name(self):
        """Affichage avec le nombre d'articles (remplace name_get dépréciée)"""
        for record in self:
            if record.article_count > 0:
                record.display_name = f"{record.name} ({record.article_count})"
            else:
                record.display_name = record.name

    def action_view_articles(self):
        """Ouvre la vue des articles de cette famille"""
        self.ensure_one()
        
        # Récupérer tous les articles
        article_ids = self._get_all_article_ids()
        
        return {
            'name': f'Articles - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'rexel.article',
            'view_mode': 'list,form',
            'domain': [('id', 'in', article_ids)],
        }

    def _get_all_article_ids(self):
        """Récupère tous les articles de cette famille (récursif)"""
        article_ids = self.article_ids.ids
        for child in self.child_ids:
            article_ids.extend(child._get_all_article_ids())
        return article_ids

    @api.model
    def rebuild_hierarchy_from_articles(self):
        """Reconstruit la hiérarchie depuis les articles"""
        _logger.info("Reconstruction de la hiérarchie...")
        
        self.search([]).unlink()
        
        articles = self.env['rexel.article'].search([])
        family_map = {}
        
        for article in articles:
            # Créer la hiérarchie avec les nouveaux noms de champs
            famille = article.famille_libelle or 'Sans famille'
            sous_famille = article.sous_famille_libelle or 'Sans sous-famille'
            fonction = article.fonction_libelle or 'Sans fonction'
            lidic = article.fabricant_libelle or 'Sans fabricant'
            gamme = 'Articles'  # Pas de gamme dans le nouveau modèle
            
            # Construire les clés uniques
            key_f = famille
            key_sf = f"{famille}|{sous_famille}"
            key_fn = f"{key_sf}|{fonction}"
            key_ld = f"{key_fn}|{lidic}"
            key_gm = f"{key_ld}|{gamme}"
            
            # Créer les nœuds si nécessaire
            if key_f not in family_map:
                family_map[key_f] = self.create({'name': famille, 'level': 'famille', 'sequence': 10})
            
            if key_sf not in family_map:
                family_map[key_sf] = self.create({
                    'name': sous_famille,
                    'level': 'sous_famille',
                    'parent_id': family_map[key_f].id,
                    'sequence': 20
                })
            
            if key_fn not in family_map:
                family_map[key_fn] = self.create({
                    'name': fonction,
                    'level': 'fonction',
                    'parent_id': family_map[key_sf].id,
                    'sequence': 30
                })
            
            if key_ld not in family_map:
                family_map[key_ld] = self.create({
                    'name': lidic,
                    'level': 'lidic',
                    'parent_id': family_map[key_fn].id,
                    'sequence': 40
                })
            
            if key_gm not in family_map:
                family_map[key_gm] = self.create({
                    'name': gamme,
                    'level': 'gamme',
                    'parent_id': family_map[key_ld].id,
                    'sequence': 50
                })
            
            # Lier l'article
            article.write({'family_node_id': family_map[key_gm].id})
        
        _logger.info(f"Hiérarchie reconstruite: {len(family_map)} nœuds")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Succès',
                'message': 'Hiérarchie reconstruite !',
                'type': 'success',
            }
        }
