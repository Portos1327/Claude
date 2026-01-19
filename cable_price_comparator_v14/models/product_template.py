# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProductTemplate(models.Model):
    """Extension de product.template pour les câbles"""
    _inherit = 'product.template'
    
    # Lien vers le câble maître
    cable_master_id = fields.Many2one(
        'cable.product.master',
        string='Câble maître',
        help='Référence vers le câble maître pour comparaison de prix'
    )
    
    # Fiches techniques et documents
    datasheet_url = fields.Char(
        string='Fiche technique (URL)',
        help='Lien vers la fiche technique PDF du produit'
    )
    dop_url = fields.Char(
        string='DOP (URL)',
        help='Lien vers la Déclaration de Performance'
    )
    
    # Informations techniques câble
    cable_type_code = fields.Char(
        string='Type câble',
        help='Code type: R2V, AR2V, H07V-U, etc.'
    )
    cable_config = fields.Char(
        string='Configuration',
        help='Configuration: 3G, 4X, 1X, etc.'
    )
    cable_section = fields.Float(
        string='Section (mm²)',
        digits=(6, 2)
    )
    
    def action_open_datasheet(self):
        """Ouvre la fiche technique dans un nouvel onglet"""
        self.ensure_one()
        if self.datasheet_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.datasheet_url,
                'target': 'new',
            }
        return False
    
    def action_open_dop(self):
        """Ouvre le DOP dans un nouvel onglet"""
        self.ensure_one()
        if self.dop_url:
            return {
                'type': 'ir.actions.act_url',
                'url': self.dop_url,
                'target': 'new',
            }
        return False
