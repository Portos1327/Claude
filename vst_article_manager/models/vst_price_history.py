# -*- coding: utf-8 -*-

from odoo import models, fields, api


class VstPriceHistory(models.Model):
    _name = 'vst.price.history'
    _description = 'Historique des prix VST'
    _order = 'date desc'
    _rec_name = 'article_id'

    article_id = fields.Many2one(
        'vst.article',
        string='Article',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    date = fields.Datetime(
        string='Date',
        default=fields.Datetime.now,
        required=True
    )
    
    type_prix = fields.Selection([
        ('achat_adherent', 'Prix Achat Adhérent'),
        ('public_ht', 'Prix Public HT'),
        ('public_ttc', 'Prix Public TTC'),
    ], string='Type de prix', default='achat_adherent')
    
    prix_ancien = fields.Float(
        string='Ancien prix',
        digits='Product Price'
    )
    
    prix_nouveau = fields.Float(
        string='Nouveau prix',
        digits='Product Price'
    )
    
    variation = fields.Float(
        string='Variation (%)',
        compute='_compute_variation',
        store=True,
        digits=(5, 2)
    )
    
    variation_absolue = fields.Float(
        string='Variation (€)',
        compute='_compute_variation',
        store=True,
        digits='Product Price'
    )

    @api.depends('prix_ancien', 'prix_nouveau')
    def _compute_variation(self):
        for record in self:
            record.variation_absolue = (record.prix_nouveau or 0) - (record.prix_ancien or 0)
            if record.prix_ancien and record.prix_ancien != 0:
                record.variation = ((record.prix_nouveau - record.prix_ancien) / record.prix_ancien) * 100
            else:
                record.variation = 0.0
