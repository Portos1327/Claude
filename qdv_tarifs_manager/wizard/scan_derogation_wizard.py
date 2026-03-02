# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Wizard de scan des dérogations
Recherche dans la base qdv.tarif.derogation si une dérogation correspond
au Code Fabricant + Référence de l'article courant.
Peut être lancé sur un article individuel ou en masse depuis la liste.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class QdvTarifScanDerogationWizard(models.TransientModel):
    _name = 'qdv.tarif.scan.derogation.wizard'
    _description = 'Wizard scan dérogations QDV'

    # =========================================================================
    # CONTEXTE
    # =========================================================================
    article_id = fields.Many2one(
        'qdv.tarif.article', string='Article', ondelete='cascade'
    )
    manufacturer_code = fields.Char(string='Code Fabricant', readonly=True)
    reference = fields.Char(string='Référence', readonly=True)

    # Mode: article unique ou scan masse
    scan_mode = fields.Selection([
        ('single', 'Article unique'),
        ('bulk', 'Tous les articles sans dérogation'),
    ], string='Mode scan', default='single', required=True)

    # Filtre pour le scan masse
    filter_base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Limiter au fabricant',
        help='Laisser vide pour scanner tous les fabricants'
    )

    # =========================================================================
    # RÉSULTAT DU SCAN
    # =========================================================================
    scan_done = fields.Boolean(default=False)
    result_line_ids = fields.One2many(
        'qdv.tarif.scan.derogation.result',
        'wizard_id',
        string='Correspondances trouvées'
    )
    result_count = fields.Integer(
        string='Correspondances', compute='_compute_result_count'
    )
    no_result_message = fields.Char(
        string='Message', compute='_compute_result_count'
    )

    @api.depends('result_line_ids')
    def _compute_result_count(self):
        for rec in self:
            rec.result_count = len(rec.result_line_ids)
            if rec.scan_done and rec.result_count == 0:
                rec.no_result_message = _("Aucune correspondance trouvée dans la base des dérogations.")
            else:
                rec.no_result_message = ''

    # =========================================================================
    # SCAN
    # =========================================================================
    def action_scan(self):
        """Lance la recherche des correspondances Code Fab + Référence"""
        self.ensure_one()
        self.result_line_ids.unlink()

        if self.scan_mode == 'single':
            articles = self.article_id
        else:
            domain = [('has_derogation', '=', False)]
            if self.filter_base_id:
                domain.append(('base_id', '=', self.filter_base_id.id))
            articles = self.env['qdv.tarif.article'].search(domain)

        results = []
        for article in articles:
            # Chercher dérogation correspondante: Code Fab + Référence
            derog = self.env['qdv.tarif.derogation'].search([
                ('manufacturer_code', '=', article.manufacturer_code),
                ('reference', '=', article.reference),
                ('active', '=', True),
            ], limit=1)

            if derog:
                results.append({
                    'wizard_id': self.id,
                    'article_id': article.id,
                    'derogation_id': derog.id,
                    'apply': True,  # coché par défaut
                    'current_derogation_id': article.derogation_id.id if article.derogation_id else False,
                })

        self.env['qdv.tarif.scan.derogation.result'].create(results)
        self.scan_done = True

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.tarif.scan.derogation.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # =========================================================================
    # APPLICATION
    # =========================================================================
    def action_apply_selected(self):
        """Applique les dérogations cochées aux articles correspondants"""
        self.ensure_one()
        to_apply = self.result_line_ids.filtered(lambda l: l.apply)

        if not to_apply:
            raise UserError(_("Aucune ligne sélectionnée à appliquer."))

        applied = 0
        for line in to_apply:
            article = line.article_id
            derog = line.derogation_id
            article.write({
                'derogation_id': derog.id,
                'rebate_code': derog.derogation_code,
                'rebate_value': derog.effective_rebate,
            })
            applied += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dérogations appliquées'),
                'message': _('%d article(s) mis à jour.') % applied,
                'type': 'success',
                'sticky': False,
            }
        }


class QdvTarifScanDerogationResult(models.TransientModel):
    """Ligne de résultat du scan dérogations"""
    _name = 'qdv.tarif.scan.derogation.result'
    _description = 'Résultat scan dérogation QDV'

    wizard_id = fields.Many2one(
        'qdv.tarif.scan.derogation.wizard', ondelete='cascade'
    )

    # Article trouvé
    article_id = fields.Many2one('qdv.tarif.article', string='Article', readonly=True)
    manufacturer_code = fields.Char(related='article_id.manufacturer_code', string='Fab.', readonly=True)
    reference = fields.Char(related='article_id.reference', string='Référence', readonly=True)
    designation = fields.Char(related='article_id.designation', string='Désignation', readonly=True)
    unit_price = fields.Float(related='article_id.unit_price', string='Prix tarif (€)', readonly=True, digits=(12, 4))
    current_rebate = fields.Float(related='article_id.rebate_value', string='Remise actuelle (%)', readonly=True, digits=(5, 2))
    current_net_price = fields.Float(related='article_id.net_price', string='Prix net actuel (€)', readonly=True, digits=(12, 4))

    # Dérogation proposée
    derogation_id = fields.Many2one('qdv.tarif.derogation', string='Dérogation trouvée', readonly=True)
    derog_code = fields.Char(related='derogation_id.derogation_code', string='Code dérog.', readonly=True)
    derog_label = fields.Char(related='derogation_id.derogation_label', string='Libellé', readonly=True)
    derog_rebate = fields.Float(related='derogation_id.effective_rebate', string='Remise dérog. (%)', readonly=True, digits=(5, 2))
    derog_net_price = fields.Float(related='derogation_id.effective_net_price', string='Prix net dérog. (€)', readonly=True, digits=(12, 4))
    derog_mode = fields.Selection(related='derogation_id.price_mode', string='Mode', readonly=True)

    # Dérogation actuelle de l'article (si déjà une)
    current_derogation_id = fields.Many2one('qdv.tarif.derogation', string='Dérogation actuelle', readonly=True)
    has_existing_derogation = fields.Boolean(
        string='Dérogation existante',
        compute='_compute_has_existing',
    )

    # Sélection
    apply = fields.Boolean(string='Appliquer', default=True)

    @api.depends('current_derogation_id')
    def _compute_has_existing(self):
        for rec in self:
            rec.has_existing_derogation = bool(rec.current_derogation_id)
