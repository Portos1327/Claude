# -*- coding: utf-8 -*-
"""
Product Product Extension
=========================

Extension du modèle product.product pour:
- Ajouter un onglet "Recherche de Fournisseurs" SIMPLIFIÉ
- Recherche par Référence + Marque uniquement (pas de code fabricant)
- Association automatique avec l'onglet Achats
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ProductProduct(models.Model):
    """
    Extension de product.product avec onglet Recherche de Fournisseurs
    
    SIMPLIFIÉ: Seulement Référence + Marque (pas de code fabricant)
    """
    _inherit = 'product.product'

    # Champs de recherche SIMPLIFIÉS
    manufacturer_ref = fields.Char(
        string='Référence fabricant',
        index=True,
        help="Référence du produit chez le fabricant (pour la recherche de prix)"
    )
    
    manufacturer_brand = fields.Char(
        string='Marque du fabricant',
        help="Nom de la marque/fabricant (ex: Legrand, Schneider)"
    )
    
    # Correspondances trouvées
    price_match_ids = fields.One2many(
        comodel_name='price.match',
        inverse_name='product_id',
        string='Fournisseurs trouvés'
    )
    
    price_match_count = fields.Integer(
        string='Nb fournisseurs',
        compute='_compute_price_match_count',
        store=True
    )
    
    best_price = fields.Float(
        string='Meilleur prix',
        compute='_compute_best_price',
        store=False,
        digits='Product Price'
    )
    
    best_price_source = fields.Char(
        string='Meilleur fournisseur',
        compute='_compute_best_price',
        store=False
    )

    def _compute_price_match_count(self):
        for product in self:
            product.price_match_count = len(product.price_match_ids.filtered(
                lambda m: m.state not in ['rejected']
            ))

    def _compute_best_price(self):
        for product in self:
            valid_matches = product.price_match_ids.filtered(
                lambda m: m.state not in ['rejected'] and m.price > 0
            )
            
            if valid_matches:
                best = min(valid_matches, key=lambda m: m.price)
                product.best_price = best.price
                product.best_price_source = best.source_id.name
            else:
                product.best_price = 0.0
                product.best_price_source = False

    def action_search_suppliers(self):
        """
        Action principale: Ouvre le wizard de recherche de fournisseurs.
        Depuis l'onglet produit ou le menu principal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rechercher des fournisseurs'),
            'res_model': 'search.prices.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
                'default_reference': self.manufacturer_ref or self.default_code or '',
                'default_brand': self.manufacturer_brand or '',
            }
        }

    def action_view_price_matches(self):
        """Ouvre la liste des correspondances/fournisseurs trouvés"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Fournisseurs trouvés - %s') % self.name,
            'res_model': 'price.match',
            'view_mode': 'list,form',
            'domain': [('product_id', '=', self.id)],
            'context': {
                'default_product_id': self.id,
                'search_default_not_rejected': 1,
            }
        }

    def action_apply_best_supplier(self):
        """
        Applique automatiquement le meilleur prix trouvé à l'onglet Achats.
        """
        self.ensure_one()
        
        valid_matches = self.price_match_ids.filtered(
            lambda m: m.state not in ['rejected'] and m.price > 0
        )
        
        if not valid_matches:
            raise UserError(_("Aucun fournisseur avec prix valide trouvé."))
        
        best_match = min(valid_matches, key=lambda m: m.price)
        return best_match.action_apply_to_purchases()

    def action_apply_all_suppliers(self):
        """
        Applique TOUS les fournisseurs trouvés à l'onglet Achats.
        """
        self.ensure_one()
        
        valid_matches = self.price_match_ids.filtered(
            lambda m: m.state not in ['rejected', 'applied'] and m.price > 0
        )
        
        if not valid_matches:
            raise UserError(_("Aucun nouveau fournisseur à ajouter."))
        
        count = 0
        for match in valid_matches:
            try:
                match.action_apply_to_purchases()
                count += 1
            except Exception as e:
                _logger.warning(f"Erreur ajout fournisseur {match.display_name}: {e}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fournisseurs ajoutés'),
                'message': _("%d fournisseur(s) ajouté(s) à l'onglet Achats.") % count,
                'type': 'success',
                'sticky': False,
            }
        }


class ProductTemplate(models.Model):
    """
    Extension de product.template pour exposer les champs de recherche
    """
    _inherit = 'product.template'

    manufacturer_ref = fields.Char(
        string='Référence fabricant',
        compute='_compute_manufacturer_fields',
        inverse='_inverse_manufacturer_ref',
        store=True
    )
    
    manufacturer_brand = fields.Char(
        string='Marque du fabricant',
        compute='_compute_manufacturer_fields',
        inverse='_inverse_manufacturer_brand',
        store=True
    )

    @api.depends('product_variant_ids', 'product_variant_ids.manufacturer_ref',
                 'product_variant_ids.manufacturer_brand')
    def _compute_manufacturer_fields(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                variant = template.product_variant_ids[0]
                template.manufacturer_ref = variant.manufacturer_ref
                template.manufacturer_brand = variant.manufacturer_brand
            else:
                template.manufacturer_ref = False
                template.manufacturer_brand = False

    def _inverse_manufacturer_ref(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids[0].manufacturer_ref = template.manufacturer_ref

    def _inverse_manufacturer_brand(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids[0].manufacturer_brand = template.manufacturer_brand
