# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Articles importés depuis les bases QDV
Enrichi avec arborescence complète des familles et dérogations par référence
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class QdvTarifArticle(models.Model):
    _name = 'qdv.tarif.article'
    _description = 'Article QDV Tarif Fournisseur'
    _order = 'manufacturer_code, reference'

    # =========================================================================
    # LIEN BASE ET PRODUIT ODOO
    # =========================================================================
    base_id = fields.Many2one(
        'qdv.tarif.base', string='Base Fabricant',
        required=True, ondelete='cascade', index=True
    )
    manufacturer_code = fields.Char(
        string='Code Fabricant', related='base_id.manufacturer_code', store=True, index=True
    )
    manufacturer_name = fields.Char(
        string='Fabricant', related='base_id.manufacturer_name', store=True
    )
    product_id = fields.Many2one(
        'product.template', string='Produit Odoo', ondelete='set null',
        help='Lien vers le produit Odoo correspondant'
    )
    product_linked = fields.Boolean(
        string='Lié Odoo', compute='_compute_product_linked', store=True
    )

    # =========================================================================
    # DONNÉES ARTICLE (lecture seule — source .qdb)
    # =========================================================================
    reference = fields.Char(string='Référence', required=True, index=True)
    designation = fields.Char(string='Désignation')
    unit_price = fields.Float(
        string='Prix tarif (€)', digits=(12, 4),
        help='Prix catalogue fabricant — jamais modifiable'
    )
    unit = fields.Char(string='Unité', default='U')

    # =========================================================================
    # FAMILLE — codes bruts depuis .qdb
    # =========================================================================
    family_code = fields.Char(
        string='Code famille complet',
        index=True,
        help='Code famille QDV complet (ex: 449_4_46_461_4610_46101)'
    )
    # Lien vers la fiche famille
    family_id = fields.Many2one(
        'qdv.tarif.family',
        string='Famille',
        compute='_compute_family_id',
        store=True,
        ondelete='set null'
    )
    # Niveaux de famille aplatis (pour filtres et regroupements)
    fam_level0 = fields.Char(
        string='Marque', related='family_id.level0_label', store=True,
        help='Niveau 0 — généralement le nom du fabricant'
    )
    fam_level1 = fields.Char(
        string='Famille', related='family_id.level1_label', store=True
    )
    fam_level2 = fields.Char(
        string='Sous-famille', related='family_id.level2_label', store=True
    )
    fam_level3 = fields.Char(
        string='Catégorie', related='family_id.level3_label', store=True
    )
    fam_level4 = fields.Char(
        string='Sous-catégorie', related='family_id.level4_label', store=True
    )
    family_breadcrumb = fields.Char(
        string='Arborescence famille', related='family_id.breadcrumb', store=True,
        help='Ex: ACOME / Systèmes / Câblage cuivre / Cat6'
    )

    # =========================================================================
    # REMISE FAMILLE
    # =========================================================================
    rebate_code = fields.Char(string='Code remise')
    rebate_value = fields.Float(string='Remise famille (%)', digits=(5, 2))

    # =========================================================================
    # DÉROGATION PAR RÉFÉRENCE
    # =========================================================================
    derogation_id = fields.Many2one(
        'qdv.tarif.derogation',
        string='Dérogation',
        ondelete='set null',
        domain="[('manufacturer_code', '=', manufacturer_code), ('active', '=', True)]",
        help='Dérogation spécifique à cet article (remise ou prix net négocié)'
    )
    has_derogation = fields.Boolean(
        string='Dérogation active', compute='_compute_has_derogation', store=True
    )
    derogation_rebate = fields.Float(
        string='Remise dérogatoire (%)',
        related='derogation_id.effective_rebate',
        store=True, digits=(5, 2)
    )
    derogation_net_price = fields.Float(
        string='Prix net dérogatoire (€)',
        related='derogation_id.effective_net_price',
        store=True, digits=(12, 4)
    )

    # =========================================================================
    # PRIX NET CALCULÉ
    # =========================================================================
    net_price = fields.Float(
        string='Prix net (€)',
        compute='_compute_net_price',
        store=True, digits=(12, 4),
        help='Dérogation si active, sinon remise famille × prix tarif'
    )
    effective_rebate = fields.Float(
        string='Remise effective (%)',
        compute='_compute_net_price',
        store=True, digits=(5, 2)
    )

    # =========================================================================
    # INFOS COMPLÉMENTAIRES
    # =========================================================================
    import_date = fields.Datetime(string='Date import', readonly=True)

    # =========================================================================
    # COMPUTED
    # =========================================================================
    @api.depends('product_id')
    def _compute_product_linked(self):
        for rec in self:
            rec.product_linked = bool(rec.product_id)

    @api.depends('derogation_id')
    def _compute_has_derogation(self):
        for rec in self:
            rec.has_derogation = bool(rec.derogation_id)

    @api.depends('family_code', 'base_id')
    def _compute_family_id(self):
        for rec in self:
            if rec.family_code and rec.base_id:
                fam = self.env['qdv.tarif.family'].search([
                    ('base_id', '=', rec.base_id.id),
                    ('family_code', '=', rec.family_code),
                ], limit=1)
                rec.family_id = fam
            else:
                rec.family_id = False

    @api.depends('unit_price', 'rebate_value',
                 'derogation_id', 'derogation_id.effective_rebate', 'derogation_id.effective_net_price',
                 'derogation_id.price_mode')
    def _compute_net_price(self):
        for rec in self:
            tarif = rec.unit_price or 0.0
            if rec.derogation_id:
                d = rec.derogation_id
                if d.price_mode == 'net_price':
                    rec.net_price = d.effective_net_price
                    rec.effective_rebate = d.effective_rebate
                else:
                    rebate = d.effective_rebate
                    rec.effective_rebate = rebate
                    rec.net_price = tarif * (1.0 - rebate / 100.0) if tarif else 0.0
            else:
                rebate = rec.rebate_value or 0.0
                rec.effective_rebate = rebate
                rec.net_price = tarif * (1.0 - rebate / 100.0) if tarif else tarif

    # =========================================================================
    # ACTIONS
    # =========================================================================
    def action_create_product(self):
        self.ensure_one()
        if self.product_id:
            raise UserError(_("Déjà lié au produit '%s'.") % self.product_id.name)
        product = self.env['product.template'].create({
            'name': self.designation or self.reference,
            'default_code': self.reference,
            'type': 'consu',
            'purchase_ok': True,
            'sale_ok': True,
            'list_price': self.net_price or self.unit_price or 0.0,
            'standard_price': self.net_price or 0.0,
        })
        self.product_id = product.id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': product.id,
            'view_mode': 'form',
        }

    def action_link_product(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.tarif.link.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_article_id': self.id},
        }

    def action_open_product(self):
        self.ensure_one()
        if not self.product_id:
            raise UserError(_("Aucun produit Odoo lié."))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': self.product_id.id,
            'view_mode': 'form',
        }

    def action_scan_derogations(self):
        """Lance le wizard de scan des dérogations pour cet article"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Scan dérogations — %s / %s') % (self.manufacturer_code, self.reference),
            'res_model': 'qdv.tarif.scan.derogation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_article_id': self.id,
                'default_manufacturer_code': self.manufacturer_code,
                'default_reference': self.reference,
            },
        }

    def action_remove_derogation(self):
        self.ensure_one()
        if not self.derogation_id:
            raise UserError(_("Pas de dérogation assignée."))
        old = self.derogation_id.derogation_code
        self.write({'derogation_id': False})
        # Remettre la remise famille
        rebate = self.env['qdv.tarif.rebate'].search([
            ('base_id', '=', self.base_id.id),
            ('rebate_code', '=', self.rebate_code),
        ], limit=1)
        if rebate:
            self.write({'rebate_value': rebate.effective_rebate})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dérogation retirée'),
                'message': _("Dérogation '%s' retirée.") % old,
                'type': 'warning', 'sticky': False,
            }
        }
