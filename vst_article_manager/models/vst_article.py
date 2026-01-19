# -*- coding: utf-8 -*-

import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

_logger = logging.getLogger(__name__)


class VstArticle(models.Model):
    _name = 'vst.article'
    _description = 'Article VST'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'code_article'

    # ===========================
    # CHAMPS PRINCIPAUX
    # ===========================
    
    code_article = fields.Char(
        string='Code Article',
        required=True,
        index=True,
        tracking=True,
        help='Code article VST unique'
    )
    
    designation = fields.Char(
        string='Désignation',
        tracking=True
    )
    
    designation_majuscule = fields.Char(
        string='Désignation (Majuscule)',
        help='Désignation en majuscules'
    )
    
    code_alpha = fields.Char(
        string='Code Alpha',
        index=True
    )
    
    display_name = fields.Char(
        string='Nom affiché',
        compute='_compute_display_name',
        store=True
    )

    # ===========================
    # INFORMATIONS FABRICANT
    # ===========================
    
    code_fabricant = fields.Char(
        string='Code Fabricant',
        index=True
    )
    
    nom_fabricant = fields.Char(
        string='Nom Fabricant',
        tracking=True
    )
    
    reference_fabricant = fields.Char(
        string='Référence Fabricant',
        index=True
    )

    # ===========================
    # PRIX
    # ===========================
    
    prix_achat_adherent = fields.Float(
        string='Prix Achat Adhérent',
        digits='Product Price',
        tracking=True,
        help='Prix d\'achat pour les adhérents VST'
    )
    
    prix_public_ht = fields.Float(
        string='Prix Public HT',
        digits='Product Price',
        tracking=True
    )
    
    prix_public_ttc = fields.Float(
        string='Prix Public TTC',
        digits='Product Price'
    )
    
    ecotaxe_ht = fields.Float(
        string='Écotaxe HT',
        digits='Product Price'
    )
    
    ecotaxe_ttc = fields.Float(
        string='Écotaxe TTC',
        digits='Product Price'
    )
    
    # Remise calculée
    remise = fields.Float(
        string='Remise (%)',
        compute='_compute_remise',
        store=True,
        digits=(5, 2)
    )

    # ===========================
    # FAMILLE / CLASSIFICATION
    # ===========================
    
    famille_code = fields.Char(
        string='Code Famille',
        help='Code hiérarchique de la famille'
    )
    
    nouvelle_famille_code = fields.Char(
        string='Code Nouvelle Famille',
        help='Nouveau code hiérarchique de la famille'
    )
    
    famille_id = fields.Many2one(
        'vst.famille',
        string='Famille',
        index=True,
        ondelete='set null'
    )
    
    source = fields.Char(
        string='Source',
        default='VST',
        readonly=True
    )
    
    libelle_activite = fields.Char(string='Libellé Activité')
    libelle_marque = fields.Char(string='Libellé Marque')
    libelle_famille = fields.Char(string='Libellé Famille')
    libelle_sous_famille = fields.Char(string='Libellé Sous-Famille')

    # ===========================
    # AUTRES INFORMATIONS
    # ===========================
    
    date_dernier_prix = fields.Date(
        string='Date Dernier Prix',
        tracking=True
    )
    
    unite = fields.Char(
        string='Unité',
        help='Unité de mesure (U, M, KG, etc.)'
    )
    
    type_article = fields.Selection([
        ('DIV', 'Divers'),
        ('ART', 'Article'),
        ('KIT', 'Kit'),
        ('LOV', 'LOV'),
    ], string='Type Article')

    # ===========================
    # GESTION ODOO
    # ===========================
    
    product_id = fields.Many2one(
        'product.product',
        string='Produit Odoo',
        ondelete='set null',
        help='Produit Odoo lié à cet article VST'
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    is_deleted = fields.Boolean(
        string='Supprimé du catalogue',
        default=False,
        help='Indique que cet article n\'est plus présent dans le catalogue VST'
    )
    
    date_suppression = fields.Datetime(
        string='Date de suppression',
        help='Date à laquelle l\'article a été détecté comme supprimé du catalogue'
    )
    
    date_import = fields.Datetime(
        string='Date d\'import',
        default=fields.Datetime.now
    )
    
    date_derniere_maj = fields.Datetime(
        string='Dernière mise à jour',
        default=fields.Datetime.now
    )

    # Historique des prix
    price_history_ids = fields.One2many(
        'vst.price.history',
        'article_id',
        string='Historique des prix'
    )
    
    price_history_count = fields.Integer(
        string='Historique',
        compute='_compute_price_history_count'
    )

    # ===========================
    # SQL CONSTRAINTS
    # ===========================
    
    _sql_constraints = [
        ('code_article_unique', 'UNIQUE(code_article)', 
         'Le code article doit être unique !'),
    ]

    # ===========================
    # COMPUTE METHODS
    # ===========================

    @api.depends('code_article', 'designation')
    def _compute_display_name(self):
        for article in self:
            if article.designation:
                article.display_name = f"[{article.code_article}] {article.designation}"
            else:
                article.display_name = article.code_article

    @api.depends('prix_public_ht', 'prix_achat_adherent')
    def _compute_remise(self):
        for article in self:
            if article.prix_public_ht and article.prix_public_ht > 0:
                article.remise = ((article.prix_public_ht - article.prix_achat_adherent) / article.prix_public_ht) * 100
            else:
                article.remise = 0.0

    def _compute_price_history_count(self):
        for article in self:
            article.price_history_count = len(article.price_history_ids)

    # ===========================
    # BUSINESS METHODS
    # ===========================

    @api.model
    def parse_date(self, date_str):
        """Parse une date au format jjmmaaaa"""
        if not date_str or len(date_str) != 8:
            return False
        try:
            return datetime.strptime(date_str, '%d%m%Y').date()
        except ValueError:
            return False

    def action_create_product(self):
        """
        Crée ou lie un produit Odoo à partir de l'article VST
        Recherche d'abord par référence fabricant pour éviter les doublons
        """
        self.ensure_one()
        
        # Vérifier si le produit lié existe toujours
        if self.product_id and not self.product_id.exists():
            self.write({'product_id': False})
        
        if self.product_id:
            raise UserError(_('Un produit Odoo est déjà lié à cet article.'))
        
        if not self.reference_fabricant:
            raise UserError(_('L\'article n\'a pas de référence fabricant. Impossible de créer le produit.'))
        
        config = self.env['vst.config'].get_config()
        supplier = config.supplier_id
        supplier_delay = config.supplier_delay or 1
        
        Product = self.env['product.product']
        SupplierInfo = self.env['product.supplierinfo']
        
        # Rechercher un produit existant par référence fabricant
        existing_product = Product.search([
            ('default_code', '=', self.reference_fabricant)
        ], limit=1)
        
        if existing_product:
            product = existing_product
            
            if supplier:
                existing_supplier = SupplierInfo.search([
                    ('product_tmpl_id', '=', product.product_tmpl_id.id),
                    ('partner_id', '=', supplier.id)
                ], limit=1)
                
                if existing_supplier:
                    existing_supplier.write({
                        'price': self.prix_achat_adherent or 0.0,
                        'product_code': self.code_article,
                        'product_name': self.designation,
                    })
                else:
                    SupplierInfo.create({
                        'partner_id': supplier.id,
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'price': self.prix_achat_adherent or 0.0,
                        'delay': supplier_delay,
                        'product_code': self.code_article,
                        'product_name': self.designation,
                    })
            
            self.write({'product_id': product.id})
            self.message_post(
                body=_('Produit existant trouvé et lié: [%s] %s. VST ajouté comme fournisseur.') % (
                    product.default_code, product.name
                )
            )
            
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.product',
                'res_id': product.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Créer un nouveau produit
        product_name = self.designation or f"[{self.nom_fabricant}] {self.reference_fabricant}"
        
        product_vals = {
            'name': product_name,
            'default_code': self.reference_fabricant,
            'list_price': self.prix_public_ht or 0.0,
            'standard_price': self.prix_achat_adherent or 0.0,
            'type': 'product',
        }
        
        product = Product.create(product_vals)
        
        if supplier:
            SupplierInfo.create({
                'partner_id': supplier.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'price': self.prix_achat_adherent or 0.0,
                'delay': supplier_delay,
                'product_code': self.code_article,
                'product_name': self.designation,
            })
        
        self.write({'product_id': product.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': product.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_products_batch(self):
        """Crée les produits Odoo pour plusieurs articles VST sélectionnés"""
        created = 0
        linked = 0
        errors = []
        
        config = self.env['vst.config'].get_config()
        supplier = config.supplier_id
        supplier_delay = config.supplier_delay or 1
        
        Product = self.env['product.product']
        SupplierInfo = self.env['product.supplierinfo']
        
        for article in self:
            try:
                if article.product_id and article.product_id.exists():
                    continue
                
                if article.product_id and not article.product_id.exists():
                    article.write({'product_id': False})
                
                if not article.reference_fabricant:
                    errors.append(f"[{article.code_article}] Pas de référence fabricant")
                    continue
                
                # Rechercher produit existant
                existing_product = Product.search([
                    ('default_code', '=', article.reference_fabricant)
                ], limit=1)
                
                if existing_product:
                    product = existing_product
                    linked += 1
                else:
                    product_name = article.designation or f"[{article.nom_fabricant}] {article.reference_fabricant}"
                    product = Product.create({
                        'name': product_name,
                        'default_code': article.reference_fabricant,
                        'list_price': article.prix_public_ht or 0.0,
                        'standard_price': article.prix_achat_adherent or 0.0,
                        'type': 'product',
                    })
                    created += 1
                
                # Ajouter fournisseur
                if supplier:
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
                
            except Exception as e:
                errors.append(f"[{article.code_article}] {str(e)}")
        
        message = _('Traitement terminé:\n- %d produits créés\n- %d produits liés\n- %d erreurs') % (created, linked, len(errors))
        if errors:
            message += '\n\nErreurs:\n' + '\n'.join(errors[:10])
            if len(errors) > 10:
                message += f'\n... et {len(errors) - 10} autres erreurs'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Création de produits'),
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }

    def action_view_price_history(self):
        """Affiche l'historique des prix"""
        self.ensure_one()
        return {
            'name': _('Historique des prix - %s') % self.code_article,
            'type': 'ir.actions.act_window',
            'res_model': 'vst.price.history',
            'view_mode': 'list,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_restore_article(self):
        """Restaure un article marqué comme supprimé"""
        self.ensure_one()
        self.write({
            'is_deleted': False,
            'date_suppression': False,
            'active': True,
        })
        return True

    def action_unlink_product(self):
        """Dissocie le produit Odoo de cet article VST"""
        self.ensure_one()
        if self.product_id:
            product_name = self.product_id.display_name if self.product_id.exists() else "Produit supprimé"
            self.message_post(body=_('Produit Odoo dissocié: %s') % product_name)
        self.write({'product_id': False})
        return True

    def action_open_product(self):
        """Ouvre le produit Odoo lié"""
        self.ensure_one()
        if not self.product_id:
            raise UserError(_('Aucun produit Odoo n\'est lié à cet article.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def _cron_check_products(self):
        """Cron pour vérifier et nettoyer les liens vers des produits supprimés"""
        articles = self.search([('product_id', '!=', False)])
        count = 0
        for article in articles:
            if not article.product_id.exists():
                article.write({'product_id': False})
                count += 1
        if count:
            _logger.info("VST: %d articles dissociés de produits supprimés", count)
