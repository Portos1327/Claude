# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Remises par famille fabricant + dérogations par référence
Données issues de Rebates.qdbr (base SQLite)
Structure: RowID, Version, Date, ManufacturerCode, SupplierCode, RebateCode, Rebate,
           DerogationRebate, UseDerogation, RebateLabel, RebateComment

Deux types de remises:
  - Remises famille  (qdv.tarif.rebate)  : importées depuis Rebates.qdbr, modifiables
  - Dérogations réf. (qdv.tarif.derogation): créées manuellement, assignables à un article
"""
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class QdvTarifRebate(models.Model):
    _name = 'qdv.tarif.rebate'
    _description = 'Remise Famille QDV'
    _order = 'base_id, rebate_code'

    base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Base Fabricant',
        required=True,
        ondelete='cascade',
        index=True
    )
    manufacturer_code = fields.Char(
        string='Code Fabricant',
        related='base_id.manufacturer_code',
        store=True,
        index=True
    )

    # =========================================================================
    # DONNÉES REMISES (depuis Rebates.qdbr - modifiables)
    # =========================================================================
    rebate_code = fields.Char(
        string='Code Famille',
        required=True,
        help='Code famille remise QDV (ex: 219_011, 217_*)'
    )
    rebate_label = fields.Char(
        string='Libellé Famille',
        help='Description de la famille (ex: INTERS DIFF.DX3 ID 2P VIS)'
    )
    # Prix tarif NON modifiable - lecture seule
    rebate_value = fields.Float(
        string='Remise catalogue (%)',
        digits=(5, 2),
        help='Taux de remise catalogue issu de Rebates.qdbr — non modifiable directement'
    )
    # Remise négociée - modifiable librement
    negotiated_value = fields.Float(
        string='Remise négociée (%)',
        digits=(5, 2),
        help='Remise négociée avec le fabricant — remplace la remise catalogue si renseignée'
    )
    use_negotiated = fields.Boolean(
        string='Utiliser remise négociée',
        default=False,
        help='Si coché, la remise négociée est utilisée à la place de la remise catalogue'
    )
    effective_rebate = fields.Float(
        string='Remise effective (%)',
        compute='_compute_effective_rebate',
        store=True,
        digits=(5, 2),
        help='Remise réellement appliquée dans les calculs de prix net'
    )
    rebate_comment = fields.Char(string='Commentaire / Note')

    # Indicateurs hiérarchie
    is_default = fields.Boolean(
        string='Famille principale (wildcard)',
        compute='_compute_is_default',
        store=True,
        help='True si le code se termine par * — remise par défaut de toute la famille'
    )
    parent_code = fields.Char(
        string='Code famille parent',
        compute='_compute_parent_code',
        store=True,
        help='Code famille parent (ex: pour 219_011, le parent est 219_*)'
    )

    # Nombre d'articles de cette base utilisant ce code remise
    article_count = fields.Integer(
        string='Articles concernés',
        compute='_compute_article_count',
        help='Nombre d\'articles de cette base ayant ce code remise'
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('rebate_value', 'negotiated_value', 'use_negotiated')
    def _compute_effective_rebate(self):
        for rec in self:
            if rec.use_negotiated and rec.negotiated_value:
                rec.effective_rebate = rec.negotiated_value
            else:
                rec.effective_rebate = rec.rebate_value

    @api.depends('rebate_code')
    def _compute_is_default(self):
        for rec in self:
            rec.is_default = bool(rec.rebate_code and rec.rebate_code.endswith('_*'))

    @api.depends('rebate_code')
    def _compute_parent_code(self):
        for rec in self:
            code = rec.rebate_code or ''
            if code.endswith('_*') or not code:
                rec.parent_code = False
            else:
                parts = code.split('_')
                if len(parts) >= 2:
                    rec.parent_code = parts[0] + '_*'
                else:
                    rec.parent_code = False

    def _compute_article_count(self):
        for rec in self:
            rec.article_count = self.env['qdv.tarif.article'].search_count([
                ('base_id', '=', rec.base_id.id),
                ('rebate_code', '=', rec.rebate_code),
            ])

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_view_articles(self):
        """Ouvre les articles de cette base utilisant ce code remise"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articles - Remise %s') % self.rebate_code,
            'res_model': 'qdv.tarif.article',
            'view_mode': 'list,form',
            'domain': [
                ('base_id', '=', self.base_id.id),
                ('rebate_code', '=', self.rebate_code),
            ],
        }

    def action_apply_to_articles(self):
        """Recalcule le prix net de tous les articles concernés par cette remise"""
        self.ensure_one()
        articles = self.env['qdv.tarif.article'].search([
            ('base_id', '=', self.base_id.id),
            ('rebate_code', '=', self.rebate_code),
        ])
        count = 0
        for art in articles:
            art._compute_net_price()
            # Force le recalcul stocké
            art.write({'rebate_value': self.effective_rebate})
            count += 1
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Remise appliquée'),
                'message': _('%d articles mis à jour avec %.2f%%') % (count, self.effective_rebate),
                'type': 'success',
                'sticky': False,
            }
        }


