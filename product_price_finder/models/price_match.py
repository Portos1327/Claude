# -*- coding: utf-8 -*-
"""
Price Match - Correspondances produit/article
==============================================

Ce modèle stocke les correspondances trouvées entre les produits Odoo
et les articles des différents modules de tarifs.

FONCTIONNALITÉ CLÉ: Association automatique avec l'onglet Achats
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class PriceMatch(models.Model):
    """
    Correspondance entre un produit Odoo et un article de tarif
    
    Permet de:
    - Tracker les associations produit <-> article
    - Remplir automatiquement l'onglet Achats (supplierinfo)
    - Lier l'article source au produit Odoo
    """
    _name = 'price.match'
    _description = 'Correspondance produit/prix'
    _order = 'product_id, price'
    _rec_name = 'display_name'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Produit Odoo',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    source_id = fields.Many2one(
        comodel_name='price.source',
        string='Source de prix',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Référence vers l'article source
    article_model = fields.Char(
        string='Modèle article',
        required=True
    )
    
    article_id = fields.Integer(
        string='ID article',
        required=True
    )
    
    # Informations de l'article
    reference = fields.Char(
        string='Référence fabricant',
        index=True
    )
    
    designation = fields.Char(
        string='Désignation'
    )
    
    brand = fields.Char(
        string='Marque/Fabricant'
    )
    
    # Prix
    price = fields.Float(
        string='Prix net',
        digits='Product Price'
    )
    
    price_base = fields.Float(
        string='Prix de base',
        digits='Product Price'
    )
    
    discount = fields.Float(
        string='Remise (%)'
    )
    
    unit = fields.Char(
        string='Unité'
    )
    
    # Fournisseur pour onglet Achats
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fournisseur',
        help="Fournisseur à utiliser dans l'onglet Achats"
    )
    
    supplierinfo_id = fields.Many2one(
        comodel_name='product.supplierinfo',
        string='Info fournisseur',
        help="Ligne créée dans l'onglet Achats du produit"
    )
    
    # État
    state = fields.Selection([
        ('found', 'Trouvé'),
        ('selected', 'Sélectionné'),
        ('applied', 'Appliqué aux Achats'),
        ('rejected', 'Rejeté'),
    ], string='État', default='found')
    
    is_best_price = fields.Boolean(
        string='Meilleur prix',
        compute='_compute_is_best_price',
        store=True
    )
    
    # Dates
    found_date = fields.Datetime(
        string='Date de découverte',
        default=fields.Datetime.now
    )
    
    last_update = fields.Datetime(
        string='Dernière mise à jour'
    )
    
    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('source_id', 'reference', 'brand', 'price')
    def _compute_display_name(self):
        for match in self:
            parts = [match.source_id.name or 'N/A']
            if match.brand:
                parts.append(match.brand)
            if match.reference:
                parts.append(match.reference)
            if match.price:
                parts.append(f"{match.price:.2f}€")
            match.display_name = ' - '.join(parts)

    @api.depends('product_id', 'price')
    def _compute_is_best_price(self):
        for match in self:
            if not match.product_id or not match.price:
                match.is_best_price = False
                continue
            
            min_match = self.search([
                ('product_id', '=', match.product_id.id),
                ('price', '>', 0),
                ('state', 'not in', ['rejected']),
            ], order='price asc', limit=1)
            
            match.is_best_price = min_match.id == match.id if min_match else False

    def _get_or_create_partner(self):
        """
        Récupère ou crée le partenaire fournisseur pour cette correspondance.
        Utilise le fournisseur de la source ou en crée un basé sur la marque.
        """
        self.ensure_one()
        
        # Priorité 1: Fournisseur déjà défini sur la correspondance
        if self.partner_id:
            return self.partner_id
        
        # Priorité 2: Fournisseur configuré sur la source
        if self.source_id.partner_id:
            self.partner_id = self.source_id.partner_id
            return self.partner_id
        
        # Priorité 3: Chercher ou créer basé sur la marque ou la source
        partner_name = self.brand or self.source_id.name
        
        partner = self.env['res.partner'].search([
            ('name', 'ilike', partner_name),
            ('supplier_rank', '>', 0),
        ], limit=1)
        
        if not partner:
            partner = self.env['res.partner'].create({
                'name': partner_name,
                'supplier_rank': 1,
                'company_type': 'company',
            })
            _logger.info(f"Fournisseur créé automatiquement: {partner_name}")
        
        self.partner_id = partner
        return partner

    def action_apply_to_purchases(self):
        """
        FONCTION PRINCIPALE: Applique cette correspondance à l'onglet Achats du produit.
        
        Crée ou met à jour:
        1. Le partenaire fournisseur (si nécessaire)
        2. La ligne product.supplierinfo
        3. Le lien article <-> produit dans le module source
        """
        self.ensure_one()
        
        if not self.price:
            raise UserError(_("Aucun prix disponible pour cette correspondance."))
        
        if not self.product_id:
            raise UserError(_("Aucun produit associé."))
        
        # 1. Obtenir le fournisseur
        partner = self._get_or_create_partner()
        
        # 2. Créer ou mettre à jour le supplierinfo
        SupplierInfo = self.env['product.supplierinfo']
        
        # Chercher une ligne existante pour ce fournisseur
        existing = SupplierInfo.search([
            ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
            ('partner_id', '=', partner.id),
        ], limit=1)
        
        vals = {
            'partner_id': partner.id,
            'product_tmpl_id': self.product_id.product_tmpl_id.id,
            'product_id': self.product_id.id,
            'price': self.price,
            'product_code': self.reference,
            'product_name': self.designation,
            'min_qty': 1.0,
        }
        
        if existing:
            existing.write(vals)
            self.supplierinfo_id = existing
        else:
            self.supplierinfo_id = SupplierInfo.create(vals)
        
        # 3. Lier l'article source au produit Odoo
        self._link_article_to_product()
        
        # 4. Mettre à jour l'état
        self.state = 'applied'
        self.last_update = fields.Datetime.now()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Fournisseur ajouté'),
                'message': _("Fournisseur: %s\nRéférence: %s\nPrix: %.2f €") % (
                    partner.name, self.reference, self.price
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def _link_article_to_product(self):
        """
        Crée le lien bidirectionnel entre l'article source et le produit Odoo.
        Met à jour le champ product_id de l'article dans le module source.
        """
        self.ensure_one()
        
        if not self.article_model or self.article_model not in self.env:
            return False
        
        if not self.source_id.product_field:
            return False
        
        try:
            article = self.env[self.article_model].browse(self.article_id)
            if article.exists() and hasattr(article, self.source_id.product_field):
                article.write({self.source_id.product_field: self.product_id.id})
                _logger.info(f"Article {self.reference} lié au produit {self.product_id.name}")
                return True
        except Exception as e:
            _logger.warning(f"Impossible de lier l'article: {e}")
        
        return False

    def action_view_source_article(self):
        """Ouvre la fiche de l'article source"""
        self.ensure_one()
        
        if self.article_model not in self.env:
            raise UserError(_("Le module %s n'est pas installé.") % self.article_model)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.article_model,
            'res_id': self.article_id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_update_price(self):
        """Met à jour le prix depuis la source"""
        self.ensure_one()
        
        if self.article_model not in self.env:
            raise UserError(_("Le module %s n'est pas installé.") % self.article_model)
        
        article = self.env[self.article_model].browse(self.article_id)
        if not article.exists():
            raise UserError(_("L'article source n'existe plus."))
        
        source = self.source_id
        vals = {'last_update': fields.Datetime.now()}
        
        if source.price_field and hasattr(article, source.price_field):
            vals['price'] = getattr(article, source.price_field, 0.0) or 0.0
        
        if source.price_base_field and hasattr(article, source.price_base_field):
            vals['price_base'] = getattr(article, source.price_base_field, 0.0) or 0.0
        
        if source.discount_field and hasattr(article, source.discount_field):
            vals['discount'] = getattr(article, source.discount_field, 0.0) or 0.0
        
        self.write(vals)
        
        # Mettre à jour aussi le supplierinfo si existant
        if self.supplierinfo_id and 'price' in vals:
            self.supplierinfo_id.price = vals['price']
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Prix mis à jour'),
                'message': _("Prix net: %.2f €") % vals.get('price', 0),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_reject(self):
        """Rejette cette correspondance"""
        self.state = 'rejected'

    def action_select(self):
        """Sélectionne cette correspondance pour application ultérieure"""
        self.state = 'selected'

    @api.model
    def create_from_search_result(self, product_id, result):
        """
        Crée une correspondance à partir d'un résultat de recherche.
        """
        # Vérifier si existe déjà
        existing = self.search([
            ('product_id', '=', product_id),
            ('source_id', '=', result.get('source_id')),
            ('article_id', '=', result.get('article_id')),
        ], limit=1)
        
        vals = {
            'product_id': product_id,
            'source_id': result.get('source_id'),
            'article_model': result.get('model_name'),
            'article_id': result.get('article_id'),
            'reference': result.get('reference'),
            'designation': result.get('designation'),
            'brand': result.get('brand'),
            'price': result.get('price', 0.0),
            'price_base': result.get('price_base', 0.0),
            'discount': result.get('discount', 0.0),
            'unit': result.get('unit'),
            'partner_id': result.get('partner_id'),
            'state': 'found',
        }
        
        if existing:
            existing.write(vals)
            return existing
        
        return self.create(vals)
