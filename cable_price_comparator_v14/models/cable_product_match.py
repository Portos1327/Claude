# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CableProductMatch(models.Model):
    """Correspondance entre lignes de tarif et produit maître"""
    _name = 'cable.product.match'
    _description = 'Correspondance produit câble'
    _order = 'master_product_id, match_score desc'

    master_product_id = fields.Many2one(
        'cable.product.master',
        string='Produit maître',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    pricelist_line_id = fields.Many2one(
        'cable.pricelist.line',
        string='Ligne tarif',
        required=True,
        ondelete='cascade',
        index=True
    )
    supplier_id = fields.Many2one(
        related='pricelist_line_id.supplier_id',
        string='Fournisseur',
        store=True
    )
    
    # Score et méthode
    match_score = fields.Integer(
        string='Score',
        help='Score de confiance 0-100'
    )
    match_method = fields.Selection([
        ('exact_ref', 'Référence exacte'),
        ('ean', 'Code EAN'),
        ('normalized_ref', 'Référence normalisée'),
        ('designation', 'Analyse désignation'),
        ('characteristics', 'Caractéristiques'),
        ('fuzzy', 'Correspondance floue'),
        ('manual', 'Manuel'),
    ], string='Méthode')
    
    # Détails du matching
    match_details = fields.Text(
        string='Détails',
        help='Explication du matching'
    )
    
    # Validation
    is_validated = fields.Boolean(
        string='Validé',
        default=False,
        help='Correspondance validée manuellement'
    )
    validated_by = fields.Many2one(
        'res.users',
        string='Validé par'
    )
    validated_date = fields.Datetime(string='Date validation')
    
    # État
    state = fields.Selection([
        ('suggested', 'Suggéré'),
        ('validated', 'Validé'),
        ('rejected', 'Rejeté'),
    ], string='État', default='suggested')
    
    def action_validate(self):
        """Valider la correspondance"""
        for match in self:
            match.write({
                'state': 'validated',
                'is_validated': True,
                'validated_by': self.env.uid,
                'validated_date': fields.Datetime.now(),
            })
            # Mettre à jour la ligne de tarif
            match.pricelist_line_id.write({
                'master_product_id': match.master_product_id.id,
                'match_score': match.match_score,
                'match_method': match.match_method,
            })
    
    def action_reject(self):
        """Rejeter la correspondance"""
        self.write({'state': 'rejected'})
    
    _sql_constraints = [
        ('line_unique', 'UNIQUE(pricelist_line_id)', 
         'Une ligne de tarif ne peut avoir qu\'une seule correspondance.')
    ]
