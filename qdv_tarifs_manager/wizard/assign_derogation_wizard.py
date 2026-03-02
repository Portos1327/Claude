# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Wizard assignation de dérogation à un article
Permet de sélectionner une dérogation existante ou d'en créer une nouvelle à la volée
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class QdvTarifAssignDerogationWizard(models.TransientModel):
    _name = 'qdv.tarif.assign.derogation.wizard'
    _description = 'Assigner une dérogation à un article QDV'

    article_id = fields.Many2one(
        'qdv.tarif.article',
        string='Article',
        required=True,
        readonly=True,
        ondelete='cascade'
    )
    base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Base Fabricant',
        readonly=True
    )
    current_derogation_id = fields.Many2one(
        'qdv.tarif.derogation',
        string='Dérogation actuelle',
        readonly=True
    )

    # =========================================================================
    # CHOIX: sélectionner existante OU créer nouvelle
    # =========================================================================
    mode = fields.Selection([
        ('existing', 'Sélectionner une dérogation existante'),
        ('new', 'Créer une nouvelle dérogation'),
    ], string='Mode', default='existing', required=True)

    # Mode existante
    derogation_id = fields.Many2one(
        'qdv.tarif.derogation',
        string='Dérogation',
        domain="[('base_id', '=', base_id), ('active', '=', True)]",
        help='Choisir parmi les dérogations déjà créées pour ce fabricant'
    )

    # Mode création nouvelle
    new_code = fields.Char(
        string='Code dérogation',
        help='Ex: DEROG_001, PROMO_2026, CHANTIER_MAIRIE...'
    )
    new_label = fields.Char(
        string='Libellé',
        help='Description de la dérogation'
    )
    new_rebate = fields.Float(
        string='Taux de remise (%)',
        digits=(5, 2),
        help='Taux dérogatoire à appliquer'
    )
    new_comment = fields.Text(
        string='Motif / Notes'
    )

    # Aperçu prix
    article_reference = fields.Char(
        related='article_id.reference', string='Référence', readonly=True
    )
    article_unit_price = fields.Float(
        related='article_id.unit_price', string='Prix tarif (€)', readonly=True
    )
    preview_net_price = fields.Float(
        string='Prix net prévisuel (€)',
        compute='_compute_preview',
        digits=(12, 4),
        help='Prix net calculé avec la dérogation sélectionnée'
    )
    preview_rebate = fields.Float(
        string='Remise prévisuelle (%)',
        compute='_compute_preview',
        digits=(5, 2)
    )

    @api.depends('mode', 'derogation_id', 'new_rebate', 'article_id.unit_price')
    def _compute_preview(self):
        for rec in self:
            price = rec.article_id.unit_price or 0.0
            if rec.mode == 'existing' and rec.derogation_id:
                rebate = rec.derogation_id.rebate_value
            elif rec.mode == 'new':
                rebate = rec.new_rebate
            else:
                rebate = rec.article_id.rebate_value or 0.0
            rec.preview_rebate = rebate
            rec.preview_net_price = price * (1.0 - rebate / 100.0) if price else 0.0

    def action_confirm(self):
        """Confirme l'assignation de la dérogation à l'article"""
        self.ensure_one()

        if self.mode == 'existing':
            if not self.derogation_id:
                raise UserError(_("Veuillez sélectionner une dérogation."))
            derogation = self.derogation_id

        else:  # mode == 'new'
            if not self.new_code:
                raise UserError(_("Le code dérogation est obligatoire."))
            if not self.new_label:
                raise UserError(_("Le libellé est obligatoire."))
            if self.new_rebate <= 0:
                raise UserError(_("Le taux de remise doit être supérieur à 0."))

            # Vérifier que le code n'existe pas déjà pour ce fabricant
            existing = self.env['qdv.tarif.derogation'].search([
                ('base_id', '=', self.base_id.id),
                ('derogation_code', '=', self.new_code),
            ], limit=1)
            if existing:
                raise UserError(_(
                    "Le code dérogation '%s' existe déjà pour ce fabricant.\n"
                    "Utilisez le mode 'Sélectionner existante' ou choisissez un autre code."
                ) % self.new_code)

            derogation = self.env['qdv.tarif.derogation'].create({
                'base_id': self.base_id.id,
                'derogation_code': self.new_code,
                'derogation_label': self.new_label,
                'rebate_value': self.new_rebate,
                'comment': self.new_comment or '',
                'active': True,
            })

        # Assigner la dérogation à l'article
        self.article_id.write({
            'derogation_id': derogation.id,
            'rebate_code': derogation.derogation_code,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dérogation assignée'),
                'message': _("Dérogation '%s' (%.2f%%) assignée à la référence '%s'") % (
                    derogation.derogation_code,
                    derogation.rebate_value,
                    self.article_id.reference,
                ),
                'type': 'success',
                'sticky': False,
            }
        }
