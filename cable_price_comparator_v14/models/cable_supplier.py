# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CableSupplier(models.Model):
    """Fournisseurs de câbles (fabricants ou distributeurs)"""
    _name = 'cable.supplier'
    _description = 'Fournisseur de câbles'
    _order = 'sequence, name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Nom',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='Code court pour identification (ex: SERMES, ELEN, NEXANS)'
    )
    sequence = fields.Integer(string='Séquence', default=10)
    
    supplier_type = fields.Selection([
        ('manufacturer', 'Fabricant'),
        ('distributor', 'Distributeur'),
        ('wholesaler', 'Grossiste'),
    ], string='Type', default='manufacturer', required=True)
    
    # Informations contact
    partner_id = fields.Many2one(
        'res.partner',
        string='Partenaire Odoo',
        help='Lien vers le partenaire Odoo pour les achats'
    )
    website = fields.Char(string='Site web')
    email = fields.Char(string='Email')
    phone = fields.Char(string='Téléphone')
    
    # Configuration import Excel
    excel_config_ids = fields.One2many(
        'cable.supplier.excel.config',
        'supplier_id',
        string='Configurations Excel'
    )
    
    # Colonnes par défaut
    default_ref_column = fields.Char(
        string='Colonne Référence',
        default='REFARTICLE',
        help='Nom de la colonne référence dans les fichiers Excel'
    )
    default_designation_column = fields.Char(
        string='Colonne Désignation',
        default='Désignation'
    )
    default_price_column = fields.Char(
        string='Colonne Prix',
        default='NET'
    )
    default_unit_column = fields.Char(
        string='Colonne Unité',
        default='GRM'
    )
    default_family_column = fields.Char(
        string='Colonne Famille',
        default='Famille'
    )
    
    # Unité de prix par défaut
    default_price_unit = fields.Selection([
        ('km', '€/km'),
        ('m', '€/m'),
        ('unit', '€/unité'),
        ('100m', '€/100m'),
        ('kg', '€/kg'),
    ], string='Unité prix par défaut', default='km')
    
    # Statistiques
    pricelist_count = fields.Integer(
        string='Nombre de tarifs',
        compute='_compute_counts'
    )
    line_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_counts'
    )
    last_import_date = fields.Datetime(
        string='Dernier import',
        compute='_compute_last_import'
    )
    
    active = fields.Boolean(string='Actif', default=True)
    notes = fields.Text(string='Notes')
    
    @api.depends()
    def _compute_counts(self):
        for supplier in self:
            pricelists = self.env['cable.pricelist'].search([
                ('supplier_id', '=', supplier.id)
            ])
            supplier.pricelist_count = len(pricelists)
            supplier.line_count = self.env['cable.pricelist.line'].search_count([
                ('pricelist_id', 'in', pricelists.ids)
            ])
    
    @api.depends()
    def _compute_last_import(self):
        for supplier in self:
            last_pricelist = self.env['cable.pricelist'].search([
                ('supplier_id', '=', supplier.id)
            ], order='date_import desc', limit=1)
            supplier.last_import_date = last_pricelist.date_import if last_pricelist else False
    
    def action_view_pricelists(self):
        """Ouvrir la liste des tarifs du fournisseur"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Tarifs {self.name}',
            'res_model': 'cable.pricelist',
            'view_mode': 'list,form',
            'domain': [('supplier_id', '=', self.id)],
            'context': {'default_supplier_id': self.id},
        }
    
    def action_view_lines(self):
        """Ouvrir la liste des lignes d'articles"""
        self.ensure_one()
        pricelists = self.env['cable.pricelist'].search([
            ('supplier_id', '=', self.id)
        ])
        return {
            'type': 'ir.actions.act_window',
            'name': f'Articles {self.name}',
            'res_model': 'cable.pricelist.line',
            'view_mode': 'list,form',
            'domain': [('pricelist_id', 'in', pricelists.ids)],
        }
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Le code fournisseur doit être unique.')
    ]


class CableSupplierExcelConfig(models.Model):
    """Configuration de mapping Excel par fournisseur"""
    _name = 'cable.supplier.excel.config'
    _description = 'Configuration Excel fournisseur'
    _order = 'sequence'

    supplier_id = fields.Many2one(
        'cable.supplier',
        string='Fournisseur',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Nom configuration', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    
    # Feuille Excel
    sheet_name = fields.Char(
        string='Nom de la feuille',
        help='Nom de la feuille Excel à importer (laisser vide pour la première)'
    )
    header_row = fields.Integer(
        string='Ligne d\'en-tête',
        default=0,
        help='Numéro de la ligne contenant les en-têtes (0 = première ligne)'
    )
    
    # Mapping des colonnes
    col_reference = fields.Char(string='Colonne Référence', required=True)
    col_designation = fields.Char(string='Colonne Désignation', required=True)
    col_price_gross = fields.Char(string='Colonne Prix Brut')
    col_discount = fields.Char(string='Colonne Remise')
    col_price_net = fields.Char(string='Colonne Prix Net')
    col_unit = fields.Char(string='Colonne Unité')
    col_family = fields.Char(string='Colonne Famille')
    col_weight = fields.Char(string='Colonne Poids')
    col_ean = fields.Char(string='Colonne Code EAN')
    col_datasheet_url = fields.Char(string='Colonne Lien fiche technique')
    
    # Unité de prix
    price_unit = fields.Selection([
        ('km', '€/km'),
        ('m', '€/m'),
        ('unit', '€/unité'),
        ('100m', '€/100m'),
        ('kg', '€/kg'),
    ], string='Unité prix', default='km')
    
    active = fields.Boolean(string='Actif', default=True)
    notes = fields.Text(string='Notes')
