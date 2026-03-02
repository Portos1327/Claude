# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Dérogations par référence article
Une dérogation = Code Fabricant + Référence + (Remise % OU Prix net)

Exemple: 062525 LEG → article LEGRAND réf 062525, remise ou prix net spécifique

Flux:
  1. Saisie manuelle dans l'onglet "Dérogations" (ou import)
  2. Scan depuis "Articles QDV" → recherche Code Fab + Référence
  3. Si trouvé → wizard propose d'appliquer
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class QdvTarifDerogation(models.Model):
    _name = 'qdv.tarif.derogation'
    _description = 'Dérogation remise QDV par référence'
    _order = 'manufacturer_code, derogation_code'
    _rec_name = 'derogation_code'

    # =========================================================================
    # IDENTITÉ DE LA DÉROGATION
    # =========================================================================
    derogation_code = fields.Char(
        string='Code dérogation',
        required=True,
        index=True,
        help='Identifiant unique de la dérogation.\n'
             'Convention suggérée: RÉFÉRENCE CODEFAB (ex: 062525 LEG)\n'
             'Peut aussi être un nom de chantier, accord, etc.'
    )
    derogation_label = fields.Char(
        string='Libellé',
        required=True,
        help='Description: accord commercial, chantier, client...'
    )
    active = fields.Boolean(default=True)
    valid_from = fields.Date(string='Valable du')
    valid_to = fields.Date(string='Valable jusqu\'au')
    comment = fields.Text(string='Motif / Notes')

    # =========================================================================
    # FABRICANT CIBLÉ
    # =========================================================================
    manufacturer_code = fields.Char(
        string='Code fabricant',
        required=True,
        index=True,
        help='Code QDV du fabricant concerné (ex: LEG, SCH, ABB...)'
    )
    base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Base tarif',
        compute='_compute_base_id',
        store=False,  # Non-stored : évite les recomputes en cascade lors des transactions
        help='Base tarif correspondante (calculée depuis le code fabricant)'
    )

    # =========================================================================
    # RÉFÉRENCE ARTICLE CIBLÉE
    # =========================================================================
    reference = fields.Char(
        string='Référence article',
        index=True,
        help='Référence article exacte chez le fabricant (ex: 062525)\n'
             'Laisser vide pour que la dérogation s\'applique à toute la famille/base'
    )
    # Lien calculé vers l'article Odoo si importé
    article_id = fields.Many2one(
        'qdv.tarif.article',
        string='Article QDV correspondant',
        compute='_compute_article_id',
        store=False,  # Non-stored : évite les recomputes en cascade lors des transactions
        help='Article QDV trouvé avec ce code fab + référence'
    )
    article_matched = fields.Boolean(
        string='Article trouvé',
        compute='_compute_article_id',
        store=False,  # Non-stored
    )
    article_unit_price = fields.Float(
        string='Prix tarif article (€)',
        digits=(12, 4),
        help='Prix tarif catalogue de l\'article (copié depuis qdv.tarif.article)'
    )
    article_designation = fields.Char(
        string='Désignation article',
        help='Désignation de l\'article (copiée depuis qdv.tarif.article)'
    )

    # =========================================================================
    # REMISE OU PRIX NET (l'un calcule l'autre)
    # =========================================================================
    price_mode = fields.Selection([
        ('rebate', 'Remise %'),
        ('net_price', 'Prix net €'),
    ], string='Mode tarification', default='rebate', required=True,
       help='Choisir comment définir la dérogation: par remise % ou par prix net')

    rebate_value = fields.Float(
        string='Remise dérogatoire (%)',
        digits=(5, 2),
        help='Remise en % à appliquer sur le prix tarif catalogue'
    )
    net_price_override = fields.Float(
        string='Prix net dérogatoire (€)',
        digits=(12, 4),
        help='Prix net négocié — calcule automatiquement la remise équivalente'
    )
    # Champs calculés l'un depuis l'autre
    computed_rebate = fields.Float(
        string='Remise équivalente (%)',
        compute='_compute_cross_values',
        digits=(5, 2),
        store=False,  # Non-stored : calculé à la volée
        help='Remise calculée depuis le prix net et le prix tarif'
    )
    computed_net_price = fields.Float(
        string='Prix net calculé (€)',
        compute='_compute_cross_values',
        digits=(12, 4),
        store=False,  # Non-stored : calculé à la volée
        help='Prix net calculé depuis la remise et le prix tarif'
    )
    # Valeur effective utilisée
    effective_rebate = fields.Float(
        string='Remise effective (%)',
        compute='_compute_effective',
        store=True,
        digits=(5, 2)
    )
    effective_net_price = fields.Float(
        string='Prix net effectif (€)',
        compute='_compute_effective',
        store=True,
        digits=(12, 4)
    )

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('manufacturer_code')
    def _compute_base_id(self):
        for rec in self:
            if rec.manufacturer_code:
                try:
                    base = self.env['qdv.tarif.base'].search(
                        [('manufacturer_code', '=', rec.manufacturer_code)], limit=1
                    )
                    rec.base_id = base
                except Exception:
                    rec.base_id = False
            else:
                rec.base_id = False

    @api.depends('manufacturer_code', 'reference')
    def _compute_article_id(self):
        for rec in self:
            if rec.manufacturer_code and rec.reference:
                try:
                    article = self.env['qdv.tarif.article'].search([
                        ('manufacturer_code', '=', rec.manufacturer_code),
                        ('reference', '=', rec.reference),
                    ], limit=1)
                    rec.article_id = article
                    rec.article_matched = bool(article)
                    if article:
                        rec.article_unit_price = article.unit_price or 0.0
                        rec.article_designation = article.designation or ''
                except Exception:
                    rec.article_id = False
                    rec.article_matched = False
            else:
                rec.article_id = False
                rec.article_matched = False

    @api.depends('price_mode', 'rebate_value', 'net_price_override', 'article_unit_price')
    def _compute_cross_values(self):
        for rec in self:
            tarif = rec.article_unit_price or 0.0
            if rec.price_mode == 'rebate':
                # Prix net depuis remise
                rebate = rec.rebate_value or 0.0
                rec.computed_net_price = tarif * (1.0 - rebate / 100.0) if tarif else 0.0
                rec.computed_rebate = rebate
            else:
                # Remise depuis prix net
                net = rec.net_price_override or 0.0
                if tarif and net <= tarif:
                    rec.computed_rebate = (1.0 - net / tarif) * 100.0
                elif tarif and net > tarif:
                    rec.computed_rebate = 0.0  # prix net > tarif = pas de remise
                else:
                    rec.computed_rebate = 0.0
                rec.computed_net_price = net

    @api.depends('price_mode', 'rebate_value', 'net_price_override', 'article_id')
    def _compute_effective(self):
        """
        Calcule les valeurs effectives directement depuis les sources
        (sans passer par computed_rebate/computed_net_price non-stored).
        effective_rebate et effective_net_price sont stored pour être utilisés
        dans les exports QDV sans déclencher de recompute en cascade.
        """
        for rec in self:
            # Récupérer prix tarif sans déclencher de compute
            tarif = 0.0
            if rec.article_id:
                try:
                    tarif = rec.article_id.unit_price or 0.0
                except Exception:
                    pass

            if rec.price_mode == 'rebate':
                rebate = rec.rebate_value or 0.0
                rec.effective_rebate = rebate
                rec.effective_net_price = tarif * (1.0 - rebate / 100.0) if tarif else 0.0
            else:
                net = rec.net_price_override or 0.0
                rec.effective_net_price = net
                if tarif and tarif > 0 and net <= tarif:
                    rec.effective_rebate = (1.0 - net / tarif) * 100.0
                else:
                    rec.effective_rebate = 0.0

    # =========================================================================
    # ONCHANGE (cross-calcul immédiat dans le formulaire)
    # =========================================================================
    @api.onchange('rebate_value', 'net_price_override', 'price_mode', 'article_unit_price')
    def _onchange_prices(self):
        tarif = self.article_unit_price or 0.0
        if self.price_mode == 'rebate' and self.rebate_value and tarif:
            self.net_price_override = tarif * (1.0 - self.rebate_value / 100.0)
        elif self.price_mode == 'net_price' and self.net_price_override and tarif:
            if tarif > 0:
                self.rebate_value = (1.0 - self.net_price_override / tarif) * 100.0

    # =========================================================================
    # CONTRAINTE UNICITÉ
    # =========================================================================
    _sql_constraints = [
        ('unique_derog_code_fab_ref',
         'UNIQUE(derogation_code, manufacturer_code, reference)',
         'Ce code dérogation existe déjà pour ce fabricant et cette référence.'),
    ]

    @api.constrains('rebate_value')
    def _check_rebate(self):
        for rec in self:
            if rec.price_mode == 'rebate' and rec.rebate_value < 0:
                raise ValidationError(_("La remise ne peut pas être négative."))

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_apply_to_article(self):
        """Applique cette dérogation à l'article correspondant"""
        self.ensure_one()
        if not self.article_id:
            raise UserError(_("Aucun article QDV trouvé pour %s / %s") % (
                self.manufacturer_code, self.reference or '(sans référence)'))
        self.article_id.write({
            'derogation_id': self.id,
            'rebate_code': self.derogation_code,
            'rebate_value': self.effective_rebate,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dérogation appliquée'),
                'message': _('%s → %.2f%% (prix net %.4f€)') % (
                    self.article_id.reference,
                    self.effective_rebate,
                    self.effective_net_price,
                ),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_article(self):
        self.ensure_one()
        if not self.article_id:
            raise UserError(_("Aucun article trouvé."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.tarif.article',
            'res_id': self.article_id.id,
            'view_mode': 'form',
        }
