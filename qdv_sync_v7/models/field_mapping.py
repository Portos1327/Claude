# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QdvFieldMapping(models.Model):
    """Mapping des champs entre Odoo et QDV - COLONNES DYNAMIQUES"""
    _name = 'qdv.field.mapping'
    _description = 'Mapping champs QDV'
    _order = 'qdv_table, sequence'

    supplier_id = fields.Many2one('qdv.supplier', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, string='Actif')
    
    # Table QDV
    qdv_table = fields.Selection([
        ('articles', 'Articles'),
        ('columns_data_mt', 'ColumnsDataMT (Prix €/m)'),
        ('columns_data_wf', 'ColumnsDataWF (Prix forfait)'),
        ('extended_data', 'ExtendedData (Données étendues)'),
    ], string='Table QDV', required=True, default='articles')
    
    # Colonne QDV - CHAR pour permettre les colonnes dynamiques
    qdv_column = fields.Char(string='Colonne QDV', required=True,
        help='Nom technique de la colonne QDV (ex: Reference, CostPerUnitMT, MaterialKindID)')
    qdv_column_title = fields.Char(string='Titre QDV', readonly=True,
        help='Titre affiché dans QDV (détecté par scan)')
    
    # Source de la valeur
    value_source = fields.Selection([
        ('odoo_field', 'Champ Odoo'),
        ('static', 'Valeur statique'),
        ('template', 'Template (avec variables)'),
    ], string='Source valeur', default='odoo_field', required=True)
    
    # Champ Odoo
    odoo_field = fields.Char(string='Champ Odoo',
        help='Nom technique du champ Odoo. Cliquez sur "Voir champs disponibles" pour la liste.')
    
    # Valeur statique
    static_value = fields.Char(string='Valeur statique')
    
    # Options
    is_key = fields.Boolean(string='Clé', default=False)
    
    sync_direction = fields.Selection([
        ('odoo_to_qdv', 'Odoo → QDV uniquement'),
        ('qdv_to_odoo', 'QDV → Odoo uniquement'),
        ('bidirectional', 'Bidirectionnel'),
        ('none', 'Pas de sync'),
    ], string='Direction sync', default='odoo_to_qdv', required=True)
    
    convert_family_to_code = fields.Boolean(string='Convertir en code famille', default=False)
    
    # Pour MaterialKindID - mapping automatique par famille
    auto_material_kind = fields.Boolean(string='MaterialKindID auto', default=False,
        help='Détermine automatiquement le MaterialKindID basé sur la famille')

    @api.onchange('qdv_column')
    def _onchange_qdv_column(self):
        """Définit automatiquement la table selon la colonne"""
        if self.qdv_column:
            col = self.qdv_column.lower()
            if col in ('costperunitmt', 'rebate', 'costperunitmtbrut', 'materialkindid', 'coefficientmt'):
                self.qdv_table = 'columns_data_mt'
            elif col in ('costperunitwf', 'rebatewf', 'timekindid', 'coefficientwf', 'timeperunit'):
                self.qdv_table = 'columns_data_wf'
            elif col in ('textvalue', 'numericvalues'):
                self.qdv_table = 'extended_data'
            else:
                self.qdv_table = 'articles'
        
        # Suggestions automatiques
        auto_map = {
            'Reference': ('reference', 'odoo_field'),
            'Description': ('designation', 'odoo_field'),
            'Family': ('family', 'odoo_field'),
            'Manufacturer': ('manufacturer_name', 'odoo_field'),
            'UserDefinedField': ('_template', 'template'),
            'Unit': ('_static', 'static'),
            'ArticleDate': ('date_tarif', 'odoo_field'),
            'CostPerUnitMT': ('price_net', 'odoo_field'),
            'Rebate': ('discount', 'odoo_field'),
        }
        if self.qdv_column in auto_map:
            self.odoo_field, self.value_source = auto_map[self.qdv_column]
            if self.qdv_column == 'Unit':
                self.static_value = 'm'
            elif self.qdv_column == 'Family':
                self.convert_family_to_code = True
            elif self.qdv_column == 'MaterialKindID':
                self.auto_material_kind = True

    @api.onchange('value_source')
    def _onchange_value_source(self):
        if self.value_source == 'static':
            self.odoo_field = '_static'
        elif self.value_source == 'template':
            self.odoo_field = '_template'


class QdvFieldsWizard(models.TransientModel):
    """Wizard pour afficher les champs disponibles"""
    _name = 'qdv.fields.wizard'
    _description = 'Liste des champs disponibles'

    supplier_id = fields.Many2one('qdv.supplier', string='Fournisseur')
    content = fields.Text(string='Champs disponibles', readonly=True)
    field_to_copy = fields.Char(string='Champ à copier')
