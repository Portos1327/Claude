# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class RunMatchingWizard(models.TransientModel):
    """Wizard pour lancer le matching automatique"""
    _name = 'cable.run.matching.wizard'
    _description = 'Lancer le matching'

    pricelist_ids = fields.Many2many(
        'cable.pricelist',
        string='Tarifs à traiter',
        help='Laisser vide pour traiter tous les tarifs importés'
    )
    
    scope = fields.Selection([
        ('selected', 'Tarifs sélectionnés'),
        ('unmatched', 'Articles non correspondus uniquement'),
        ('all', 'Tous les articles'),
    ], string='Portée', default='selected', required=True)
    
    create_masters = fields.Boolean(
        string='Créer produits maîtres',
        default=True,
        help='Créer automatiquement les produits maîtres non existants'
    )
    
    min_score = fields.Integer(
        string='Score minimum',
        default=70,
        help='Score minimum pour accepter une correspondance (0-100)'
    )
    
    # Résultats
    result_log = fields.Text(string='Résultats', readonly=True)
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('done', 'Terminé'),
    ], string='État', default='draft')
    
    processed_count = fields.Integer(string='Traités', readonly=True)
    matched_count = fields.Integer(string='Correspondances', readonly=True)
    created_count = fields.Integer(string='Créés', readonly=True)
    
    def action_run(self):
        """Lancer le matching"""
        self.ensure_one()
        
        engine = self.env['cable.matching.engine']
        
        # Déterminer les tarifs à traiter
        if self.pricelist_ids:
            pricelist_ids = self.pricelist_ids.ids
        else:
            pricelists = self.env['cable.pricelist'].search([
                ('state', 'in', ('imported', 'matched'))
            ])
            pricelist_ids = pricelists.ids
        
        if not pricelist_ids:
            raise UserError(_("Aucun tarif à traiter."))
        
        _logger.info(f"Lancement matching pour {len(pricelist_ids)} tarifs")
        
        # Lancer le matching
        stats = engine.run_matching_batch(
            pricelist_ids=pricelist_ids,
            create_masters=self.create_masters
        )
        
        # Mettre à jour l'état des tarifs
        for pricelist in self.env['cable.pricelist'].browse(pricelist_ids):
            if pricelist.state == 'imported':
                pricelist.state = 'matched'
        
        # Résultats
        self.processed_count = stats.get('processed', 0)
        self.matched_count = stats.get('matched', 0)
        self.created_count = stats.get('created', 0)
        
        log_lines = [
            "✅ Matching terminé",
            "",
            "📊 Résultats:",
            f"  • Articles traités: {self.processed_count}",
            f"  • Correspondances trouvées: {self.matched_count}",
            f"  • Produits maîtres créés: {self.created_count}",
            f"  • Échecs: {stats.get('failed', 0)}",
        ]
        
        self.result_log = '\n'.join(log_lines)
        self.state = 'done'
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_view_matches(self):
        """Voir les correspondances créées"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Correspondances',
            'res_model': 'cable.pricelist.line',
            'view_mode': 'list,form',
            'domain': [
                ('pricelist_id', 'in', self.pricelist_ids.ids if self.pricelist_ids else []),
                ('master_product_id', '!=', False)
            ],
            'context': {'search_default_group_by_master': 1},
        }
