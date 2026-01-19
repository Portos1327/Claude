# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class RexelConfig(models.Model):
    _name = 'rexel.config'
    _description = 'Configuration Rexel Cloud API'
    
    name = fields.Char(string='Nom', required=True, default='Configuration Rexel')
    
    # ========== CONFIGURATION API ==========
    api_enabled = fields.Boolean(string='API activée', default=False)
    api_base_url = fields.Char(
        string='URL de base API',
        default='https://api.rexel.fr',
        help='URL de base de l\'API Rexel Cloud'
    )
    
    # OAuth2 Microsoft
    oauth_tenant_id = fields.Char(
        string='Tenant ID Azure',
        default='822cd975-5643-4b7e-b398-69a164e55719',
        help='ID du tenant Microsoft Azure'
    )
    oauth_client_id = fields.Char(
        string='Client ID',
        default='4036c6d5-fce1-4569-a177-072a4e45bd39',
        help='Client ID de l\'application Azure'
    )
    oauth_client_secret = fields.Char(
        string='Client Secret',
        help='Client Secret de l\'application Azure (sensible)'
    )
    oauth_scope = fields.Char(
        string='Scope OAuth',
        default='aee2ba94-a840-453a-9151-1355638ac04e/.default',
        help='Portée de l\'authentification'
    )
    subscription_key = fields.Char(
        string='Clé d\'abonnement',
        default='e9fa63ce8d934beb83c5a1f94817983a',
        help='Clé d\'abonnement API Rexel'
    )
    
    # Informations client Rexel
    customer_id = fields.Char(
        string='N° client Rexel',
        help='Numéro de compte client REXEL (7 chiffres)'
    )
    customer_scope = fields.Char(
        string='Mot client',
        default='TURQUAND',
        help='Mot client pour le contrôle de juridiction (en majuscules)'
    )
    
    # ========== FOURNISSEUR ODOO ASSOCIÉ ==========
    supplier_id = fields.Many2one(
        'res.partner',
        string='Fournisseur Odoo',
        domain=[('is_company', '=', True)],
        help='Contact fournisseur Odoo à associer aux produits créés depuis Rexel. '
             'Ce fournisseur sera automatiquement ajouté dans l\'onglet Achats des produits.'
    )
    
    supplier_delay = fields.Integer(
        string='Délai de livraison (jours)',
        default=3,
        help='Délai de livraison par défaut pour ce fournisseur'
    )
    
    supplier_currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        help='Devise utilisée pour les prix fournisseur'
    )
    
    # Token management
    access_token = fields.Char(string='Access Token', readonly=True)
    token_expires_at = fields.Datetime(string='Token expire le', readonly=True)
    
    # ========== CONFIGURATION IMPORT ==========
    import_mode = fields.Selection([
        ('excel', 'Fichier Excel uniquement'),
        ('api', 'API uniquement'),
        ('both', 'Excel et API'),
    ], string='Mode d\'import', default='both', required=True)
    
    auto_update_prices = fields.Boolean(
        string='Mise à jour auto des prix',
        default=False,
        help='Met à jour automatiquement les prix depuis l\'API'
    )
    
    auto_update_frequency = fields.Selection([
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
    ], string='Fréquence mise à jour', default='weekly')
    
    # ========== CHEMINS TEMPLATES (conservés pour exports) ==========
    template_beg = fields.Char(
        string='Template BEG',
        default='C:\\Program Files\\Odoo 18.0.20251211\\server\\templates\\MAJ Base_Article - BEG avec formules V1.xlsx',
        help='Chemin complet vers le fichier template BEG'
    )
    
    template_niedax = fields.Char(
        string='Template NIEDAX',
        default='C:\\Program Files\\Odoo 18.0.20251211\\server\\templates\\MAJ Base_Article - NIEDAX avec formules V1.xlsx',
        help='Chemin complet vers le fichier template NIEDAX'
    )
    
    template_cables = fields.Char(
        string='Template CÂBLES',
        default='C:\\Program Files\\Odoo 18.0.20251211\\server\\templates\\MAJ Base_Article - CABLES avec formules V1.xlsx',
        help='Chemin complet vers le fichier template CÂBLES'
    )
    
    template_quickdevis = fields.Char(
        string='Template QuickDevis',
        default='C:\\Program Files\\Odoo 18.0.20251211\\server\\templates\\Tarif câbles net rexel oct 2025 V2.xlsx',
        help='Chemin complet vers le fichier template QuickDevis 7'
    )
    
    # ========== STATISTIQUES API ==========
    last_api_call = fields.Datetime(string='Dernier appel API', readonly=True)
    api_call_count = fields.Integer(string='Nb appels API', readonly=True, default=0)
    last_api_error = fields.Text(string='Dernière erreur API', readonly=True)
    
    # ========== RATE LIMITING ==========
    rate_limit_enabled = fields.Boolean(
        string='Limiter les requêtes',
        default=True,
        help='Active la limitation du nombre de requêtes par seconde'
    )
    rate_limit_per_second = fields.Integer(
        string='Requêtes max / seconde',
        default=10,
        help='Nombre maximum de requêtes par seconde (Découverte: 10, Premium: 20)'
    )
    rate_limit_last_reset = fields.Datetime(
        string='Dernier reset rate limit',
        readonly=True
    )
    rate_limit_current_count = fields.Integer(
        string='Compteur actuel',
        readonly=True,
        default=0
    )
    
    # ========== PACK API ==========
    api_pack = fields.Selection([
        ('discovery', 'Pack Découverte (Gratuit)'),
        ('premium', 'Pack Premium (Abonnement)'),
    ], string='Pack API', default='discovery', required=True,
       help='Sélectionnez votre pack API Rexel pour activer les fonctionnalités correspondantes')
    
    @api.onchange('api_pack')
    def _onchange_api_pack(self):
        """Met à jour automatiquement la limite de requêtes selon le pack"""
        if self.api_pack == 'discovery':
            self.rate_limit_per_second = 10
        elif self.api_pack == 'premium':
            self.rate_limit_per_second = 20
    
    # Pas de contrainte SQL - on gère la configuration unique via get_config()

    @api.model
    def get_config(self):
        """Retourne la configuration (crée si n'existe pas)"""
        config = self.search([], limit=1)
        if not config:
            config = self.with_context(force_create=True).create({'name': 'Configuration Rexel'})
        return config
    
    @api.model
    def action_open_config(self):
        """Ouvre la configuration existante ou en crée une nouvelle"""
        config = self.get_config()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Configuration Rexel',
            'res_model': 'rexel.config',
            'res_id': config.id,
            'view_mode': 'form',
            'target': 'inline',
        }

    @api.model
    def action_reset_config(self):
        """Supprime toutes les configurations existantes pour permettre une nouvelle création"""
        configs = self.search([])
        if configs:
            configs.unlink()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Configuration réinitialisée'),
                    'message': _('La configuration a été supprimée. Vous pouvez en créer une nouvelle.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        return True

    def action_reset_token(self):
        """Réinitialise le token OAuth2"""
        self.ensure_one()
        self.write({
            'access_token': False,
            'token_expires_at': False,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Token réinitialisé'),
                'message': _('Le token a été supprimé. Un nouveau sera généré à la prochaine requête API.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_delete_and_recreate(self):
        """Supprime la configuration actuelle et ouvre le formulaire de création"""
        self.ensure_one()
        self.unlink()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Nouvelle Configuration Rexel',
            'res_model': 'rexel.config',
            'view_mode': 'form',
            'target': 'current',
            'context': {'force_create': True},
        }

    def _get_access_token(self):
        """
        Obtient un access token OAuth2 depuis Microsoft Azure
        Utilise le flow Client Credentials
        """
        self.ensure_one()
        
        # Vérifier si le token actuel est encore valide
        if self.access_token and self.token_expires_at:
            now = fields.Datetime.now()
            # Garder 5 minutes de marge
            if self.token_expires_at > now + timedelta(minutes=5):
                return self.access_token
        
        # Obtenir un nouveau token
        token_url = f"https://login.microsoftonline.com/{self.oauth_tenant_id}/oauth2/v2.0/token/"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.oauth_client_id,
            'client_secret': self.oauth_client_secret,
            'scope': self.oauth_scope,
        }
        
        try:
            response = requests.post(token_url, data=data, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)  # Par défaut 1h
                
                # Enregistrer le token et sa date d'expiration
                self.write({
                    'access_token': access_token,
                    'token_expires_at': fields.Datetime.now() + timedelta(seconds=expires_in),
                })
                
                return access_token
            else:
                error_msg = f"Erreur OAuth2: {response.status_code} - {response.text}"
                self.last_api_error = error_msg
                raise UserError(_(error_msg))
                
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur connexion OAuth2: {str(e)}"
            self.last_api_error = error_msg
            raise UserError(_(error_msg))

    def _get_api_headers(self):
        """Retourne les headers HTTP pour les appels API"""
        self.ensure_one()
        
        access_token = self._get_access_token()
        
        return {
            'Authorization': f'Bearer {access_token}',
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/json',
        }

    def _rate_limit_wait(self):
        """
        Implémente le rate limiting pour respecter la limite de requêtes/seconde.
        Attend si nécessaire avant de permettre une nouvelle requête.
        """
        import time
        self.ensure_one()
        
        if not self.rate_limit_enabled:
            return
        
        max_requests = self.rate_limit_per_second or 10
        now = fields.Datetime.now()
        
        # Vérifier si on doit réinitialiser le compteur (nouvelle seconde)
        if self.rate_limit_last_reset:
            time_diff = (now - self.rate_limit_last_reset).total_seconds()
            
            if time_diff >= 1.0:
                # Nouvelle seconde - réinitialiser le compteur
                self.write({
                    'rate_limit_last_reset': now,
                    'rate_limit_current_count': 1,
                })
            elif self.rate_limit_current_count >= max_requests:
                # Limite atteinte - attendre la fin de la seconde
                wait_time = 1.0 - time_diff
                if wait_time > 0:
                    _logger.debug(f"Rate limit atteint ({max_requests}/sec), attente de {wait_time:.3f}s")
                    time.sleep(wait_time)
                # Réinitialiser après l'attente
                self.write({
                    'rate_limit_last_reset': fields.Datetime.now(),
                    'rate_limit_current_count': 1,
                })
            else:
                # Incrémenter le compteur
                self.write({
                    'rate_limit_current_count': self.rate_limit_current_count + 1,
                })
        else:
            # Première requête
            self.write({
                'rate_limit_last_reset': now,
                'rate_limit_current_count': 1,
            })

    def action_test_api_connection(self):
        """Teste la connexion à l'API Rexel avec OAuth2"""
        self.ensure_one()
        
        if not self.api_enabled:
            raise UserError(_('L\'API n\'est pas activée dans la configuration.'))
        
        if not self.customer_id:
            raise UserError(_('Le numéro client Rexel n\'est pas configuré.'))
        
        if not self.oauth_client_secret:
            raise UserError(_('Le Client Secret OAuth2 n\'est pas configuré.'))
        
        try:
            # 1. Obtenir le token OAuth2
            access_token = self._get_access_token()
            
            # 2. Tester avec l'API Customers
            url = f"{self.api_base_url}/external/customers/{self.customer_id}"
            headers = self._get_api_headers()
            
            response = requests.get(url, headers=headers, timeout=10)
            
            self.last_api_call = fields.Datetime.now()
            self.api_call_count += 1
            
            if response.status_code == 200:
                data = response.json()
                customer_name = data.get('customerName', 'N/A')
                
                self.last_api_error = False
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('✅ Connexion réussie'),
                        'message': _(f'API Rexel opérationnelle\n'
                                   f'Client: {customer_name}\n'
                                   f'Token OAuth2 valide jusqu\'à {self.token_expires_at}'),
                        'type': 'success',
                        'sticky': True,
                    }
                }
            else:
                error_msg = f"Erreur HTTP {response.status_code}: {response.text}"
                self.last_api_error = error_msg
                raise UserError(_(f'Erreur de connexion: {error_msg}'))
                
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            self.last_api_error = error_msg
            raise UserError(_(f'Erreur de connexion à l\'API: {error_msg}'))

    def action_verify_templates(self):
        """Vérifie que les fichiers templates existent"""
        import os
        self.ensure_one()
        
        templates = {
            'BEG': self.template_beg,
            'NIEDAX': self.template_niedax,
            'CÂBLES': self.template_cables,
            'QuickDevis': self.template_quickdevis,
        }
        
        messages = []
        all_exist = True
        
        for name, path in templates.items():
            if path and os.path.exists(path):
                messages.append(f"✓ {name}: OK")
            else:
                messages.append(f"✗ {name}: INTROUVABLE ({path})")
                all_exist = False
        
        message_type = 'success' if all_exist else 'warning'
        title = 'Vérification des templates' if all_exist else 'Templates manquants'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _(title),
                'message': '<br/>'.join(messages),
                'type': message_type,
                'sticky': True,
            }
        }
    
    def _calculate_remise(self, api_remise, prix_base, prix_net):
        """
        Calcule la remise en pourcentage à partir des prix.
        
        NOTE IMPORTANTE: L'API Rexel retourne `referenceRebate` comme un MONTANT (en €),
        PAS comme un pourcentage ! Il faut donc TOUJOURS calculer la remise depuis les prix.
        
        Formule: remise_% = ((prix_base - prix_net) / prix_base) * 100
        
        Args:
            api_remise: Valeur referenceRebate retournée par l'API (MONTANT en €, ignoré)
            prix_base: Prix de base (clientBasePrice)
            prix_net: Prix net client (clientNetPrice)
            
        Returns:
            float: Remise en pourcentage (0-100)
        """
        # TOUJOURS calculer la remise depuis les prix
        # car referenceRebate est un MONTANT, pas un pourcentage !
        try:
            base = float(prix_base or 0)
            net = float(prix_net or 0)
            
            if base > 0 and net >= 0:
                remise_calculee = ((base - net) / base) * 100
                _logger.debug(f"Remise calculée: {remise_calculee:.2f}% (base={base}, net={net})")
                return round(remise_calculee, 2)
        except (ValueError, TypeError) as e:
            _logger.debug(f"Erreur calcul remise: {e}")
        
        return 0.0
    
    def _determine_unit_from_conditionnement(self, conditionnement, condition_label=None, api_unit=None, reference=None):
        """
        Détermine l'unité de mesure selon la logique suivante (dans l'ordre) :
        
        1. PRIORITÉ 1 - Unité API : Si l'API retourne une unité (PIECE, METRE, etc.)
           - PIECE / PCS / UNITE -> U
           - METRE / ML / M -> ML
           
        2. PRIORITÉ 2 - Table de correspondances : Vérifier rexel.unit.mapping
           - Correspondances personnalisables par l'utilisateur
           
        3. DÉFAUT : Si rien trouvé -> U + enregistrement dans conditionnements inconnus
        
        Args:
            conditionnement: Valeur du conditionnement (TOU, MET, PIE, etc.)
            condition_label: Label de condition supplémentaire
            api_unit: Unité retournée par l'API (PIECE, METRE, etc.)
            reference: Référence de l'article (pour le log des inconnus)
            
        Returns:
            tuple: (unite, error_message)
                - unite: 'ML' ou 'U'
                - error_message: None ou str avec le conditionnement problématique
        """
        # ========== PRIORITÉ 1 : Unité API ==========
        if api_unit:
            api_unit_upper = str(api_unit).strip().upper()
            
            # Conversion PIECE -> U
            if api_unit_upper in ('PIECE', 'PCS', 'UNITE', 'UNITÉ', 'U', 'UN', 'PCE'):
                _logger.debug(f"Unité API '{api_unit}' -> U")
                return ('U', None)
            
            # Conversion METRE -> ML
            if api_unit_upper in ('METRE', 'MÈTRE', 'ML', 'M', 'METER', 'METERS', 'METRES'):
                _logger.debug(f"Unité API '{api_unit}' -> ML")
                return ('ML', None)
            
            # Autre unité API connue
            if api_unit_upper in ('KG', 'KILOGRAMME'):
                _logger.debug(f"Unité API '{api_unit}' -> U (par défaut pour KG)")
                return ('U', None)
        
        # ========== PRIORITÉ 2 : Table de correspondances ==========
        cond_str = str(conditionnement or '').strip().upper()
        label_str = str(condition_label or '').strip().upper()
        
        if cond_str:
            # Chercher dans la table de correspondances
            UnitMapping = self.env['rexel.unit.mapping']
            
            # Recherche exacte sur le conditionnement
            mapping = UnitMapping.search([
                ('conditionnement', '=', cond_str),
                ('active', '=', True)
            ], limit=1)
            
            if mapping:
                mapping.increment_usage()
                _logger.debug(f"Correspondance trouvée: '{cond_str}' -> {mapping.unite}")
                return (mapping.unite, None)
            
            # Recherche partielle (le conditionnement contient le code)
            all_mappings = UnitMapping.search([('active', '=', True)], order='sequence')
            for m in all_mappings:
                if m.conditionnement in cond_str or m.conditionnement in label_str:
                    m.increment_usage()
                    _logger.debug(f"Correspondance partielle: '{cond_str}' contient '{m.conditionnement}' -> {m.unite}")
                    return (m.unite, None)
        
        # ========== PRIORITÉ 3 : Défaut ==========
        # Si conditionnement vide ou juste un chiffre -> U sans erreur
        if not cond_str or cond_str.isdigit():
            _logger.debug(f"Conditionnement vide ou numérique '{conditionnement}' -> U (défaut)")
            return ('U', None)
        
        # Conditionnement inconnu -> U + message d'erreur + enregistrement
        _logger.warning(f"Conditionnement inconnu '{conditionnement}' -> U (défaut) - À VÉRIFIER")
        
        # Enregistrer le conditionnement inconnu pour analyse ultérieure
        try:
            self.env['rexel.unknown.conditionnement'].sudo().log_unknown(cond_str, reference)
        except Exception as e:
            _logger.debug(f"Impossible d'enregistrer le conditionnement inconnu: {e}")
        
        return ('U', conditionnement)  # Retourne le conditionnement pour le message d'erreur
    
    def get_product_prices_from_api(self, articles):
        """
        Récupère les informations produits depuis l'API ProductPrice avec OAuth2
        
        Args:
            articles: recordset d'articles rexel.article
            
        Returns:
            dict: {article_id: {'found': True/False, 'prix_base': X, 'prix_net': Y, ...}}
        """
        self.ensure_one()
        
        if not self.api_enabled:
            raise UserError(_('L\'API n\'est pas activée.'))
        
        results = {}
        url = f"{self.api_base_url}/external/productprices/productSalePrices"
        
        # Construire la requête
        product_details = []
        article_map = {}  # Pour retrouver l'article par son index
        
        for idx, article in enumerate(articles):
            product_details.append({
                'supplierCode': article.trigramme_fabricant,
                'supplierComRef': article.reference_rexel or article.reference_fabricant,
                'orderingQty': 1
            })
            article_map[idx] = article
            # Initialiser comme non trouvé
            results[article.id] = {'found': False}
        
        request_data = {
            'getProductSalePricesExt': {
                'idCodOrigin': self.customer_scope,
                'idNumVersion': '1',
                'idCustomer': self.customer_id,
                'productDetails': product_details,
            }
        }
        
        # Obtenir les headers avec OAuth2
        headers = self._get_api_headers()
        
        try:
            response = requests.post(url, json=request_data, headers=headers, timeout=30)
            self.last_api_call = fields.Datetime.now()
            self.api_call_count += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # DEBUG: Logger la réponse complète pour analyse
                _logger.debug("=== RÉPONSE API productSalePrices ===")
                _logger.debug(f"Réponse brute: {data}")
                
                # Parser la réponse selon la structure de l'API Rexel
                if 'data' in data and 'productSalePricesExt' in data['data']:
                    product_details = data['data']['productSalePricesExt'].get('productDetails', [])
                    
                    # IMPORTANT: Si un seul produit, l'API retourne un dict au lieu d'une liste
                    if isinstance(product_details, dict):
                        product_list = [product_details]
                        _logger.debug("productDetails est un dict (1 seul produit) -> converti en liste")
                    elif isinstance(product_details, list):
                        product_list = product_details
                    else:
                        product_list = []
                        _logger.warning(f"productDetails type inattendu: {type(product_details)}")
                    
                    for idx, product_data in enumerate(product_list):
                        # DEBUG: Logger chaque produit
                        _logger.debug(f"Produit {idx}: {product_data}")
                        
                        if idx < len(articles):
                            article = article_map[idx]
                            
                            # Vérifier si le produit a été trouvé (a un prix ou une référence)
                            has_data = (
                                product_data.get('clientBasePrice') or 
                                product_data.get('clientNetPrice') or
                                product_data.get('rexelRef') or
                                product_data.get('itemLabel')
                            )
                            
                            if has_data:
                                # Essayer plusieurs noms de champs possibles pour l'unité
                                api_unit = (
                                    product_data.get('salesUnit') or
                                    product_data.get('uom') or
                                    product_data.get('unit') or
                                    product_data.get('unitOfMeasure') or
                                    product_data.get('sellingUnit') or
                                    product_data.get('orderUnit') or
                                    product_data.get('priceUnit') or
                                    product_data.get('baseUnit') or
                                    product_data.get('UOM') or
                                    product_data.get('UNIT') or
                                    product_data.get('unite') or
                                    product_data.get('uniteVente') or
                                    product_data.get('uniteCommande')
                                )
                                
                                # Essayer plusieurs noms pour le conditionnement depuis l'API
                                conditionnement_api = (
                                    product_data.get('packagingQuantity') or
                                    product_data.get('conditioningQuantity') or
                                    product_data.get('packageQty') or
                                    product_data.get('packQty') or
                                    product_data.get('quantityPerPack') or
                                    product_data.get('conditionnement') or
                                    product_data.get('colisage') or
                                    ''
                                )
                                
                                # Récupérer aussi le label de condition (peut contenir TOU, MET, etc.)
                                condition_label = product_data.get('conditionLabel') or ''
                                
                                # IMPORTANT: Si l'API ne retourne pas de conditionnement,
                                # utiliser celui déjà présent sur l'article
                                conditionnement_raw = conditionnement_api or article.conditionnement or ''
                                
                                _logger.info(f"Article {article.reference_fabricant}: conditionnement API='{conditionnement_api}', article='{article.conditionnement}' -> utilisé='{conditionnement_raw}'")
                                
                                # Utiliser la méthode centralisée pour déterminer l'unité
                                unite_finale, unit_error = self._determine_unit_from_conditionnement(
                                    conditionnement_raw, condition_label, api_unit
                                )
                                
                                if unit_error:
                                    _logger.warning(f"⚠️ Article {article.reference_fabricant}: conditionnement '{unit_error}' inconnu -> défaut U - À VÉRIFIER")
                                
                                _logger.info(f"Article {article.reference_fabricant}: unité API={api_unit}, conditionnement={conditionnement_raw}, conditionLabel={condition_label} -> unité finale={unite_finale}")
                                
                                # Calculer la remise (TOUJOURS depuis les prix, referenceRebate est un montant pas un %)
                                prix_base_val = float(product_data.get('clientBasePrice') or 0)
                                prix_net_val = float(product_data.get('clientNetPrice') or 0)
                                remise_calculee = self._calculate_remise(
                                    product_data.get('referenceRebate'),
                                    prix_base_val,
                                    prix_net_val
                                )
                                
                                _logger.debug(f"Article {article.reference_fabricant}: prix_base={prix_base_val}, prix_net={prix_net_val}, referenceRebate(montant)={product_data.get('referenceRebate')} -> remise_calculée={remise_calculee}%")
                                
                                results[article.id] = {
                                    'found': True,
                                    # Prix
                                    'prix_base': prix_base_val,
                                    'prix_net': prix_net_val,
                                    # Remise calculée (en %)
                                    'remise': remise_calculee,
                                    # Références
                                    'reference_rexel': product_data.get('rexelRef'),
                                    'designation': product_data.get('itemLabel'),
                                    # Unité de mesure (UOM) et conditionnement
                                    'unite_mesure': unite_finale,
                                    'conditionnement': conditionnement_raw if conditionnement_raw else None,
                                    'unit_error': unit_error,  # Conditionnement problématique si inconnu
                                    # Écotaxe D3E
                                    'montant_d3e': float(product_data.get('D3ECost') or 0) if product_data.get('hasD3E') == 'true' else 0,
                                    'unite_d3e': float(product_data.get('D3EQuantity') or 0) if product_data.get('hasD3E') == 'true' else 0,
                                    # Infos supplémentaires
                                    'condition_label': condition_label if condition_label else None,
                                    'price_label': product_data.get('priceLabel'),
                                    # DEBUG: Garder la réponse brute pour analyse
                                    '_raw_data': product_data,
                                }
                            else:
                                # Article non trouvé dans Rexel
                                results[article.id] = {
                                    'found': False,
                                    'error': 'Article non trouvé chez Rexel'
                                }
                                
                self.last_api_error = False
            else:
                error_msg = f"Erreur HTTP {response.status_code}: {response.text}"
                self.last_api_error = error_msg
                _logger.error(error_msg)
                
        except Exception as e:
            error_msg = str(e)
            self.last_api_error = error_msg
            _logger.error(f"Erreur lors de l'appel API: {error_msg}")
        
        return results

    def get_product_unit_from_api(self, supplier_code, supplier_ref):
        """
        Récupère l'unité de mesure depuis l'API Products/units
        Endpoint: GET /products/v2/units/{supplierCode}/{supplierComRef}
        
        Args:
            supplier_code: Trigramme fabricant (ex: LEG, SCH)
            supplier_ref: Référence commerciale du produit
            
        Returns:
            dict: {'unite': 'U', 'unite_api': 'PIECE', 'warning': None} ou None
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return None
        
        # Encoder les paramètres URL (certaines références contiennent des caractères spéciaux)
        import urllib.parse
        supplier_code_encoded = urllib.parse.quote(str(supplier_code), safe='')
        supplier_ref_encoded = urllib.parse.quote(str(supplier_ref), safe='')
        
        url = f"{self.api_base_url}/products/v2/units/{supplier_code_encoded}/{supplier_ref_encoded}"
        headers = self._get_api_headers()
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_unit_response(data, supplier_code, supplier_ref)
                    
            elif response.status_code == 400:
                # Produit non trouvé - normal pour certains produits
                return None
            else:
                _logger.warning(f"Unité non trouvée pour {supplier_code}/{supplier_ref}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            _logger.error(f"Erreur récupération unité {supplier_code}/{supplier_ref}: {str(e)}")
            return None

    def _parse_unit_response(self, data, supplier_code, supplier_ref):
        """Parse la réponse de l'API units"""
        elements = None
        
        # Extraire les éléments selon la structure
        if isinstance(data, dict):
            if 'elements' in data and isinstance(data['elements'], list) and len(data['elements']) > 0:
                elements = data['elements'][0]
            elif 'motUnite' in data:
                elements = data
        elif isinstance(data, list) and len(data) > 0:
            elements = data[0]
        
        if elements:
            # Extraire l'unité de l'API
            unite_api = elements.get('motUnite', '').upper().strip()
            
            # Correspondance des unités Rexel vers Odoo
            unite_odoo = 'U'
            warning = None
            
            if unite_api == 'PIECE':
                unite_odoo = 'U'
            elif unite_api == 'METRE':
                unite_odoo = 'ML'
            elif unite_api:
                unite_odoo = 'U'
                warning = f"Unité API '{unite_api}' non reconnue - vérifier"
            
            # Retourner TOUS les champs de l'API units
            return {
                # Champs de base
                'unite': unite_odoo,
                'unite_api': unite_api,
                'warning': warning,
                'supplier_code': supplier_code,
                'supplier_ref': supplier_ref,
                
                # Identification
                'codeInterneProduit': elements.get('codeInterneProduit'),
                'codeMotFabricant': elements.get('codeMotFabricant'),
                'referenceCommerciale': elements.get('referenceCommerciale'),
                'referenceRexel': elements.get('referenceRexel'),
                'codeEAN13': elements.get('codeEAN13'),
                'codeEANUnite': elements.get('codeEANUnite'),
                
                # Type et unité
                'typeConditionnement': elements.get('typeConditionnement'),
                'motUnite': elements.get('motUnite'),
                
                # Libellés
                'libelleLong': elements.get('libelleLong'),
                'libelleCourt': elements.get('libelleCourt'),
                'libelle': elements.get('libelle'),
                
                # Conversion
                'nombreConversionPrincipale': elements.get('nombreConversionPrincipale'),
                'flagUnitePrincipale': elements.get('flagUnitePrincipale'),
                'flagUnitePreparable': elements.get('flagUnitePreparable'),
                
                # Poids (en grammes)
                'poidsBrut': elements.get('poidsBrut'),
                'poidsNet': elements.get('poidsNet'),
                
                # Dimensions extérieures (en mm)
                'longueurExterieure': elements.get('longueurExterieure'),
                'largeurExterieure': elements.get('largeurExterieure'),
                'hauteurExterieure': elements.get('hauteurExterieure'),
                'volumeExterieur': elements.get('volumeExterieur'),
                
                # Dimensions intérieures (en mm)
                'longueurInterieure': elements.get('longueurInterieure'),
                'largeurInterieure': elements.get('largeurInterieure'),
                'hauteurInterieure': elements.get('hauteurInterieure'),
                'volumeInterieur': elements.get('volumeInterieur'),
            }
        return None

    def get_product_units_batch(self, products_list, max_workers=None):
        """
        Récupère les unités de mesure pour plusieurs produits en PARALLÈLE
        Respecte la limite de requêtes par seconde configurée.
        
        Args:
            products_list: Liste de tuples (supplier_code, supplier_ref)
                          ex: [('BE4', '91028'), ('SCH', '123456')]
            max_workers: Nombre de threads parallèles (si None, utilise rate_limit_per_second)
            
        Returns:
            dict: {(supplier_code, supplier_ref): unit_data, ...}
        """
        self.ensure_one()
        
        if not self.api_enabled or not products_list:
            return {}
        
        import concurrent.futures
        import urllib.parse
        import time
        
        results = {}
        headers = self._get_api_headers()
        base_url = self.api_base_url
        
        # Utiliser la limite de requêtes configurée comme nombre de workers
        if max_workers is None:
            if self.rate_limit_enabled:
                max_workers = self.rate_limit_per_second or 10
            else:
                max_workers = 10
        
        # Pour respecter le rate limit, on traite par lots
        rate_limit = self.rate_limit_per_second if self.rate_limit_enabled else 100
        
        def fetch_unit(product_tuple):
            """Fonction interne pour récupérer une unité"""
            supplier_code, supplier_ref = product_tuple
            try:
                supplier_code_encoded = urllib.parse.quote(str(supplier_code), safe='')
                supplier_ref_encoded = urllib.parse.quote(str(supplier_ref), safe='')
                url = f"{base_url}/products/v2/units/{supplier_code_encoded}/{supplier_ref_encoded}"
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return (product_tuple, self._parse_unit_response(data, supplier_code, supplier_ref))
                else:
                    return (product_tuple, None)
            except Exception as e:
                _logger.debug(f"Erreur batch unit {supplier_code}/{supplier_ref}: {e}")
                return (product_tuple, None)
        
        _logger.info(f"=== Récupération batch de {len(products_list)} unités ({max_workers} workers, {rate_limit} req/sec) ===")
        
        # Traiter par lots pour respecter le rate limit
        batch_size = rate_limit
        total_batches = (len(products_list) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, len(products_list))
            batch = products_list[batch_start:batch_end]
            
            batch_start_time = time.time()
            
            # Exécuter les requêtes du lot en parallèle
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(fetch_unit, p): p for p in batch}
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        product_tuple, unit_data = future.result()
                        if unit_data:
                            results[product_tuple] = unit_data
                    except Exception as e:
                        _logger.error(f"Erreur future: {e}")
            
            # Log de progression
            done_count = batch_end
            if done_count % 50 == 0 or done_count == len(products_list):
                _logger.info(f"Progression unités: {done_count}/{len(products_list)}")
            
            # Attendre si nécessaire pour respecter le rate limit (1 seconde entre chaque lot)
            if self.rate_limit_enabled and batch_num < total_batches - 1:
                elapsed = time.time() - batch_start_time
                if elapsed < 1.0:
                    wait_time = 1.0 - elapsed
                    time.sleep(wait_time)
        
        _logger.info(f"=== Batch terminé: {len(results)}/{len(products_list)} unités trouvées ===")
        return results

    # ==========================================================
    # ========== API STOCKS (Pack Découverte) ==================
    # ==========================================================
    
    def get_product_stocks(self, products_list, agence_code=None, zip_code=None):
        """
        Récupère les informations de stock pour une liste de produits
        URL: /external/stocks/positions
        Pack: Découverte et Premium
        
        Args:
            products_list: Liste de tuples (supplier_code, supplier_ref, quantity)
            agence_code: Code agence Rexel (optionnel)
            zip_code: Code postal de livraison (optionnel)
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return {}
        
        url = f"{self.api_base_url}/external/stocks/positions"
        headers = self._get_api_headers()
        
        # Construire le payload
        product_details = []
        for item in products_list:
            supplier_code, supplier_ref, qty = item if len(item) == 3 else (item[0], item[1], 1)
            product_details.append({
                'supplierCode': supplier_code,
                'supplierComRef': supplier_ref,
                'orderingQty': qty
            })
        
        payload = {
            'getPositionsExtRequest': {
                'idCustomer': self.customer_id,
                'productDetails': product_details
            }
        }
        
        if agence_code:
            payload['getPositionsExtRequest']['agenceCode'] = agence_code
        if zip_code:
            payload['getPositionsExtRequest']['zipCode'] = zip_code
        
        try:
            self._rate_limit_wait()
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_stocks_response(data)
            else:
                _logger.warning(f"API Stocks erreur {response.status_code}: {response.text[:200]}")
                return {}
        except Exception as e:
            _logger.error(f"Erreur API Stocks: {e}")
            return {}
    
    def _parse_stocks_response(self, data):
        """Parse la réponse de l'API stocks"""
        results = {}
        
        try:
            positions = data.get('data', {}).get('getPositionsExt', {})
            product_details = positions.get('productDetails', [])
            
            if not isinstance(product_details, list):
                product_details = [product_details] if product_details else []
            
            for product in product_details:
                supplier_code = product.get('supplierCode', '')
                supplier_ref = product.get('supplierComRef', '')
                key = (supplier_code, supplier_ref)
                
                results[key] = {
                    'rexelRef': product.get('rexelRef'),
                    'itemLabel': product.get('itemLabel'),
                    'availableBranchStock': product.get('availableBranchStock'),
                    'availableCLRStock': product.get('availableCLRStock'),
                    'availableServiceCenterStock': product.get('availableServiceCenterStock'),
                    'branchAvailabilityDelay': product.get('branchAvailabilityDelay'),
                    'DCAvailabilityDelay': product.get('DCAvailabilityDelay'),
                    'DCCode': product.get('DCCode'),
                    'branchMinimumQuantity': product.get('branchMinimumQuantity'),
                    'branchMultipleQuantity': product.get('branchMultipleQuantity'),
                    'DCMinimumQuantity': product.get('DCMinimumQuantity'),
                    'DCMultipleQuantity': product.get('DCMultipleQuantity'),
                    'deliveryDate': product.get('deliveryDate'),
                    'backOrderDeliveryDate': product.get('backOrderDeliveryDate'),
                    'cutOffDelivery': product.get('cutOffDelivery'),
                    'serviceCenterCode': product.get('serviceCenterCode'),
                }
        except Exception as e:
            _logger.error(f"Erreur parsing stocks: {e}")
        
        return results

    # ==========================================================
    # ========== API PRODUCTPRICE (Pack Découverte) ============
    # ==========================================================
    
    def get_product_prices(self, products_list, agence_code=None, zip_code=None):
        """
        Récupère les informations de prix pour une liste de produits
        URL: /external/productprices/productSalePrices
        Pack: Découverte et Premium
        
        Args:
            products_list: Liste de tuples (supplier_code, supplier_ref, quantity)
            agence_code: Code agence Rexel (optionnel)
            zip_code: Code postal de livraison (optionnel)
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return {}
        
        url = f"{self.api_base_url}/external/productprices/productSalePrices"
        headers = self._get_api_headers()
        
        # Construire le payload
        product_details = []
        for item in products_list:
            supplier_code, supplier_ref, qty = item if len(item) == 3 else (item[0], item[1], 1)
            product_details.append({
                'supplierCode': supplier_code,
                'supplierComRef': supplier_ref,
                'orderingQty': qty
            })
        
        payload = {
            'getProductSalePricesExt': {
                'idCustomer': self.customer_id,
                'productDetails': product_details
            }
        }
        
        if agence_code:
            payload['getProductSalePricesExt']['agenceCode'] = agence_code
        if zip_code:
            payload['getProductSalePricesExt']['zipCode'] = zip_code
        
        try:
            self._rate_limit_wait()
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_prices_response(data)
            else:
                _logger.warning(f"API Prices erreur {response.status_code}: {response.text[:200]}")
                return {}
        except Exception as e:
            _logger.error(f"Erreur API Prices: {e}")
            return {}
    
    def _parse_prices_response(self, data):
        """Parse la réponse de l'API productSalePrices"""
        results = {}
        
        try:
            prices_ext = data.get('data', {}).get('productSalePricesExt', {})
            product_details = prices_ext.get('productDetails', [])
            
            if not isinstance(product_details, list):
                product_details = [product_details] if product_details else []
            
            for product in product_details:
                supplier_code = product.get('supplierCode', '')
                supplier_ref = product.get('supplierComRef', '')
                key = (supplier_code, supplier_ref)
                
                results[key] = {
                    'idProduct': product.get('idProduct'),
                    'rexelRef': product.get('rexelRef'),
                    'itemLabel': product.get('itemLabel'),
                    'clientBasePrice': product.get('clientBasePrice'),
                    'clientNetPrice': product.get('clientNetPrice'),
                    'hasD3E': product.get('hasD3E'),
                    'D3EQuantity': product.get('D3EQuantity'),
                    'D3ECost': product.get('D3ECost'),
                    'salesAgreement': product.get('salesAgreement'),
                    'conditionLabel': product.get('conditionLabel'),
                    'referenceRebate': product.get('referenceRebate'),
                    'priceLabel': product.get('priceLabel'),
                }
        except Exception as e:
            _logger.error(f"Erreur parsing prices: {e}")
        
        return results

    # ==========================================================
    # ========== API REXEL-MEDIAS (Pack Premium) ===============
    # ==========================================================
    
    def get_product_image(self, supplier_code, supplier_ref):
        """
        Récupère l'image d'un produit
        URL: /rexel-medias/v1/full-image/commercialReference/{ref}/supplierCode/{code}
        Pack: Premium uniquement
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return None
        
        if self.api_pack != 'premium':
            _logger.info("API Images requiert le Pack Premium")
            return None
        
        import urllib.parse
        supplier_code_enc = urllib.parse.quote(str(supplier_code), safe='')
        supplier_ref_enc = urllib.parse.quote(str(supplier_ref), safe='')
        
        url = f"{self.api_base_url}/rexel-medias/v1/full-image/commercialReference/{supplier_ref_enc}/supplierCode/{supplier_code_enc}"
        headers = self._get_api_headers()
        
        try:
            self._rate_limit_wait()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Retourne le contenu binaire de l'image
                import base64
                return base64.b64encode(response.content)
            else:
                _logger.debug(f"Image non trouvée pour {supplier_code}/{supplier_ref}")
                return None
        except Exception as e:
            _logger.error(f"Erreur API Image: {e}")
            return None
    
    def get_technical_sheet_links(self, supplier_code, supplier_ref):
        """
        Récupère les liens vers les fiches techniques
        URL: /rexel-medias/v1/technical-sheets-links/commercialReference/{ref}/supplierCode/{code}
        Pack: Premium uniquement
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return None
        
        if self.api_pack != 'premium':
            _logger.info("API Fiches techniques requiert le Pack Premium")
            return None
        
        import urllib.parse
        supplier_code_enc = urllib.parse.quote(str(supplier_code), safe='')
        supplier_ref_enc = urllib.parse.quote(str(supplier_ref), safe='')
        
        url = f"{self.api_base_url}/rexel-medias/v1/technical-sheets-links/commercialReference/{supplier_ref_enc}/supplierCode/{supplier_code_enc}"
        headers = self._get_api_headers()
        
        try:
            self._rate_limit_wait()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                # Peut retourner une liste de fiches techniques
                if isinstance(data, list) and len(data) > 0:
                    return data[0]  # Retourne la première fiche
                return data
            else:
                return None
        except Exception as e:
            _logger.error(f"Erreur API Technical Sheets Links: {e}")
            return None

    # ==========================================================
    # ========== API PRODUCTCEE (Pack Premium) =================
    # ==========================================================
    
    def get_product_cee(self, supplier_code, supplier_ref):
        """
        Récupère les informations CEE (Certificat d'économie d'énergie) d'un produit
        URL: /products/v2/productCEE/{supplierCode}/{supplierComRef}
        Pack: Premium uniquement
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return None
        
        if self.api_pack != 'premium':
            _logger.info("API CEE requiert le Pack Premium")
            return None
        
        import urllib.parse
        supplier_code_enc = urllib.parse.quote(str(supplier_code), safe='')
        supplier_ref_enc = urllib.parse.quote(str(supplier_ref), safe='')
        
        url = f"{self.api_base_url}/products/v2/productCEE/{supplier_code_enc}/{supplier_ref_enc}"
        headers = self._get_api_headers()
        
        try:
            self._rate_limit_wait()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'codeInterneProduit': data.get('codeInterneProduit'),
                    'referenceRexel': data.get('referenceRexel'),
                    'idOperationCEE': data.get('idOperationCEE'),
                    'codeSecteurOperationCEE': data.get('codeSecteurOperationCEE'),
                    'codeSousSecteurOperationCEE': data.get('codeSousSecteurOperationCEE'),
                    'referenceOperationCEE': data.get('referenceOperationCEE'),
                    'referenceRexelOperationCEE': data.get('referenceRexelOperationCEE'),
                    'certificatCEE': data.get('certificatCEE'),
                    'urlFicheOperationCEE': data.get('urlFicheOperationCEE'),
                    'statutCEE': data.get('statutCEE'),
                    'flagEligibilitePrimexel': data.get('flagEligibilitePrimexel'),
                    'dateDebutValidite': data.get('dateDebutValidite'),
                    'dateFinValidite': data.get('dateFinValidite'),
                }
            else:
                return None
        except Exception as e:
            _logger.error(f"Erreur API CEE: {e}")
            return None

    # ==========================================================
    # ========== API PRODUCTENVIRONMENTALATTRIBUTES (Premium) ==
    # ==========================================================
    
    def get_product_environmental(self, supplier_code, supplier_ref):
        """
        Récupère l'éco-score d'un produit
        URL: /products/v2/productEnvironmentalAttributes/{supplierCode}/{supplierComRef}
        Pack: Premium uniquement
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return None
        
        if self.api_pack != 'premium':
            _logger.info("API Environmental requiert le Pack Premium")
            return None
        
        import urllib.parse
        supplier_code_enc = urllib.parse.quote(str(supplier_code), safe='')
        supplier_ref_enc = urllib.parse.quote(str(supplier_ref), safe='')
        
        url = f"{self.api_base_url}/products/v2/productEnvironmentalAttributes/{supplier_code_enc}/{supplier_ref_enc}"
        headers = self._get_api_headers()
        
        try:
            self._rate_limit_wait()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'codeInterneProduit': data.get('codeInterneProduit'),
                    'referenceRexel': data.get('referenceRexel'),
                    'noteEcoscore': data.get('noteEcoscore'),
                    'codeCritereEnvironemental': data.get('codeCritereEnvironemental'),
                }
            else:
                return None
        except Exception as e:
            _logger.error(f"Erreur API Environmental: {e}")
            return None

    # ==========================================================
    # ========== API PRODUCTREPLACEMENTLINKS (Premium) =========
    # ==========================================================
    
    def get_product_replacement(self, supplier_code, supplier_ref):
        """
        Récupère les produits de remplacement
        URL: /products/v2/productReplacementLinks/{supplierCode}/{supplierComRef}
        Pack: Premium uniquement
        """
        self.ensure_one()
        
        if not self.api_enabled:
            return None
        
        if self.api_pack != 'premium':
            _logger.info("API Replacement requiert le Pack Premium")
            return None
        
        import urllib.parse
        supplier_code_enc = urllib.parse.quote(str(supplier_code), safe='')
        supplier_ref_enc = urllib.parse.quote(str(supplier_ref), safe='')
        
        url = f"{self.api_base_url}/products/v2/productReplacementLinks/{supplier_code_enc}/{supplier_ref_enc}"
        headers = self._get_api_headers()
        
        try:
            self._rate_limit_wait()
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'codeInterneProduit': data.get('codeInterneProduit'),
                    'referenceRexel': data.get('referenceRexel'),
                    'sens': data.get('sens'),  # PAR ou DE
                    'codeInterneProduitRemplacement': data.get('codeInterneProduitRemplacement'),
                    'referenceRexelRemplacement': data.get('referenceRexelRemplacement'),
                    'dateDebutLien': data.get('dateDebutLien'),
                    'dateFinLien': data.get('dateFinLien'),
                    'datePeremption': data.get('datePeremption'),
                }
            else:
                return None
        except Exception as e:
            _logger.error(f"Erreur API Replacement: {e}")
            return None

    # ==========================================================
    # ========== MÉTHODES BATCH POUR TOUS LES APPELS ===========
    # ==========================================================
    
    def get_all_product_data_batch(self, products_list):
        """
        Récupère TOUTES les données disponibles pour une liste de produits
        en fonction du pack (Découverte ou Premium)
        
        Args:
            products_list: Liste de tuples (supplier_code, supplier_ref)
            
        Returns:
            dict: {(supplier_code, supplier_ref): {all_data}, ...}
        """
        self.ensure_one()
        
        if not self.api_enabled or not products_list:
            return {}
        
        import concurrent.futures
        import time
        
        results = {}
        headers = self._get_api_headers()
        
        # Initialiser les résultats
        for p in products_list:
            results[p] = {}
        
        # 1. Récupérer les UNITS (Découverte + Premium)
        _logger.info("=== Récupération des UNITS ===")
        units_data = self.get_product_units_batch(products_list)
        for key, data in units_data.items():
            if key in results:
                results[key]['units'] = data
        
        # 2. Récupérer les STOCKS (Découverte + Premium)
        _logger.info("=== Récupération des STOCKS ===")
        stocks_data = self.get_product_stocks([(p[0], p[1], 1) for p in products_list])
        for key, data in stocks_data.items():
            if key in results:
                results[key]['stocks'] = data
        
        # 3. Récupérer les PRIX (Découverte + Premium)
        _logger.info("=== Récupération des PRIX ===")
        prices_data = self.get_product_prices([(p[0], p[1], 1) for p in products_list])
        for key, data in prices_data.items():
            if key in results:
                results[key]['prices'] = data
        
        # 4. Si Pack Premium, récupérer les données supplémentaires
        if self.api_pack == 'premium':
            _logger.info("=== Pack Premium: Récupération des données supplémentaires ===")
            
            rate_limit = self.rate_limit_per_second if self.rate_limit_enabled else 20
            
            for i, (supplier_code, supplier_ref) in enumerate(products_list):
                key = (supplier_code, supplier_ref)
                
                # Rate limiting
                if self.rate_limit_enabled and i > 0 and i % rate_limit == 0:
                    time.sleep(1)
                
                # CEE
                cee_data = self.get_product_cee(supplier_code, supplier_ref)
                if cee_data:
                    results[key]['cee'] = cee_data
                
                # Environmental
                env_data = self.get_product_environmental(supplier_code, supplier_ref)
                if env_data:
                    results[key]['environmental'] = env_data
                
                # Replacement
                repl_data = self.get_product_replacement(supplier_code, supplier_ref)
                if repl_data:
                    results[key]['replacement'] = repl_data
                
                # Technical sheet links
                tech_data = self.get_technical_sheet_links(supplier_code, supplier_ref)
                if tech_data:
                    results[key]['technical'] = tech_data
                
                if (i + 1) % 50 == 0:
                    _logger.info(f"Progression Premium: {i + 1}/{len(products_list)}")
        
        return results
