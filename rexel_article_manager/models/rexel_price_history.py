# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class RexelPriceHistory(models.Model):
    _name = 'rexel.price.history'
    _description = 'Historique des prix articles Rexel'
    _order = 'date desc, id desc'

    article_id = fields.Many2one('rexel.article', string='Article', required=True, ondelete='cascade', index=True)
    reference = fields.Char(related='article_id.reference_fabricant', string='Référence', store=True, index=True)
    designation = fields.Text(related='article_id.designation', string='Désignation', store=True)
    
    date = fields.Datetime(string='Date', required=True, default=fields.Datetime.now, index=True)
    prix_base = fields.Float(string='Prix de base', digits=(10, 5), required=True)
    prix_net = fields.Float(string='Prix net', digits=(10, 5), required=True)
    remise = fields.Float(string='Remise (%)', digits=(5, 2), compute='_compute_remise', store=True)
    
    # Source de la mise à jour
    source = fields.Selection([
        ('import', 'Import Esabora'),
        ('rexel_api', 'Mise à jour Rexel.fr'),
        ('manual', 'Manuel'),
    ], string='Source', default='import', required=True)
    
    user_id = fields.Many2one('res.users', string='Utilisateur', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')

    @api.depends('prix_base', 'prix_net')
    def _compute_remise(self):
        """Calcule la remise en pourcentage"""
        for record in self:
            if record.prix_base and record.prix_base > 0:
                record.remise = ((record.prix_base - record.prix_net) / record.prix_base) * 100
            else:
                record.remise = 0.0

    @api.depends('reference', 'date', 'prix_net')
    def _compute_display_name(self):
        """Affichage personnalisé (remplace name_get dépréciée)"""
        for record in self:
            if record.date:
                record.display_name = f"{record.reference} - {record.date.strftime('%d/%m/%Y %H:%M')} - {record.prix_net}€"
            else:
                record.display_name = f"{record.reference} - {record.prix_net}€"
