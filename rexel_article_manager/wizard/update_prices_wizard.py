# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class UpdatePricesWizard(models.TransientModel):
    _name = 'update.prices.wizard'
    _description = 'Mise à jour des articles via API Rexel Cloud'

    # ========== MODE DE MISE À JOUR ==========
    update_mode = fields.Selection([
        ('all', 'Tous les articles'),
        ('selection', 'Articles sélectionnés'),
        ('filter', 'Avec filtre'),
    ], string='Articles à mettre à jour', default='all', required=True)
    
    # ========== FILTRES ==========
    filter_famille = fields.Char(string='Famille contient')
    filter_fabricant = fields.Char(string='Fabricant contient')
    
    # ========== OPTIONS ==========
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
    
    fetch_units = fields.Boolean(
        string='Récupérer les unités de mesure (UOM)',
        default=False,
        help='Appelle l\'API units pour chaque article sans unité. ATTENTION: Peut être lent si beaucoup d\'articles!'
    )
    
    # ========== STATISTIQUES ==========
    articles_count = fields.Integer(string='Nombre d\'articles', readonly=True)
    articles_updated = fields.Integer(string='Articles mis à jour', readonly=True)
    articles_obsolete = fields.Integer(string='Articles obsolètes', readonly=True)
    prices_changed = fields.Integer(string='Prix modifiés', readonly=True)
    units_updated = fields.Integer(string='Unités mises à jour', readonly=True)
    errors_count = fields.Integer(string='Erreurs', readonly=True)
    update_log = fields.Text(string='Log de mise à jour', readonly=True)

    @api.onchange('update_mode', 'filter_famille', 'filter_fabricant')
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
            if self.filter_famille:
                domain.append(('famille_libelle', 'ilike', self.filter_famille))
            if self.filter_fabricant:
                domain.append(('fabricant_libelle', 'ilike', self.filter_fabricant))
        
        # Mode 'all' = pas de filtre
        return domain

    def action_update_prices(self):
        """Lance la mise à jour complète des articles via l'API"""
        self.ensure_one()
        
        # Récupérer la configuration
        config = self.env['rexel.config'].get_config()
        
        if not config.api_enabled:
            raise UserError(_('L\'API n\'est pas activée dans la configuration.'))
        
        # Récupérer les articles à mettre à jour
        domain = self._get_articles_domain()
        articles = self.env['rexel.article'].search(domain)
        
        if not articles:
            raise UserError(_('Aucun article à mettre à jour.'))
        
        # Mise à jour par batch
        batch_size = 50
        articles_updated = 0
        articles_obsolete = 0
        prices_changed = 0
        units_updated = 0
        errors_count = 0
        log_messages = []
        unit_errors = []  # Liste des références avec conditionnement inconnu
        
        for i in range(0, len(articles), batch_size):
            batch = articles[i:i+batch_size]
            
            try:
                # Appeler l'API pour ce batch
                api_data = config.get_product_prices_from_api(batch)
                
                for article_id, product_info in api_data.items():
                    article = self.env['rexel.article'].browse(article_id)
                    
                    if product_info.get('found'):
                        # Article trouvé - Mise à jour complète
                        update_vals = {
                            'is_obsolete': False,
                            'obsolete_date': False,
                            'obsolete_reason': False,
                            'last_api_update': fields.Datetime.now(),
                            'import_source': 'api',
                        }
                        
                        # Tracker les erreurs d'unités (conditionnement inconnu)
                        if product_info.get('unit_error'):
                            unit_errors.append(f"{article.reference_fabricant} (cond: {product_info['unit_error']})")
                        
                        # Prix
                        if product_info.get('prix_base'):
                            update_vals['prix_base'] = product_info['prix_base']
                        if product_info.get('prix_net'):
                            # Vérifier si le prix a changé pour l'historique
                            if article.prix_net != product_info['prix_net']:
                                prices_changed += 1
                                if self.create_history:
                                    self.env['rexel.price.history'].create({
                                        'article_id': article.id,
                                        'old_price': article.prix_net,
                                        'new_price': product_info['prix_net'],
                                        'date': fields.Datetime.now(),
                                    })
                            update_vals['prix_net'] = product_info['prix_net']
                        
                        # Remise: toujours mettre à jour si présente (même si 0)
                        if product_info.get('remise') is not None:
                            update_vals['remise'] = product_info['remise']
                        
                        # Références (mise à jour si présentes)
                        if product_info.get('reference_rexel'):
                            update_vals['reference_rexel'] = product_info['reference_rexel']
                        if product_info.get('designation'):
                            update_vals['designation'] = product_info['designation']
                        
                        # Unité de mesure (UOM) - respecter le flag unite_mesure_forcee
                        if product_info.get('unite_mesure') and not article.unite_mesure_forcee:
                            if article.unite_mesure != product_info['unite_mesure']:
                                update_vals['unite_mesure'] = product_info['unite_mesure']
                                units_updated += 1
                        elif self.fetch_units and article.trigramme_fabricant and not article.unite_mesure_forcee:
                            # Si pas d'unité retournée et option activée, appeler l'API units
                            # L'API units attend: supplierCode (trigramme) et supplierComRef (référence commerciale)
                            # IMPORTANT: utiliser la référence SANS le trigramme (ex: 91028 au lieu de BE491028)
                            
                            unit_data = None
                            refs_to_try = []
                            
                            # Construire la liste des références à essayer
                            # D'abord la référence fabricant (souvent la bonne)
                            if article.reference_fabricant:
                                refs_to_try.append(article.reference_fabricant)
                            
                            # Pour certaines références Rexel qui sont "TRIGRAMME+REF", extraire la partie REF
                            if article.reference_rexel:
                                ref_rexel = article.reference_rexel
                                trigramme = article.trigramme_fabricant or ''
                                # Si la référence Rexel commence par le trigramme, on l'enlève
                                if trigramme and ref_rexel.startswith(trigramme):
                                    ref_sans_trigramme = ref_rexel[len(trigramme):]
                                    if ref_sans_trigramme and ref_sans_trigramme not in refs_to_try:
                                        refs_to_try.insert(0, ref_sans_trigramme)  # Priorité
                                if ref_rexel not in refs_to_try:
                                    refs_to_try.append(ref_rexel)
                            
                            for ref_to_try in refs_to_try:
                                try:
                                    unit_data = config.get_product_unit_from_api(
                                        article.trigramme_fabricant,
                                        ref_to_try
                                    )
                                    if unit_data and unit_data.get('unite'):
                                        # L'API retourne: {'unite': 'U' ou 'ML', 'unite_api': 'PIECE' ou 'METRE', 'warning': ...}
                                        update_vals['unite_mesure'] = unit_data['unite']
                                        units_updated += 1
                                        
                                        # Construire le message de log
                                        unite_api = unit_data.get('unite_api', '')
                                        unite_odoo = unit_data['unite']
                                        
                                        if unit_data.get('warning'):
                                            # Unité non reconnue - avertissement
                                            log_messages.append(f"  ⚠️ {article.reference_fabricant}: {unit_data['warning']} (API: {unite_api} -> {unite_odoo})")
                                        else:
                                            log_messages.append(f"  📏 Unité {article.reference_fabricant}: {unite_api} -> {unite_odoo}")
                                        break
                                except Exception as e:
                                    _logger.warning(f"Erreur récupération unité {article.reference_fabricant} avec ref {ref_to_try}: {e}")
                        
                        if product_info.get('conditionnement'):
                            update_vals['conditionnement'] = product_info['conditionnement']
                        
                        # Écotaxe D3E
                        if product_info.get('montant_d3e'):
                            update_vals['montant_d3e'] = product_info['montant_d3e']
                        if product_info.get('unite_d3e'):
                            update_vals['unite_d3e'] = product_info['unite_d3e']
                        
                        # Mettre à jour l'article
                        article.write(update_vals)
                        articles_updated += 1
                        
                        # Mettre à jour le produit Odoo si demandé
                        if self.update_products and article.product_id:
                            product_vals = {
                                'list_price': product_info.get('prix_base', article.prix_base),
                            }
                            if product_info.get('designation'):
                                product_vals['name'] = product_info['designation']
                            article.product_id.write(product_vals)
                        
                        log_messages.append(f"✓ {article.reference_fabricant}: MAJ OK")
                        
                    else:
                        # Article NON trouvé chez Rexel
                        if self.mark_obsolete:
                            article.write({
                                'is_obsolete': True,
                                'obsolete_date': fields.Datetime.now(),
                                'obsolete_reason': product_info.get('error', 'Article non trouvé lors de la mise à jour API'),
                            })
                            articles_obsolete += 1
                            log_messages.append(f"⚠ {article.reference_fabricant}: OBSOLÈTE - Non trouvé chez Rexel")
                        else:
                            errors_count += 1
                            log_messages.append(f"✗ {article.reference_fabricant}: Non trouvé")
                    
            except Exception as e:
                errors_count += len(batch)
                error_msg = f"Erreur batch {i//batch_size + 1}: {str(e)}"
                log_messages.append(error_msg)
                _logger.error(error_msg)
        
        # Mettre à jour les statistiques
        self.articles_updated = articles_updated
        self.articles_obsolete = articles_obsolete
        self.prices_changed = prices_changed
        self.units_updated = units_updated
        self.errors_count = errors_count
        
        # ==========================================================
        # VÉRIFICATION FINALE: Réparer les articles obsolètes par erreur
        # ==========================================================
        articles_repaired = 0
        if articles_obsolete > 0:
            _logger.info("=== Vérification des articles marqués obsolètes ===")
            
            # Récupérer les articles qui viennent d'être marqués obsolètes
            obsolete_articles = articles.filtered(lambda a: a.is_obsolete)
            
            if obsolete_articles:
                # Re-vérifier un par un les articles obsolètes
                for article in obsolete_articles:
                    if not article.trigramme_fabricant or not article.reference_fabricant:
                        continue
                    
                    try:
                        # Appel API individuel pour vérification
                        single_result = config.get_product_prices_from_api(article)
                        
                        if single_result.get(article.id, {}).get('found'):
                            # Article trouvé ! C'était une erreur du batch
                            product_info = single_result[article.id]
                            
                            update_vals = {
                                'is_obsolete': False,
                                'obsolete_date': False,
                                'obsolete_reason': False,
                                'last_api_update': fields.Datetime.now(),
                                'import_source': 'api',  # Source = API après réparation
                            }
                            
                            # Mettre à jour les prix
                            if product_info.get('prix_base'):
                                update_vals['prix_base'] = product_info['prix_base']
                            if product_info.get('prix_net'):
                                update_vals['prix_net'] = product_info['prix_net']
                            if product_info.get('remise') is not None:
                                update_vals['remise'] = product_info['remise']
                            # Mettre à jour l'unité si disponible ET non forcée
                            if product_info.get('unite_mesure') and not article.unite_mesure_forcee:
                                update_vals['unite_mesure'] = product_info['unite_mesure']
                            
                            article.write(update_vals)
                            articles_repaired += 1
                            articles_obsolete -= 1
                            log_messages.append(f"🔧 {article.reference_fabricant}: RÉPARÉ (retrouvé en vérification)")
                            
                    except Exception as e:
                        _logger.debug(f"Vérification {article.reference_fabricant}: {e}")
                
                if articles_repaired > 0:
                    _logger.info(f"=== {articles_repaired} articles réparés ===")
                    self.articles_obsolete = articles_obsolete
        
        # Résumé en début de log
        summary = f"""
========== RÉSUMÉ ==========
✓ Articles mis à jour: {articles_updated}
💰 Prix modifiés: {prices_changed}
📏 Unités mises à jour: {units_updated}
⚠ Articles obsolètes: {articles_obsolete}
🔧 Articles réparés: {articles_repaired}
✗ Erreurs: {errors_count}
============================

"""
        # Ajouter les erreurs d'unités si présentes
        if unit_errors:
            unit_error_msg = f"""
⚠️ ATTENTION - UNITÉS À VÉRIFIER ({len(unit_errors)} articles)
Les articles suivants ont un conditionnement inconnu.
L'unité a été mise à U par défaut - À VÉRIFIER MANUELLEMENT:

"""
            # Limiter à 50 références pour ne pas surcharger
            for ref in unit_errors[:50]:
                unit_error_msg += f"  • {ref}\n"
            if len(unit_errors) > 50:
                unit_error_msg += f"  ... et {len(unit_errors) - 50} autres\n"
            unit_error_msg += "\n"
            summary += unit_error_msg
        
        self.update_log = summary + '\n'.join(log_messages[-100:])  # Limiter à 100 lignes
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'update.prices.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'show_results': True},
        }

    def action_close(self):
        """Ferme le wizard"""
        return {'type': 'ir.actions.act_window_close'}
