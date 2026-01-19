# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CreateProductsWizard(models.TransientModel):
    _name = 'create.products.vst.wizard'
    _description = 'Assistant de création de produits Odoo'

    article_ids = fields.Many2many('vst.article', string='Articles à traiter')
    
    mode = fields.Selection([
        ('selected', 'Articles sélectionnés uniquement'),
        ('all_without', 'Tous les articles sans produit Odoo'),
    ], string='Mode', default='selected', required=True)
    
    skip_without_ref = fields.Boolean(
        string='Ignorer les articles sans référence fabricant',
        default=True
    )
    
    # Résultats
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('done', 'Terminé')
    ], default='draft')
    
    products_created = fields.Integer(string='Produits créés', readonly=True)
    products_linked = fields.Integer(string='Produits liés (existants)', readonly=True)
    errors_count = fields.Integer(string='Erreurs', readonly=True)
    log_message = fields.Text(string='Log', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if self.env.context.get('active_ids'):
            res['article_ids'] = [(6, 0, self.env.context.get('active_ids'))]
        return res

    def action_create_products(self):
        """Lance la création des produits"""
        self.ensure_one()
        
        # Déterminer les articles à traiter
        if self.mode == 'all_without':
            articles = self.env['vst.article'].search([
                ('product_id', '=', False),
                ('active', '=', True),
                ('is_deleted', '=', False),
            ])
        else:
            articles = self.article_ids.filtered(lambda a: not a.product_id or not a.product_id.exists())
        
        if not articles:
            raise UserError(_('Aucun article à traiter (tous ont déjà un produit Odoo lié).'))
        
        config = self.env['vst.config'].get_config()
        supplier = config.supplier_id
        supplier_delay = config.supplier_delay or 1
        
        if not supplier:
            raise UserError(_(
                'Aucun fournisseur VST configuré.\n\n'
                'Allez dans VST > Configuration > Configuration VST\n'
                'et sélectionnez un fournisseur.'
            ))
        
        Product = self.env['product.product']
        SupplierInfo = self.env['product.supplierinfo']
        
        created = 0
        linked = 0
        errors = []
        
        for article in articles:
            try:
                # Vérifier si le produit lié existe toujours
                if article.product_id and not article.product_id.exists():
                    article.write({'product_id': False})
                
                if article.product_id:
                    continue
                
                if self.skip_without_ref and not article.reference_fabricant:
                    errors.append(f"[{article.code_article}] Pas de référence fabricant")
                    continue
                
                ref_to_use = article.reference_fabricant or article.code_article
                
                # Rechercher produit existant par référence
                existing_product = Product.search([
                    ('default_code', '=', ref_to_use)
                ], limit=1)
                
                if existing_product:
                    product = existing_product
                    
                    # Ajouter/mettre à jour le fournisseur
                    existing_supplier = SupplierInfo.search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('partner_id', '=', supplier.id)
                    ], limit=1)
                    
                    if existing_supplier:
                        existing_supplier.write({
                            'price': article.prix_achat_adherent or 0.0,
                            'product_code': article.code_article,
                            'product_name': article.designation,
                        })
                    else:
                        SupplierInfo.create({
                            'partner_id': supplier.id,
                            'product_tmpl_id': product.product_tmpl_id.id,
                            'price': article.prix_achat_adherent or 0.0,
                            'delay': supplier_delay,
                            'product_code': article.code_article,
                            'product_name': article.designation,
                        })
                    
                    article.write({'product_id': product.id})
                    linked += 1
                    
                else:
                    # Créer nouveau produit
                    product_name = article.designation or f"[{article.nom_fabricant}] {ref_to_use}"
                    
                    product = Product.create({
                        'name': product_name,
                        'default_code': ref_to_use,
                        'list_price': article.prix_public_ht or 0.0,
                        'standard_price': article.prix_achat_adherent or 0.0,
                        'type': 'product',
                    })
                    
                    # Ajouter fournisseur
                    SupplierInfo.create({
                        'partner_id': supplier.id,
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'price': article.prix_achat_adherent or 0.0,
                        'delay': supplier_delay,
                        'product_code': article.code_article,
                        'product_name': article.designation,
                    })
                    
                    article.write({'product_id': product.id})
                    created += 1
                    
            except Exception as e:
                errors.append(f"[{article.code_article}] {str(e)}")
        
        # Construire le log
        log_lines = [
            "=" * 50,
            "CRÉATION DE PRODUITS ODOO",
            "=" * 50,
            "",
            f"Produits créés: {created}",
            f"Produits liés (existants): {linked}",
            f"Erreurs: {len(errors)}",
            "",
        ]
        
        if errors:
            log_lines.append("ERREURS:")
            for err in errors[:30]:
                log_lines.append(f"  - {err}")
            if len(errors) > 30:
                log_lines.append(f"  ... et {len(errors) - 30} autres erreurs")
        
        self.write({
            'state': 'done',
            'products_created': created,
            'products_linked': linked,
            'errors_count': len(errors),
            'log_message': '\n'.join(log_lines),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'create.products.vst.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back(self):
        """Retour à l'étape de configuration"""
        self.write({
            'state': 'draft',
            'products_created': 0,
            'products_linked': 0,
            'errors_count': 0,
            'log_message': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'create.products.vst.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
