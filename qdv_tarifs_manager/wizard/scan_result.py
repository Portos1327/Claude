# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Wizard résultat scan + Wizard lien produit
"""
from odoo import models, fields, _


class QdvTarifScanResult(models.TransientModel):
    """Affiche le résultat du scan d'une base .qdb"""
    _name = 'qdv.tarif.scan.result'
    _description = 'Résultat Scan QDB'

    base_id = fields.Many2one('qdv.tarif.base', string='Base scannée', readonly=True)
    content = fields.Text(string='Informations', readonly=True)


class QdvTarifLinkWizard(models.TransientModel):
    """Lie un article QDV à un produit Odoo existant"""
    _name = 'qdv.tarif.link.wizard'
    _description = 'Lier article QDV à produit Odoo'

    article_id = fields.Many2one('qdv.tarif.article', string='Article QDV', readonly=True)
    product_id = fields.Many2one(
        'product.template',
        string='Produit Odoo',
        required=True,
        help='Sélectionnez le produit Odoo à lier à cet article QDV'
    )

    def action_confirm_link(self):
        self.ensure_one()
        self.article_id.product_id = self.product_id.id
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Lien créé'),
                'message': _("Article '%s' lié au produit '%s'") % (
                    self.article_id.reference, self.product_id.name),
                'type': 'success',
                'sticky': False,
            }
        }
