# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

_logger = logging.getLogger(__name__)


class UpdatePricesWizard(models.TransientModel):
    _name = 'update.prices.wizard'
    _description = 'Mise à jour des articles via API Rexel Cloud'

    # ========== MODE DE MISE À JOUR ==========
    update_mode = fields.Selection([
        ('all', 'Tous les articles'),
        ('selection', 'Articles sélectionnés'),
        ('filter', 'Avec filtres'),
    ], string='Articles à mettre à jour', default='all', required=True)
    
    # ========== FILTRES AVANCÉS (Many2one) ==========
    # Filtres par famille/hiérarchie (basé sur les libellés des articles directement)
    filter_famille_id = fields.Many2one(
        'rexel.product.family',
        string='Famille',
        domain=[('level', '=', 'famille')],
        help='Filtrer par famille de produits'
    )
    filter_sous_famille_id = fields.Many2one(
        'rexel.product.family',
        string='Sous-famille',
        domain="[('level', '=', 'sous_famille'), ('parent_id', '=', filter_famille_id)]",
        help='Filtrer par sous-famille'
    )
    filter_fonction_id = fields.Many2one(
        'rexel.product.family',
        string='Fonction',
        domain="[('level', '=', 'fonction'), ('parent_id', '=', filter_sous_famille_id)]",
        help='Filtrer par fonction'
    )
    
    # Filtre par fabricant (sélection dynamique)
    filter_fabricant = fields.Selection(
        selection='_get_fabricants_selection',
        string='Fabricant',
        help='Filtrer par fabricant'
    )
    
    # Filtres booléens (comme dans la recherche)
    filter_obsolete = fields.Selection([
        ('all', '-- Tous --'),
        ('yes', 'Articles obsolètes'),
        ('no', 'Articles actifs'),
    ], string='Statut',
       default='all',
       help='Filtrer les articles obsolètes ou actifs'
    )
    
    filter_with_product = fields.Selection([
        ('all', '-- Tous --'),
        ('yes', 'Avec produit Odoo'),
        ('no', 'Sans produit Odoo'),
    ], string='Produit Odoo',
       default='all',
       help='Filtrer les articles avec ou sans produit Odoo lié'
    )
    
    filter_selection_durable = fields.Selection([
        ('all', '-- Tous --'),
        ('yes', 'Sélection durable'),
        ('no', 'Non durable'),
    ], string='Sélection durable',
       default='all',
       help='Filtrer les articles de la sélection durable'
    )
    
    # Filtre par source d'import
    filter_import_source = fields.Selection([
        ('all', '-- Tous --'),
        ('excel', 'Import Excel'),
        ('api', 'Import API'),
    ], string='Source import',
       default='all',
       help='Filtrer par source d\'import (Excel ou API)'
    )
    
    # Filtres texte libre (recherche manuelle)
    filter_famille_text = fields.Char(
        string='Famille contient',
        help='Filtrer par nom de famille (recherche partielle)'
    )
    filter_fabricant_text = fields.Char(
        string='Fabricant contient',
        help='Filtrer par nom de fabricant (recherche partielle)'
    )
    filter_reference = fields.Char(
        string='Référence contient',
        help='Filtrer par référence fabricant (recherche partielle)'
    )
    filter_designation = fields.Char(
        string='Désignation contient',
        help='Filtrer par désignation (recherche partielle)'
    )
    
    @api.model
    def _get_fabricants_selection(self):
        """Retourne la liste des fabricants disponibles pour le filtre"""
        self.env.cr.execute("""
            SELECT DISTINCT fabricant_libelle 
            FROM rexel_article 
            WHERE fabricant_libelle IS NOT NULL 
            AND fabricant_libelle != ''
            ORDER BY fabricant_libelle
        """)
        fabricants = self.env.cr.fetchall()
        result = [('all', '-- Tous --')]
        result.extend([(f[0], f[0]) for f in fabricants if f[0]])
        return result
    
    @api.onchange('filter_famille_id')
    def _onchange_filter_famille(self):
        """Reset sous-famille et fonction quand famille change"""
        self.filter_sous_famille_id = False
        self.filter_fonction_id = False
    
    @api.onchange('filter_sous_famille_id')
    def _onchange_filter_sous_famille(self):
        """Reset fonction quand sous-famille change"""
        self.filter_fonction_id = False
    
    # ========== OPTIONS GÉNÉRALES ==========
    create_history = fields.Boolean(
        string='Créer historique des prix',
        default=True,
        help='Enregistre les changements de prix dans l\'historique'
    )
    
    update_products = fields.Boolean(
        string='Mettre à jour les produits Odoo',
        default=False,
        help='Met à jour aussi les prix des produits Odoo liés'
    )
    
    mark_obsolete = fields.Boolean(
        string='Marquer les articles non trouvés comme obsolètes',
        default=True,
        help='Les articles non retrouvés chez Rexel seront marqués comme obsolètes'
    )
    
    # ========== OPTIONS PERFORMANCE ==========
    use_parallel = fields.Boolean(
        string='⚡ Mode parallèle (Unités)',
        default=False,
        help='Utilise plusieurs threads pour accélérer la récupération des unités. '
             'Recommandé pour plus de 100 articles.'
    )
    
    parallel_workers = fields.Integer(
        string='Nombre de workers',
        default=5,
        help='Nombre de requêtes simultanées (1-10). Plus = plus rapide mais plus de charge serveur.'
    )
    
    # ========== APIs PACK DÉCOUVERTE ==========
    fetch_prices = fields.Boolean(
        string='💰 Prix (productSalePrices)', 
        default=True,
        help='Pack Découverte - Récupère les prix de vente client, remises et infos D3E'
    )
    
    fetch_units = fields.Boolean(
        string='📦 Unités (units)', 
        default=True,
        help='Pack Découverte - Récupère les unités de mesure et conditionnement'
    )
    
    fetch_stocks = fields.Boolean(
        string='📊 Stocks (positions)', 
        default=False,
        help='Pack Découverte - Récupère la disponibilité stock'
    )
    
    # ========== APIs PACK PREMIUM ==========
    fetch_images = fields.Boolean(
        string='🖼️ Images (full-image)', 
        default=False,
        help='Pack Premium - Récupère les URLs images produit'
    )
    
    fetch_fiches = fields.Boolean(
        string='📄 Fiches techniques', 
        default=False,
        help='Pack Premium - Récupère les liens vers les fiches techniques'
    )
    
    fetch_cee = fields.Boolean(
        string='🌿 CEE (éco-énergie)', 
        default=False,
        help='Pack Premium - Récupère les certificats économies énergie'
    )
    
    fetch_env = fields.Boolean(
        string='♻️ Attributs environnementaux', 
        default=False,
        help='Pack Premium - Récupère ecoscore et attributs durables'
    )
    
    fetch_replacement = fields.Boolean(
        string='🔄 Remplacements', 
        default=False,
        help='Pack Premium - Récupère les produits de remplacement'
    )
    
    # ========== STATISTIQUES ==========
    articles_count = fields.Integer(string='Nombre d\'articles', readonly=True)
    articles_updated = fields.Integer(string='Articles mis à jour', readonly=True)
    articles_obsolete = fields.Integer(string='Articles obsolètes', readonly=True)
    prices_changed = fields.Integer(string='Prix modifiés', readonly=True)
    units_updated = fields.Integer(string='Unités mises à jour', readonly=True)
    errors_count = fields.Integer(string='Erreurs', readonly=True)
    update_log = fields.Text(string='Log de mise à jour', readonly=True)

    @api.onchange('update_mode', 'filter_famille_id', 'filter_sous_famille_id', 
                  'filter_fonction_id', 'filter_fabricant',
                  'filter_obsolete', 'filter_with_product', 'filter_selection_durable',
                  'filter_import_source',
                  'filter_famille_text', 'filter_fabricant_text',
                  'filter_reference', 'filter_designation')
    def _onchange_count_articles(self):
        """Compte les articles qui seront mis à jour"""
        domain = self._get_articles_domain()
        self.articles_count = self.env['rexel.article'].search_count(domain)

    def _get_articles_domain(self):
        """Retourne le domaine pour filtrer les articles"""
        domain = []
        
        if self.update_mode == 'selection':
            # Articles sélectionnés depuis la vue
            article_ids = self.env.context.get('active_ids', [])
            domain = [('id', 'in', article_ids)]
        
        elif self.update_mode == 'filter':
            # ========== Filtres par hiérarchie famille (Many2one) ==========
            if self.filter_fonction_id:
                # Filtre le plus précis - par fonction
                domain.append(('fonction_libelle', '=', self.filter_fonction_id.name))
            elif self.filter_sous_famille_id:
                # Filtre par sous-famille
                domain.append(('sous_famille_libelle', '=', self.filter_sous_famille_id.name))
            elif self.filter_famille_id:
                # Filtre par famille
                domain.append(('famille_libelle', '=', self.filter_famille_id.name))
            
            # ========== Filtre par fabricant (liste déroulante) ==========
            if self.filter_fabricant and self.filter_fabricant != 'all':
                domain.append(('fabricant_libelle', '=', self.filter_fabricant))
            
            # ========== Filtres booléens ==========
            if self.filter_obsolete == 'yes':
                domain.append(('is_obsolete', '=', True))
            elif self.filter_obsolete == 'no':
                domain.append(('is_obsolete', '=', False))
            
            if self.filter_with_product == 'yes':
                domain.append(('product_id', '!=', False))
            elif self.filter_with_product == 'no':
                domain.append(('product_id', '=', False))
            
            if self.filter_selection_durable == 'yes':
                domain.append(('selection_durable', '=', True))
            elif self.filter_selection_durable == 'no':
                domain.append(('selection_durable', '=', False))
            
            # ========== Filtre par source d'import ==========
            if self.filter_import_source and self.filter_import_source != 'all':
                domain.append(('import_source', '=', self.filter_import_source))
            
            # ========== Filtres texte libre (recherche manuelle) ==========
            if self.filter_famille_text:
                domain.append(('famille_libelle', 'ilike', self.filter_famille_text))
            if self.filter_fabricant_text:
                domain.append(('fabricant_libelle', 'ilike', self.filter_fabricant_text))
            if self.filter_reference:
                domain.append(('reference_fabricant', 'ilike', self.filter_reference))
            if self.filter_designation:
                domain.append(('designation', 'ilike', self.filter_designation))
        
        # Mode 'all' = pas de filtre
        return domain

    def action_update_prices(self):
        """Lance la mise à jour complète des articles via l'API"""
        self.ensure_one()
        
        # Récupérer la configuration
        config = self.env['rexel.config'].get_config()
        
        if not config.api_enabled:
            raise UserError(_('L\'API n\'est pas activée dans la configuration.'))
        
        # Vérifier qu'au moins une API est sélectionnée
        if not any([self.fetch_prices, self.fetch_units, self.fetch_stocks, 
                    self.fetch_images, self.fetch_fiches, self.fetch_cee, 
                    self.fetch_env, self.fetch_replacement]):
            raise UserError(_('Veuillez sélectionner au moins une API à appeler.'))
        
        # Récupérer les articles à mettre à jour
        domain = self._get_articles_domain()
        articles = self.env['rexel.article'].search(domain)
        
        if not articles:
            raise UserError(_('Aucun article à mettre à jour.'))
        
        # Compteurs et logs
        batch_size = 50
        articles_updated = 0
        articles_obsolete = 0
        prices_changed = 0
        units_updated = 0
        errors_count = 0
        log_messages = []
        unit_errors = []  # Liste des références avec conditionnement inconnu
        
        log_messages.append(f"=== MISE À JOUR DE {len(articles)} ARTICLES ===")
        log_messages.append(f"APIs sélectionnées:")
        if self.fetch_prices:
            log_messages.append("  ✓ Prix (productSalePrices)")
        if self.fetch_units:
            log_messages.append("  ✓ Unités (units)")
        if self.fetch_stocks:
            log_messages.append("  ✓ Stocks (positions)")
        if self.fetch_images:
            log_messages.append("  ✓ Images (full-image)")
        if self.fetch_fiches:
            log_messages.append("  ✓ Fiches techniques")
        if self.fetch_cee:
            log_messages.append("  ✓ CEE (éco-énergie)")
        if self.fetch_env:
            log_messages.append("  ✓ Attributs environnementaux")
        if self.fetch_replacement:
            log_messages.append("  ✓ Remplacements")
        log_messages.append("")
        
        # ========== ÉTAPE 1 : API PRIX ==========
        if self.fetch_prices:
            log_messages.append("--- ÉTAPE 1: Récupération des PRIX ---")
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i+batch_size]
                
                try:
                    api_data = config.get_product_prices_from_api(batch)
                    
                    for article_id, product_info in api_data.items():
                        article = self.env['rexel.article'].browse(article_id)
                        
                        if product_info.get('found'):
                            update_vals = {
                                'is_obsolete': False,
                                'obsolete_date': False,
                                'obsolete_reason': False,
                                'last_api_update': fields.Datetime.now(),
                                'import_source': 'api',
                            }
                            
                            # Prix
                            if product_info.get('prix_base'):
                                update_vals['prix_base'] = product_info['prix_base']
                            if product_info.get('prix_net'):
                                if article.prix_net != product_info['prix_net']:
                                    prices_changed += 1
                                    if self.create_history:
                                        self.env['rexel.price.history'].create({
                                            'article_id': article.id,
                                            'prix_base': product_info.get('prix_base', article.prix_base),
                                            'prix_net': product_info['prix_net'],
                                            'source': 'rexel_api',
                                        })
                                update_vals['prix_net'] = product_info['prix_net']
                            
                            # Remise
                            if product_info.get('remise') is not None:
                                update_vals['remise'] = product_info['remise']
                            
                            # Références
                            if product_info.get('reference_rexel'):
                                update_vals['reference_rexel'] = product_info['reference_rexel']
                            if product_info.get('designation'):
                                update_vals['designation'] = product_info['designation']
                            
                            # D3E
                            if product_info.get('montant_d3e') is not None:
                                update_vals['montant_d3e'] = product_info['montant_d3e']
                            if product_info.get('unite_d3e') is not None:
                                update_vals['unite_d3e'] = product_info['unite_d3e']
                            
                            article.write(update_vals)
                            articles_updated += 1
                            
                        elif self.mark_obsolete:
                            if not article.is_obsolete:
                                article.write({
                                    'is_obsolete': True,
                                    'obsolete_date': fields.Date.today(),
                                    'obsolete_reason': 'Non trouvé via API Rexel',
                                })
                                articles_obsolete += 1
                                
                except Exception as e:
                    errors_count += 1
                    log_messages.append(f"  ✗ Erreur batch prix: {str(e)}")
            
            log_messages.append(f"  → {articles_updated} articles mis à jour, {prices_changed} prix modifiés")
        
        # ========== ÉTAPE 2 : API UNITÉS ==========
        if self.fetch_units:
            log_messages.append("")
            log_messages.append("--- ÉTAPE 2: Récupération des UNITÉS ---")
            
            # Filtrer les articles qui n'ont pas d'unité forcée
            articles_for_units = articles.filtered(lambda a: not a.unite_mesure_forcee)
            skipped_forced = len(articles) - len(articles_for_units)
            
            if skipped_forced > 0:
                log_messages.append(f"  🔒 {skipped_forced} articles avec unité forcée (ignorés)")
            
            units_batch_updated = 0
            units_batch_errors = []
            
            if self.use_parallel and len(articles_for_units) > 10:
                # ========== MODE PARALLÈLE ==========
                log_messages.append(f"  ⚡ Mode parallèle activé ({self.parallel_workers} workers)")
                start_time = time.time()
                
                # Préparer les données pour le traitement parallèle
                articles_data = [(a.id, a.trigramme_fabricant, a.reference_fabricant, a.unite_mesure, a.conditionnement) 
                                 for a in articles_for_units]
                
                # Fonction pour appeler l'API (exécutée dans un thread)
                def fetch_unit_data(article_info):
                    art_id, trigramme, reference, current_unite, current_cond = article_info
                    try:
                        # Créer une nouvelle connexion pour ce thread
                        unit_data = config.get_product_unit_from_api(trigramme, reference)
                        return (art_id, trigramme, reference, current_unite, current_cond, unit_data, None)
                    except Exception as e:
                        return (art_id, trigramme, reference, current_unite, current_cond, None, str(e))
                
                # Exécuter en parallèle
                workers = max(1, min(10, self.parallel_workers))
                results = []
                
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    futures = {executor.submit(fetch_unit_data, art_data): art_data for art_data in articles_data}
                    
                    for future in as_completed(futures):
                        try:
                            results.append(future.result())
                        except Exception as e:
                            _logger.error(f"Erreur thread: {e}")
                
                # Traiter les résultats
                for result in results:
                    art_id, trigramme, reference, current_unite, current_cond, unit_data, error = result
                    
                    if error:
                        errors_count += 1
                        _logger.debug(f"Erreur unité parallèle {reference}: {error}")
                        continue
                    
                    if unit_data:
                        api_unit_raw = unit_data.get('motUnite') or unit_data.get('unite_api')
                        conditionnement = unit_data.get('typeConditionnement') or unit_data.get('conditionnement') or ''
                        
                        # Appliquer la logique centralisée
                        unite_finale, unit_error = config._determine_unit_from_conditionnement(
                            conditionnement, None, api_unit_raw, reference
                        )
                        
                        update_vals = {}
                        
                        if unite_finale and current_unite != unite_finale:
                            update_vals['unite_mesure'] = unite_finale
                            units_batch_updated += 1
                        
                        if conditionnement and current_cond != conditionnement:
                            update_vals['conditionnement'] = conditionnement
                        
                        if unit_data.get('codeEAN13'):
                            update_vals['code_ean13'] = unit_data['codeEAN13']
                        
                        if update_vals:
                            # Mise à jour dans le contexte principal
                            article = self.env['rexel.article'].browse(art_id)
                            if article.exists():
                                article.write(update_vals)
                        
                        if unit_error:
                            units_batch_errors.append(f"{reference} (cond: {unit_error})")
                
                elapsed = time.time() - start_time
                log_messages.append(f"  ⏱️ Temps: {elapsed:.1f}s ({len(articles_for_units)/elapsed:.1f} articles/s)")
                
            else:
                # ========== MODE SÉQUENTIEL (original) ==========
                for article in articles_for_units:
                    try:
                        unit_data = config.get_product_unit_from_api(
                            article.trigramme_fabricant,
                            article.reference_fabricant
                        )
                        
                        if unit_data:
                            # Récupérer les données brutes de l'API
                            api_unit_raw = unit_data.get('motUnite') or unit_data.get('unite_api')
                            conditionnement = unit_data.get('typeConditionnement') or unit_data.get('conditionnement') or ''
                            
                            # Appliquer la logique centralisée
                            unite_finale, unit_error = config._determine_unit_from_conditionnement(
                                conditionnement, None, api_unit_raw, article.reference_fabricant
                            )
                            
                            update_vals = {}
                            
                            # Unité de mesure
                            if unite_finale and article.unite_mesure != unite_finale:
                                update_vals['unite_mesure'] = unite_finale
                                units_batch_updated += 1
                            
                            # Conditionnement
                            if conditionnement and article.conditionnement != conditionnement:
                                update_vals['conditionnement'] = conditionnement
                            
                            # Code EAN13
                            if unit_data.get('codeEAN13') and not article.code_ean13:
                                update_vals['code_ean13'] = unit_data['codeEAN13']
                            
                            if update_vals:
                                article.write(update_vals)
                            
                            # Tracker les erreurs de conditionnement
                            if unit_error:
                                units_batch_errors.append(f"{article.reference_fabricant} (cond: {unit_error})")
                                
                    except Exception as e:
                        errors_count += 1
                        _logger.error(f"Erreur unité {article.reference_fabricant}: {e}")
            
            units_updated += units_batch_updated
            unit_errors.extend(units_batch_errors)
            
            log_messages.append(f"  → {units_batch_updated} unités mises à jour")
            if units_batch_errors:
                log_messages.append(f"  ⚠️ {len(units_batch_errors)} conditionnements inconnus")
        
        # ========== ÉTAPE 3 : API STOCKS ==========
        if self.fetch_stocks:
            log_messages.append("")
            log_messages.append("--- ÉTAPE 3: Récupération des STOCKS ---")
            stocks_updated = 0
            
            for i in range(0, len(articles), batch_size):
                batch = articles[i:i+batch_size]
                try:
                    # Préparer la liste pour l'API stocks
                    products_list = [(a.trigramme_fabricant, a.reference_fabricant) for a in batch]
                    stock_data = config.get_stock_positions(products_list)
                    
                    for article in batch:
                        key = (article.trigramme_fabricant, article.reference_fabricant)
                        if key in stock_data:
                            info = stock_data[key]
                            update_vals = {}
                            
                            if info.get('availableBranchStock') is not None:
                                update_vals['api_stock_agence'] = info['availableBranchStock']
                            if info.get('availableCLRStock') is not None:
                                update_vals['api_stock_clr'] = info['availableCLRStock']
                            if info.get('branchAvailabilityDelay'):
                                update_vals['api_delai_agence'] = info['branchAvailabilityDelay']
                            
                            if update_vals:
                                article.write(update_vals)
                                stocks_updated += 1
                                
                except Exception as e:
                    errors_count += 1
                    log_messages.append(f"  ✗ Erreur batch stocks: {str(e)}")
            
            log_messages.append(f"  → {stocks_updated} stocks mis à jour")
        
        # ========== ÉTAPE 4+ : APIs PREMIUM ==========
        if any([self.fetch_images, self.fetch_fiches, self.fetch_cee, self.fetch_env, self.fetch_replacement]):
            log_messages.append("")
            log_messages.append("--- APIs PREMIUM ---")
            
            for article in articles:
                trigramme = article.trigramme_fabricant
                ref_fab = article.reference_fabricant
                
                if not trigramme or not ref_fab:
                    continue
                
                try:
                    # Images
                    if self.fetch_images:
                        img_data = config.get_product_image(trigramme, ref_fab)
                        if img_data and img_data.get('url'):
                            article.write({'url_image': img_data['url']})
                    
                    # Fiches techniques
                    if self.fetch_fiches:
                        fiche_data = config.get_product_technical_sheet(trigramme, ref_fab)
                        if fiche_data and fiche_data.get('url'):
                            article.write({'api_fiche_technique_url': fiche_data['url']})
                    
                    # CEE
                    if self.fetch_cee:
                        cee_data = config.get_product_cee(trigramme, ref_fab)
                        if cee_data:
                            update_vals = {}
                            if cee_data.get('idOperationCEE'):
                                update_vals['api_cee_id_operation'] = cee_data['idOperationCEE']
                            if cee_data.get('referenceOperationCEE'):
                                update_vals['api_cee_reference'] = cee_data['referenceOperationCEE']
                            if cee_data.get('certificatCEE'):
                                update_vals['api_cee_certificat'] = cee_data['certificatCEE']
                            if cee_data.get('urlFicheOperationCEE'):
                                update_vals['api_cee_url_fiche'] = cee_data['urlFicheOperationCEE']
                            if update_vals:
                                article.write(update_vals)
                    
                    # Environnement
                    if self.fetch_env:
                        env_data = config.get_product_environmental(trigramme, ref_fab)
                        if env_data:
                            update_vals = {}
                            if env_data.get('noteEcoscore'):
                                update_vals['ecoscore'] = env_data['noteEcoscore']
                            if env_data.get('codeCritereEnvironemental'):
                                update_vals['api_code_critere_env'] = env_data['codeCritereEnvironemental']
                            if update_vals:
                                article.write(update_vals)
                    
                    # Remplacements
                    if self.fetch_replacement:
                        repl_data = config.get_product_replacement(trigramme, ref_fab)
                        if repl_data:
                            update_vals = {}
                            if repl_data.get('sens'):
                                update_vals['api_remplacement_sens'] = repl_data['sens']
                            if repl_data.get('referenceRexelRemplacement'):
                                update_vals['api_remplacement_ref_rexel'] = repl_data['referenceRexelRemplacement']
                            if update_vals:
                                article.write(update_vals)
                                
                except Exception as e:
                    _logger.debug(f"Erreur API Premium {article.reference_fabricant}: {e}")
            
            log_messages.append("  → APIs Premium traitées")
        
        # ========== RÉSUMÉ ==========
        log_messages.append("")
        log_messages.append("=" * 50)
        log_messages.append("RÉSUMÉ")
        log_messages.append("=" * 50)
        log_messages.append(f"✓ {articles_updated} articles mis à jour")
        log_messages.append(f"✓ {prices_changed} prix modifiés")
        log_messages.append(f"✓ {units_updated} unités mises à jour")
        if articles_obsolete > 0:
            log_messages.append(f"⚠️ {articles_obsolete} articles marqués obsolètes")
        if errors_count > 0:
            log_messages.append(f"✗ {errors_count} erreurs")
        
        # Afficher les erreurs de conditionnement
        if unit_errors:
            log_messages.append("")
            log_messages.append(f"⚠️ {len(unit_errors)} conditionnements inconnus (défaut U):")
            for error in unit_errors[:10]:
                log_messages.append(f"  • {error}")
            if len(unit_errors) > 10:
                log_messages.append(f"  ... et {len(unit_errors) - 10} autres")
        
        # Enregistrer les résultats
        self.write({
            'articles_updated': articles_updated,
            'articles_obsolete': articles_obsolete,
            'prices_changed': prices_changed,
            'units_updated': units_updated,
            'errors_count': errors_count,
            'update_log': '\n'.join(log_messages),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.prices.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
