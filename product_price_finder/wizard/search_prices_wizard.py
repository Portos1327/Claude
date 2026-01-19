# -*- coding: utf-8 -*-
"""
Search Prices Wizard
====================

Wizard SIMPLIFIÉ pour rechercher des fournisseurs.
Seulement 2 critères: Référence + Marque (pas de code fabricant)
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class SearchPricesWizard(models.TransientModel):
    """
    Wizard de recherche de fournisseurs SIMPLIFIÉ
    
    2 flux possibles:
    1. Depuis menu "Recherche de Prix" → créer un produit + rechercher
    2. Depuis onglet produit "Recherche de Fournisseurs" → rechercher pour produit existant
    """
    _name = 'search.prices.wizard'
    _description = 'Recherche de fournisseurs'

    # Mode: nouveau produit ou produit existant
    mode = fields.Selection([
        ('existing', 'Produit existant'),
        ('new', 'Nouveau produit'),
    ], string='Mode', default='existing', required=True)
    
    # Produit existant
    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Produit'
    )
    
    # Nouveau produit
    new_product_name = fields.Char(
        string='Nom du produit'
    )
    
    # CRITÈRES DE RECHERCHE SIMPLIFIÉS (seulement 2 champs)
    reference = fields.Char(
        string='Référence fabricant',
        required=True,
        help="Référence du produit chez le fabricant"
    )
    
    brand = fields.Char(
        string='Marque du fabricant',
        help="Nom de la marque (ex: Legrand, Schneider)"
    )
    
    # État
    state = fields.Selection([
        ('search', 'Recherche'),
        ('results', 'Résultats'),
        ('done', 'Terminé'),
    ], string='État', default='search')
    
    # Résultats
    result_ids = fields.One2many(
        comodel_name='search.prices.wizard.result',
        inverse_name='wizard_id',
        string='Résultats'
    )
    
    result_count = fields.Integer(
        string='Nombre de résultats',
        compute='_compute_result_count'
    )

    @api.depends('result_ids')
    def _compute_result_count(self):
        for wizard in self:
            wizard.result_count = len(wizard.result_ids)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Pré-remplit les critères depuis le produit"""
        if self.product_id:
            self.mode = 'existing'
            self.reference = self.product_id.manufacturer_ref or self.product_id.default_code or ''
            self.brand = self.product_id.manufacturer_brand or ''

    @api.onchange('mode')
    def _onchange_mode(self):
        """Réinitialise selon le mode"""
        if self.mode == 'new':
            self.product_id = False

    def action_search(self):
        """
        Recherche les fournisseurs dans toutes les sources actives.
        """
        self.ensure_one()
        
        if not self.reference:
            raise UserError(_("La référence fabricant est obligatoire."))
        
        # Supprimer les anciens résultats
        self.result_ids.unlink()
        
        # Auto-détecter et créer les sources si nécessaire
        PriceSource = self.env['price.source']
        sources = PriceSource.search([('active', '=', True)])
        
        if not sources:
            # Créer automatiquement les sources détectées
            PriceSource.auto_detect_and_create_sources()
            sources = PriceSource.search([('active', '=', True)])
        
        if not sources:
            raise UserError(_(
                "Aucune source de prix configurée.\n"
                "Allez dans Recherche Prix → Configuration → Sources pour en créer."
            ))
        
        # Rechercher dans toutes les sources
        results = PriceSource.search_all_sources(
            reference=self.reference,
            brand=self.brand
        )
        
        if not results:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aucun résultat'),
                    'message': _("Aucun fournisseur trouvé pour '%s'") % self.reference,
                    'type': 'warning',
                    'sticky': False,
                    'next': {
                        'type': 'ir.actions.act_window',
                        'res_model': 'search.prices.wizard',
                        'res_id': self.id,
                        'view_mode': 'form',
                        'target': 'new',
                    }
                }
            }
        
        # Créer les lignes de résultat
        for idx, result in enumerate(results):
            self.env['search.prices.wizard.result'].create({
                'wizard_id': self.id,
                'sequence': idx + 1,
                'selected': True,
                'source_id': result.get('source_id'),
                'source_name': result.get('source_name'),
                'partner_id': result.get('partner_id'),
                'partner_name': result.get('partner_name'),
                'article_model': result.get('model_name'),
                'article_id': result.get('article_id'),
                'reference': result.get('reference'),
                'designation': result.get('designation'),
                'brand': result.get('brand'),
                'price': result.get('price', 0.0),
                'price_base': result.get('price_base', 0.0),
                'discount': result.get('discount', 0.0),
                'unit': result.get('unit'),
                'already_linked': bool(result.get('linked_product_id')),
            })
        
        self.state = 'results'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'search.prices.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_apply_selection(self):
        """
        Applique la sélection:
        1. Crée le produit si mode 'new'
        2. Met à jour les champs manufacturer_ref/brand du produit
        3. Crée les correspondances (price.match)
        4. Ajoute les fournisseurs sélectionnés à l'onglet Achats
        """
        self.ensure_one()
        
        selected_results = self.result_ids.filtered('selected')
        if not selected_results:
            raise UserError(_("Sélectionnez au moins un fournisseur."))
        
        # 1. Créer le produit si nécessaire
        if self.mode == 'new':
            if not self.new_product_name:
                # Utiliser la désignation du premier résultat
                self.new_product_name = selected_results[0].designation or self.reference
            
            product = self.env['product.product'].create({
                'name': self.new_product_name,
                'manufacturer_ref': self.reference,
                'manufacturer_brand': self.brand,
                'type': 'consu',
            })
            self.product_id = product
        else:
            if not self.product_id:
                raise UserError(_("Veuillez sélectionner un produit."))
            
            # Mettre à jour les champs du produit
            self.product_id.write({
                'manufacturer_ref': self.reference,
                'manufacturer_brand': self.brand,
            })
        
        # 2. Créer les correspondances et ajouter aux Achats
        PriceMatch = self.env['price.match']
        suppliers_added = 0
        
        for result in selected_results:
            try:
                # Créer la correspondance
                match = PriceMatch.create({
                    'product_id': self.product_id.id,
                    'source_id': result.source_id.id,
                    'article_model': result.article_model,
                    'article_id': result.article_id,
                    'reference': result.reference,
                    'designation': result.designation,
                    'brand': result.brand,
                    'price': result.price,
                    'price_base': result.price_base,
                    'discount': result.discount,
                    'unit': result.unit,
                    'partner_id': result.partner_id.id if result.partner_id else False,
                    'state': 'selected',
                })
                
                # Appliquer à l'onglet Achats
                match.action_apply_to_purchases()
                suppliers_added += 1
                
            except Exception as e:
                _logger.warning(f"Erreur ajout fournisseur {result.source_name}: {e}")
        
        self.state = 'done'
        
        # Message de confirmation
        message = _("%d fournisseur(s) ajouté(s) à l'onglet Achats du produit '%s'.") % (
            suppliers_added, self.product_id.name
        )
        
        if self.mode == 'new':
            message = _("Produit '%s' créé.\n%s") % (self.product_id.name, message)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fournisseurs ajoutés'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window',
                    'res_model': 'product.product',
                    'res_id': self.product_id.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
            }
        }

    def action_select_all(self):
        """Sélectionne tous les résultats"""
        self.result_ids.write({'selected': True})
        return self._return_wizard()

    def action_select_none(self):
        """Désélectionne tous les résultats"""
        self.result_ids.write({'selected': False})
        return self._return_wizard()

    def action_select_best_price(self):
        """Sélectionne uniquement le meilleur prix"""
        self.result_ids.write({'selected': False})
        best = self.result_ids.filtered(lambda r: r.price > 0).sorted('price')[:1]
        if best:
            best.selected = True
        return self._return_wizard()

    def _return_wizard(self):
        """Retourne l'action pour rester sur le wizard"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'search.prices.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class SearchPricesWizardResult(models.TransientModel):
    """
    Ligne de résultat du wizard de recherche
    """
    _name = 'search.prices.wizard.result'
    _description = 'Résultat de recherche'
    _order = 'sequence, price'

    wizard_id = fields.Many2one(
        comodel_name='search.prices.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    
    sequence = fields.Integer(default=10)
    selected = fields.Boolean(string='✓', default=True)
    
    # Source
    source_id = fields.Many2one('price.source', string='Source')
    source_name = fields.Char(string='Module')
    
    # Fournisseur
    partner_id = fields.Many2one('res.partner', string='Fournisseur')
    partner_name = fields.Char(string='Nom fournisseur')
    
    # Article
    article_model = fields.Char(string='Modèle')
    article_id = fields.Integer(string='ID')
    
    # Données
    reference = fields.Char(string='Référence')
    designation = fields.Char(string='Désignation')
    brand = fields.Char(string='Marque')
    
    price = fields.Float(string='Prix net', digits='Product Price')
    price_base = fields.Float(string='Prix base', digits='Product Price')
    discount = fields.Float(string='Remise %')
    unit = fields.Char(string='Unité')
    
    already_linked = fields.Boolean(string='Déjà lié')

    def action_view_article(self):
        """Ouvre l'article source"""
        self.ensure_one()
        if self.article_model not in self.env:
            raise UserError(_("Module non installé."))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.article_model,
            'res_id': self.article_id,
            'view_mode': 'form',
            'target': 'new',
        }
