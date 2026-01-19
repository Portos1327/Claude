# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CablePricelist(models.Model):
    """Tarif câbles importé d'un fournisseur"""
    _name = 'cable.pricelist'
    _description = 'Tarif câbles fournisseur'
    _order = 'date_validity desc, date_import desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('Nouveau')
    )
    
    supplier_id = fields.Many2one(
        'cable.supplier',
        string='Fournisseur',
        required=True,
        tracking=True,
        ondelete='restrict'
    )
    supplier_code = fields.Char(
        related='supplier_id.code',
        string='Code fournisseur',
        store=True
    )
    
    # Dates
    date_import = fields.Datetime(
        string='Date d\'import',
        default=fields.Datetime.now,
        required=True
    )
    date_validity = fields.Date(
        string='Date de validité',
        help='Date à partir de laquelle ce tarif est applicable'
    )
    date_validity_end = fields.Date(
        string='Fin de validité',
        help='Date de fin de validité du tarif'
    )
    period_name = fields.Char(
        string='Période',
        help='Nom de la période tarifaire (ex: Septembre 2025)'
    )
    
    # Fichier source
    file_name = fields.Char(string='Nom du fichier')
    file_data = fields.Binary(
        string='Fichier source',
        attachment=True
    )
    sheet_name = fields.Char(
        string='Feuille importée',
        help='Nom de la feuille Excel importée'
    )
    
    # État
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('imported', 'Importé'),
        ('matched', 'Correspondances établies'),
        ('validated', 'Validé'),
        ('archived', 'Archivé'),
    ], string='État', default='draft', tracking=True)
    
    # Lignes
    line_ids = fields.One2many(
        'cable.pricelist.line',
        'pricelist_id',
        string='Lignes'
    )
    
    # Statistiques
    line_count = fields.Integer(
        string='Nombre d\'articles',
        compute='_compute_stats',
        store=True
    )
    matched_count = fields.Integer(
        string='Correspondances',
        compute='_compute_stats',
        store=True
    )
    unmatched_count = fields.Integer(
        string='Non correspondus',
        compute='_compute_stats',
        store=True
    )
    match_rate = fields.Float(
        string='Taux de correspondance (%)',
        compute='_compute_stats',
        store=True
    )
    
    # Prix
    price_min = fields.Float(
        string='Prix min',
        compute='_compute_price_stats',
        digits='Product Price'
    )
    price_max = fields.Float(
        string='Prix max',
        compute='_compute_price_stats',
        digits='Product Price'
    )
    price_avg = fields.Float(
        string='Prix moyen',
        compute='_compute_price_stats',
        digits='Product Price'
    )
    
    notes = fields.Text(string='Notes d\'import')
    active = fields.Boolean(string='Actif', default=True)
    
    @api.depends('line_ids', 'line_ids.master_product_id')
    def _compute_stats(self):
        for pricelist in self:
            lines = pricelist.line_ids
            pricelist.line_count = len(lines)
            matched = lines.filtered(lambda l: l.master_product_id)
            pricelist.matched_count = len(matched)
            pricelist.unmatched_count = pricelist.line_count - pricelist.matched_count
            pricelist.match_rate = (
                (pricelist.matched_count / pricelist.line_count * 100)
                if pricelist.line_count > 0 else 0
            )
    
    @api.depends('line_ids.price_net')
    def _compute_price_stats(self):
        for pricelist in self:
            prices = pricelist.line_ids.filtered(
                lambda l: l.price_net and l.price_net > 0
            ).mapped('price_net')
            if prices:
                pricelist.price_min = min(prices)
                pricelist.price_max = max(prices)
                pricelist.price_avg = sum(prices) / len(prices)
            else:
                pricelist.price_min = 0
                pricelist.price_max = 0
                pricelist.price_avg = 0
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('Nouveau')) == _('Nouveau'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'cable.pricelist'
                ) or _('Nouveau')
        return super().create(vals_list)
    
    def action_set_imported(self):
        """Marquer comme importé"""
        self.write({'state': 'imported'})
    
    def action_run_matching(self):
        """Lancer le matching automatique"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Lancer le matching',
            'res_model': 'cable.run.matching.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_pricelist_ids': [(6, 0, self.ids)],
            }
        }
    
    def action_validate(self):
        """Valider le tarif"""
        for pricelist in self:
            if pricelist.state not in ('imported', 'matched'):
                raise UserError(_("Le tarif doit être importé ou correspondé avant validation."))
        self.write({'state': 'validated'})
    
    def action_archive(self):
        """Archiver le tarif"""
        self.write({'state': 'archived', 'active': False})
    
    def action_view_lines(self):
        """Voir les lignes du tarif"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Articles - {self.name}',
            'res_model': 'cable.pricelist.line',
            'view_mode': 'list,form',
            'domain': [('pricelist_id', '=', self.id)],
            'context': {'default_pricelist_id': self.id},
        }
    
    def action_view_unmatched(self):
        """Voir les articles non correspondus"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Non correspondus - {self.name}',
            'res_model': 'cable.pricelist.line',
            'view_mode': 'list,form',
            'domain': [
                ('pricelist_id', '=', self.id),
                ('master_product_id', '=', False)
            ],
        }
