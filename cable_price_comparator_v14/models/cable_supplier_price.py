# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CableSupplierPrice(models.Model):
    """Prix fournisseur pour un câble maître
    
    Ce modèle sépare clairement les données fournisseur du produit maître.
    Chaque enregistrement représente un prix d'un fournisseur spécifique
    pour un câble maître donné.
    """
    _name = 'cable.supplier.price'
    _description = 'Prix fournisseur câble'
    _order = 'cable_master_id, price_per_ml'
    _rec_name = 'display_name'

    # Lien vers le câble maître (source de vérité)
    cable_master_id = fields.Many2one(
        'cable.product.master',
        string='Câble maître',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    # Fournisseur
    supplier_id = fields.Many2one(
        'cable.supplier',
        string='Fournisseur',
        required=True,
        index=True
    )
    supplier_code = fields.Char(
        related='supplier_id.code',
        string='Code fournisseur',
        store=True
    )
    
    # Identification fournisseur
    supplier_ref = fields.Char(
        string='Référence fournisseur',
        index=True,
        help='Référence article chez ce fournisseur'
    )
    brand = fields.Char(
        string='Marque fabricant',
        help='Marque du fabricant (Nexans, Prysmian, etc.)'
    )
    ean = fields.Char(
        string='Code EAN',
        index=True
    )
    
    # Prix
    price_gross = fields.Float(
        string='Prix brut',
        digits='Product Price'
    )
    discount = fields.Float(
        string='Remise (%)',
        digits=(5, 2)
    )
    price_net = fields.Float(
        string='Prix net',
        digits='Product Price',
        required=True
    )
    price_unit = fields.Selection([
        ('km', '€/km'),
        ('m', '€/ml'),
        ('100m', '€/100m'),
        ('unit', '€/unité'),
    ], string='Unité prix', default='m', required=True)
    
    # Prix normalisé en €/ml pour comparaison
    price_per_ml = fields.Float(
        string='Prix €/ml',
        compute='_compute_price_per_ml',
        store=True,
        digits=(12, 4)
    )
    
    # Disponibilité
    availability = fields.Selection([
        ('available', 'Disponible'),
        ('on_order', 'Sur commande'),
        ('out_of_stock', 'Rupture'),
        ('discontinued', 'Arrêté'),
    ], string='Disponibilité', default='available')
    min_order_qty = fields.Float(string='Qté mini commande')
    lead_time_days = fields.Integer(string='Délai (jours)')
    
    # Médias et documentation
    image_url = fields.Char(string='URL Image')
    datasheet_url = fields.Char(string='URL Fiche technique')
    dop_url = fields.Char(string='URL DOP')
    
    # Tarif source
    pricelist_id = fields.Many2one(
        'cable.pricelist',
        string='Tarif source',
        help='Tarif d\'origine de ce prix'
    )
    date_price = fields.Date(
        string='Date du prix',
        default=fields.Date.today
    )
    
    # Variation M-1
    price_previous = fields.Float(
        string='Prix M-1 €/ml',
        digits=(12, 4)
    )
    price_variation = fields.Float(
        string='Variation (%)',
        compute='_compute_variation',
        store=True,
        digits=(5, 2)
    )
    
    # Indicateurs
    is_best_price = fields.Boolean(
        string='Meilleur prix',
        compute='_compute_is_best',
        store=True
    )
    
    display_name = fields.Char(
        string='Nom',
        compute='_compute_display_name',
        store=True
    )
    
    active = fields.Boolean(default=True)
    notes = fields.Text(string='Notes')
    
    @api.depends('supplier_id', 'cable_master_id', 'supplier_ref')
    def _compute_display_name(self):
        for rec in self:
            parts = []
            if rec.supplier_code:
                parts.append(f"[{rec.supplier_code}]")
            if rec.supplier_ref:
                parts.append(rec.supplier_ref)
            elif rec.cable_master_id:
                parts.append(rec.cable_master_id.name[:30])
            rec.display_name = ' '.join(parts) if parts else 'Prix'
    
    @api.depends('price_net', 'price_unit')
    def _compute_price_per_ml(self):
        """Convertit tous les prix en €/ml"""
        conversions = {
            'km': 0.001,
            'm': 1,
            '100m': 0.01,
            'unit': 1,
        }
        for rec in self:
            factor = conversions.get(rec.price_unit, 1)
            rec.price_per_ml = rec.price_net * factor if rec.price_net else 0
    
    @api.depends('price_per_ml', 'price_previous')
    def _compute_variation(self):
        """Calcule la variation par rapport au prix précédent"""
        for rec in self:
            if rec.price_previous and rec.price_per_ml:
                rec.price_variation = (
                    (rec.price_per_ml - rec.price_previous) / rec.price_previous * 100
                )
            else:
                rec.price_variation = 0
    
    @api.depends('cable_master_id.best_supplier_price_id')
    def _compute_is_best(self):
        """Indique si c'est le meilleur prix pour ce câble"""
        for rec in self:
            rec.is_best_price = (
                rec.cable_master_id.best_supplier_price_id.id == rec.id
                if rec.cable_master_id.best_supplier_price_id else False
            )
    
    _sql_constraints = [
        ('unique_supplier_cable', 
         'UNIQUE(cable_master_id, supplier_id)',
         'Un seul prix par fournisseur et par câble maître.')
    ]
