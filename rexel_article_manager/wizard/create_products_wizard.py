# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CreateProductsWizard(models.TransientModel):
    _name = 'create.products.wizard'
    _description = 'Assistant de création de produits Odoo'

    article_ids = fields.Many2many('rexel.article', string='Articles')
    
    mode = fields.Selection([
        ('create', 'Créer les produits manquants'),
        ('update', 'Mettre à jour les produits existants'),
        ('both', 'Créer et mettre à jour'),
    ], string='Mode', default='create', required=True)
    
    filter_by_family = fields.Boolean(string='Filtrer par famille', default=False)
    family_filter = fields.Char(string='Famille')
    
    # Statistiques
    total_articles = fields.Integer(string='Total articles', readonly=True)
    articles_with_product = fields.Integer(string='Articles avec produit', readonly=True)
    articles_without_product = fields.Integer(string='Articles sans produit', readonly=True)
    
    # Résultats
    products_created = fields.Integer(string='Produits créés', readonly=True)
    products_updated = fields.Integer(string='Produits mis à jour', readonly=True)
    errors = fields.Integer(string='Erreurs', readonly=True)
    log_message = fields.Text(string='Log', readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Récupère les articles sélectionnés"""
        res = super().default_get(fields_list)
        
        if self.env.context.get('active_ids'):
            article_ids = self.env.context.get('active_ids')
            res['article_ids'] = [(6, 0, article_ids)]
            
            articles = self.env['rexel.article'].browse(article_ids)
            res['total_articles'] = len(articles)
            res['articles_with_product'] = len(articles.filtered('product_id'))
            res['articles_without_product'] = len(articles.filtered(lambda a: not a.product_id))
        
        return res

    def action_create_products(self):
        """Lance la création/mise à jour des produits"""
        self.ensure_one()
        
        articles = self.article_ids
        
        # Filtrer par famille si demandé
        if self.filter_by_family and self.family_filter:
            articles = articles.filtered(lambda a: a.famille_libelle and self.family_filter.upper() in a.famille_libelle.upper())
        
        if not articles:
            raise UserError(_('Aucun article à traiter.'))
        
        created = 0
        updated = 0
        errors = 0
        log_lines = []
        
        for article in articles:
            try:
                if not article.product_id:
                    # Créer le produit
                    if self.mode in ['create', 'both']:
                        product_vals = article._prepare_product_values()
                        product = self.env['product.product'].create(product_vals)
                        article.write({'product_id': product.id})
                        created += 1
                        log_lines.append(f"✓ Créé: {article.reference_fabricant} → {product.default_code}")
                else:
                    # Mettre à jour le produit
                    if self.mode in ['update', 'both']:
                        product_vals = article._prepare_product_values()
                        article.product_id.write(product_vals)
                        updated += 1
                        log_lines.append(f"↻ MAJ: {article.reference_fabricant}")
                
            except Exception as e:
                errors += 1
                log_lines.append(f"✗ Erreur {article.reference_fabricant}: {str(e)}")
                _logger.error(f"Erreur création produit pour {article.reference_fabricant}: {str(e)}")
        
        # Mettre à jour les résultats
        self.write({
            'products_created': created,
            'products_updated': updated,
            'errors': errors,
            'log_message': '\n'.join(log_lines[:100]),  # Limiter à 100 lignes
        })
        
        message = f"""
        ✓ {created} produits créés
        ↻ {updated} produits mis à jour
        ✗ {errors} erreurs
        """
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Création des produits terminée'),
                'message': _(message),
                'type': 'success' if errors == 0 else 'warning',
                'sticky': True,
            }
        }
