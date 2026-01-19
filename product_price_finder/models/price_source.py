# -*- coding: utf-8 -*-
"""
Price Source - Configuration des sources de prix
================================================

Ce modèle gère les différentes sources de prix (modules de tarifs)
disponibles dans le système avec AUTO-DÉTECTION des modules installés.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


# Configuration des providers connus avec leurs paramètres par défaut
KNOWN_PROVIDERS = {
    'rexel': {
        'name': 'Rexel',
        'model_name': 'rexel.article',
        'reference_field': 'reference_fabricant',
        'brand_field': 'fabricant_libelle',
        'price_field': 'prix_net',
        'price_base_field': 'prix_base',
        'discount_field': 'remise',
        'designation_field': 'designation',
        'unit_field': 'unite_mesure',
        'product_field': 'product_id',
        'sequence': 10,
    },
    'vst': {
        'name': 'VST',
        'model_name': 'vst.article',
        'reference_field': 'reference_fabricant',
        'brand_field': 'nom_fabricant',
        'price_field': 'prix_achat',
        'price_base_field': 'prix_public',
        'discount_field': False,
        'designation_field': 'designation',
        'unit_field': 'unite',
        'product_field': 'product_id',
        'sequence': 20,
    },
    'elen': {
        'name': 'ELEN Distribution',
        'model_name': 'elen.article',
        'reference_field': 'reference',
        'brand_field': 'marque',
        'price_field': 'prix',
        'price_base_field': 'prix_base',
        'discount_field': 'remise',
        'designation_field': 'designation',
        'unit_field': 'unite',
        'product_field': 'product_id',
        'sequence': 30,
    },
    'turquand': {
        'name': 'Turquand',
        'model_name': 'turquand.article',
        'reference_field': 'reference',
        'brand_field': 'marque',
        'price_field': 'prix',
        'price_base_field': False,
        'discount_field': False,
        'designation_field': 'designation',
        'unit_field': 'unite',
        'product_field': 'product_id',
        'sequence': 40,
    },
    'generic': {
        'name': 'Source générique',
        'model_name': '',
        'reference_field': 'reference',
        'brand_field': 'brand',
        'price_field': 'price',
        'price_base_field': 'price_base',
        'discount_field': 'discount',
        'designation_field': 'name',
        'unit_field': 'uom',
        'product_field': 'product_id',
        'sequence': 100,
    },
}


class PriceSource(models.Model):
    """
    Source de prix - représente un module de tarifs installé
    
    AUTO-DÉTECTION : Les sources sont créées automatiquement
    selon les modules installés dans Odoo.
    """
    _name = 'price.source'
    _description = 'Source de prix'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nom',
        required=True,
        help="Nom de la source de prix (ex: Rexel, VST, ELEN Distribution)"
    )
    
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help="Ordre de priorité lors de la recherche"
    )
    
    active = fields.Boolean(
        string='Actif',
        default=True
    )
    
    provider_type = fields.Selection(
        selection='_get_provider_types',
        string='Type de fournisseur',
        required=True,
        help="Type de module de tarifs - Le modèle Odoo sera rempli automatiquement"
    )
    
    model_name = fields.Char(
        string='Modèle Odoo',
        compute='_compute_model_name',
        store=True,
        readonly=False,
        help="Nom technique du modèle (auto-rempli selon le type)"
    )
    
    # Champs de correspondance (SIMPLIFIÉS - pas de code fabricant)
    reference_field = fields.Char(
        string='Champ référence fabricant',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant la référence fabricant"
    )
    
    brand_field = fields.Char(
        string='Champ marque/fabricant',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant la marque ou le nom du fabricant"
    )
    
    # Champs de prix
    price_field = fields.Char(
        string='Champ prix net',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant le prix net"
    )
    
    price_base_field = fields.Char(
        string='Champ prix de base',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant le prix de base (avant remise)"
    )
    
    discount_field = fields.Char(
        string='Champ remise',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant le pourcentage de remise"
    )
    
    # Champs supplémentaires
    designation_field = fields.Char(
        string='Champ désignation',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant la désignation de l'article"
    )
    
    unit_field = fields.Char(
        string='Champ unité',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ contenant l'unité de mesure"
    )
    
    # Relation avec produits
    product_field = fields.Char(
        string='Champ produit Odoo',
        compute='_compute_field_mappings',
        store=True,
        readonly=False,
        help="Champ Many2one vers product.product"
    )
    
    # Fournisseur associé (pour l'onglet Achats)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Fournisseur associé',
        domain="[('supplier_rank', '>', 0)]",
        help="Fournisseur à utiliser dans l'onglet Achats du produit"
    )
    
    # Statistiques
    article_count = fields.Integer(
        string='Nb articles',
        compute='_compute_article_count',
        store=False
    )
    
    match_count = fields.Integer(
        string='Correspondances',
        compute='_compute_match_count',
        store=False
    )
    
    is_installed = fields.Boolean(
        string='Module installé',
        compute='_compute_is_installed',
        store=False
    )
    
    notes = fields.Text(
        string='Notes',
        help="Notes de configuration ou remarques"
    )

    @api.model
    def _get_provider_types(self):
        """
        Retourne la liste des types de fournisseurs disponibles.
        DYNAMIQUE selon les modules installés dans Odoo.
        """
        types = []
        for key, config in KNOWN_PROVIDERS.items():
            model_name = config.get('model_name')
            # Vérifier si le modèle existe (module installé)
            if not model_name or model_name in self.env:
                label = config.get('name', key.title())
                if model_name and model_name in self.env:
                    # Module installé - ajouter une indication
                    label = f"{label} ✓"
                types.append((key, label))
        return types

    @api.depends('provider_type')
    def _compute_model_name(self):
        """Auto-remplit le modèle Odoo selon le type de fournisseur"""
        for source in self:
            if source.provider_type and source.provider_type in KNOWN_PROVIDERS:
                source.model_name = KNOWN_PROVIDERS[source.provider_type].get('model_name', '')
            elif not source.model_name:
                source.model_name = ''

    @api.depends('provider_type')
    def _compute_field_mappings(self):
        """Auto-remplit tous les champs de mapping selon le type de fournisseur"""
        for source in self:
            if source.provider_type and source.provider_type in KNOWN_PROVIDERS:
                config = KNOWN_PROVIDERS[source.provider_type]
                source.reference_field = config.get('reference_field', 'reference')
                source.brand_field = config.get('brand_field', 'brand')
                source.price_field = config.get('price_field', 'price')
                source.price_base_field = config.get('price_base_field', '')
                source.discount_field = config.get('discount_field', '')
                source.designation_field = config.get('designation_field', 'name')
                source.unit_field = config.get('unit_field', '')
                source.product_field = config.get('product_field', 'product_id')

    def _compute_is_installed(self):
        """Vérifie si le module correspondant est installé"""
        for source in self:
            source.is_installed = source.model_name and source.model_name in self.env

    def _compute_article_count(self):
        """Compte le nombre d'articles dans la source"""
        for source in self:
            if source.model_name and source.model_name in self.env:
                source.article_count = self.env[source.model_name].search_count([])
            else:
                source.article_count = 0

    def _compute_match_count(self):
        """Calcule le nombre de correspondances trouvées pour cette source"""
        PriceMatch = self.env['price.match']
        for source in self:
            source.match_count = PriceMatch.search_count([
                ('source_id', '=', source.id)
            ])

    def action_view_matches(self):
        """Ouvre la liste des correspondances pour cette source"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Correspondances - %s') % self.name,
            'res_model': 'price.match',
            'view_mode': 'list,form',
            'domain': [('source_id', '=', self.id)],
            'context': {'default_source_id': self.id},
        }

    def action_view_articles(self):
        """Ouvre la liste des articles de cette source"""
        self.ensure_one()
        if not self.model_name or self.model_name not in self.env:
            raise UserError(_("Le module %s n'est pas installé.") % self.model_name)
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Articles - %s') % self.name,
            'res_model': self.model_name,
            'view_mode': 'list,form',
        }

    def test_connection(self):
        """Teste la connexion à la source de prix."""
        self.ensure_one()
        
        if not self.model_name:
            raise UserError(_("Aucun modèle Odoo configuré."))
        
        if self.model_name not in self.env:
            raise UserError(_(
                "Le modèle '%s' n'existe pas dans Odoo.\n"
                "Vérifiez que le module correspondant est installé."
            ) % self.model_name)
        
        model = self.env[self.model_name]
        model_fields = list(model._fields.keys())
        
        # Vérifier les champs
        missing_fields = []
        if self.reference_field and self.reference_field not in model_fields:
            missing_fields.append(self.reference_field)
        if self.price_field and self.price_field not in model_fields:
            missing_fields.append(self.price_field)
        
        if missing_fields:
            raise UserError(_(
                "Les champs suivants n'existent pas dans '%s':\n%s\n\n"
                "Champs disponibles: %s"
            ) % (self.model_name, ', '.join(missing_fields), ', '.join(model_fields[:20])))
        
        count = model.search_count([])
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Connexion réussie'),
                'message': _("Source '%s' OK - %d articles disponibles.") % (self.name, count),
                'type': 'success',
                'sticky': False,
            }
        }

    def search_prices(self, reference, brand=None):
        """
        Recherche les prix dans cette source.
        
        SIMPLIFIÉ: Recherche par référence ET/OU marque uniquement.
        Pas de code fabricant (non pertinent pour la recherche).
        
        Args:
            reference: Référence fabricant à rechercher
            brand: Nom de la marque/fabricant (optionnel)
            
        Returns:
            Liste de dictionnaires avec les informations de prix
        """
        self.ensure_one()
        
        if not self.model_name or self.model_name not in self.env:
            _logger.warning(f"Modèle {self.model_name} non disponible pour {self.name}")
            return []
        
        model = self.env[self.model_name]
        results = []
        
        # Construire le domaine - RECHERCHE FLEXIBLE
        domain = []
        
        if reference and self.reference_field:
            # Recherche exacte d'abord, puis partielle
            domain.append((self.reference_field, '=ilike', reference))
        
        if brand and self.brand_field:
            domain.append((self.brand_field, 'ilike', brand))
        
        if not domain:
            return []
        
        try:
            # Recherche exacte
            articles = model.search(domain, limit=100)
            
            # Si pas de résultat, recherche partielle sur la référence
            if not articles and reference and self.reference_field:
                domain_partial = [(self.reference_field, 'ilike', reference)]
                if brand and self.brand_field:
                    domain_partial.append((self.brand_field, 'ilike', brand))
                articles = model.search(domain_partial, limit=100)
            
            for article in articles:
                result = {
                    'source_id': self.id,
                    'source_name': self.name,
                    'article_id': article.id,
                    'model_name': self.model_name,
                    'partner_id': self.partner_id.id if self.partner_id else False,
                    'partner_name': self.partner_id.name if self.partner_id else self.name,
                }
                
                # Récupérer les valeurs
                if self.reference_field and hasattr(article, self.reference_field):
                    result['reference'] = getattr(article, self.reference_field, '') or ''
                
                if self.designation_field and hasattr(article, self.designation_field):
                    result['designation'] = getattr(article, self.designation_field, '') or ''
                
                if self.brand_field and hasattr(article, self.brand_field):
                    result['brand'] = getattr(article, self.brand_field, '') or ''
                
                if self.price_field and hasattr(article, self.price_field):
                    result['price'] = getattr(article, self.price_field, 0.0) or 0.0
                
                if self.price_base_field and hasattr(article, self.price_base_field):
                    result['price_base'] = getattr(article, self.price_base_field, 0.0) or 0.0
                
                if self.discount_field and hasattr(article, self.discount_field):
                    result['discount'] = getattr(article, self.discount_field, 0.0) or 0.0
                
                if self.unit_field and hasattr(article, self.unit_field):
                    result['unit'] = getattr(article, self.unit_field, '') or ''
                
                # Vérifier si déjà lié à un produit
                if self.product_field and hasattr(article, self.product_field):
                    product = getattr(article, self.product_field)
                    result['linked_product_id'] = product.id if product else False
                else:
                    result['linked_product_id'] = False
                
                results.append(result)
                
        except Exception as e:
            _logger.error(f"Erreur recherche dans {self.name}: {e}")
        
        return results

    @api.model
    def search_all_sources(self, reference, brand=None):
        """
        Recherche les prix dans TOUTES les sources actives.
        """
        all_results = []
        sources = self.search([('active', '=', True)], order='sequence')
        
        for source in sources:
            if source.is_installed:
                results = source.search_prices(reference, brand)
                all_results.extend(results)
        
        return all_results

    @api.model
    def auto_detect_and_create_sources(self):
        """
        AUTO-DÉTECTION : Crée automatiquement les sources de prix
        pour tous les modules de tarifs installés dans Odoo.
        """
        created = []
        updated = []
        
        for provider_type, config in KNOWN_PROVIDERS.items():
            model_name = config.get('model_name')
            
            # Ignorer si pas de modèle défini ou modèle non installé
            if not model_name or model_name not in self.env:
                continue
            
            # Chercher si la source existe déjà
            existing = self.search([('provider_type', '=', provider_type)], limit=1)
            
            if existing:
                # Mettre à jour si nécessaire
                if not existing.active:
                    existing.active = True
                    updated.append(existing.name)
            else:
                # Créer la nouvelle source
                vals = {
                    'name': config.get('name', provider_type.title()),
                    'provider_type': provider_type,
                    'sequence': config.get('sequence', 50),
                }
                source = self.create(vals)
                created.append(source.name)
                _logger.info(f"Source auto-créée: {source.name}")
        
        # Message de retour
        messages = []
        if created:
            messages.append(_("Sources créées: %s") % ', '.join(created))
        if updated:
            messages.append(_("Sources réactivées: %s") % ', '.join(updated))
        
        if messages:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Détection automatique'),
                    'message': '\n'.join(messages),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aucun changement'),
                    'message': _("Toutes les sources sont déjà configurées ou aucun module de tarifs n'est installé."),
                    'type': 'warning',
                    'sticky': False,
                }
            }

    # Alias pour rétrocompatibilité
    create_default_sources = auto_detect_and_create_sources
