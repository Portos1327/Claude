# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class ImportReferenceWizard(models.TransientModel):
    _name = 'import.reference.wizard'
    _description = 'Import rapide par référence Rexel'

    # Entrée
    reference_input = fields.Text(
        string='Références à importer',
        help="Entrez une ou plusieurs références Rexel (une par ligne).\n"
             "Format: TRIGRAMME REFERENCE ou juste REFERENCE_REXEL\n"
             "Exemples:\n"
             "  SCH APCRBCV202\n"
             "  LEG 406773\n"
             "  BE491028"
    )
    
    # Options
    create_families = fields.Boolean(
        string='Créer automatiquement les familles',
        default=True,
        help="Créer l'arborescence Famille/Sous-famille/Fonction si disponible"
    )
    update_existing = fields.Boolean(
        string='Mettre à jour les articles existants',
        default=True,
        help="Si un article existe déjà, mettre à jour ses informations"
    )
    fetch_units = fields.Boolean(
        string='Récupérer les unités de mesure',
        default=True,
        help="Appeler l'API units pour récupérer l'unité de mesure"
    )
    
    # Résultat
    state = fields.Selection([
        ('draft', 'Saisie'),
        ('done', 'Terminé')
    ], default='draft')
    
    result_log = fields.Text(string='Journal d\'import', readonly=True)
    articles_created = fields.Integer(string='Articles créés', readonly=True)
    articles_updated = fields.Integer(string='Articles mis à jour', readonly=True)
    articles_errors = fields.Integer(string='Erreurs', readonly=True)

    def action_import(self):
        """Importer les références via l'API"""
        self.ensure_one()
        
        _logger.info("="*60)
        _logger.info("=== DÉBUT IMPORT PAR RÉFÉRENCE ===")
        _logger.info(f"reference_input: {self.reference_input}")
        _logger.info(f"update_existing: {self.update_existing}")
        _logger.info(f"fetch_units: {self.fetch_units}")
        _logger.info("="*60)
        
        if not self.reference_input:
            raise UserError(_("Veuillez entrer au moins une référence."))
        
        # Vérifier la configuration API
        config = self.env['rexel.config'].search([('api_enabled', '=', True)], limit=1)
        _logger.info(f"Config API trouvée: {config.id if config else 'AUCUNE'}")
        
        if not config:
            raise UserError(_("Aucune configuration API active. "
                            "Veuillez configurer l'API dans Configuration > Configuration Rexel."))
        
        # Parser les références
        references = self._parse_references(self.reference_input)
        _logger.info(f"Références parsées: {references}")
        
        if not references:
            raise UserError(_("Aucune référence valide trouvée."))
        
        # Importer les articles
        log_messages = []
        created = 0
        updated = 0
        errors = 0
        warnings = 0
        
        for ref_data in references:
            try:
                result = self._import_single_reference(config, ref_data)
                if result['status'] == 'created':
                    created += 1
                    msg = f"✓ {ref_data['display']}: Article créé"
                    if result.get('warning'):
                        msg += f" ⚠️ {result['warning']}"
                        warnings += 1
                    log_messages.append(msg)
                elif result['status'] == 'updated':
                    updated += 1
                    msg = f"↻ {ref_data['display']}: Article mis à jour"
                    if result.get('warning'):
                        msg += f" ⚠️ {result['warning']}"
                        warnings += 1
                    log_messages.append(msg)
                elif result['status'] == 'exists':
                    log_messages.append(f"○ {ref_data['display']}: Article existant (non modifié)")
                else:
                    errors += 1
                    log_messages.append(f"✗ {ref_data['display']}: {result.get('error', 'Erreur inconnue')}")
            except Exception as e:
                errors += 1
                log_messages.append(f"✗ {ref_data['display']}: {str(e)}")
                _logger.error(f"Erreur import référence {ref_data}: {e}")
        
        # Résumé
        log_messages.append("")
        log_messages.append("=" * 40)
        log_messages.append(f"✓ Articles créés: {created}")
        log_messages.append(f"↻ Articles mis à jour: {updated}")
        if warnings > 0:
            log_messages.append(f"⚠️ Unités à vérifier: {warnings}")
        log_messages.append(f"✗ Erreurs: {errors}")
        
        # Note sur les correspondances d'unités
        log_messages.append("")
        log_messages.append("📏 Correspondance unités: PIECE → U, METRE → ML")
        
        self.write({
            'state': 'done',
            'result_log': '\n'.join(log_messages),
            'articles_created': created,
            'articles_updated': updated,
            'articles_errors': errors
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'import.reference.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _parse_references(self, text):
        """Parser le texte d'entrée pour extraire les références"""
        references = []
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split()
            if len(parts) >= 2:
                # Format: TRIGRAMME REFERENCE
                trigramme = parts[0].upper()
                reference = ' '.join(parts[1:])  # Au cas où la référence contient des espaces
                references.append({
                    'trigramme': trigramme,
                    'reference': reference,
                    'display': f"{trigramme} {reference}"
                })
            elif len(parts) == 1:
                # Format: REFERENCE_REXEL seule (ex: BE491028)
                ref = parts[0].upper()
                # Essayer de détecter le trigramme (3 premières lettres si alphabétiques)
                if len(ref) >= 3 and ref[:3].isalpha():
                    trigramme = ref[:3]
                    reference = ref[3:] if len(ref) > 3 else ref
                    references.append({
                        'trigramme': trigramme,
                        'reference': reference,
                        'reference_rexel': ref,
                        'display': ref
                    })
                else:
                    references.append({
                        'trigramme': None,
                        'reference': ref,
                        'display': ref
                    })
        
        return references

    def _import_single_reference(self, config, ref_data):
        """Importer une seule référence"""
        Article = self.env['rexel.article']
        
        trigramme = ref_data.get('trigramme')
        reference = ref_data.get('reference')
        reference_rexel = ref_data.get('reference_rexel')
        
        _logger.info(f"=== Import référence: trigramme={trigramme}, reference={reference}, reference_rexel={reference_rexel} ===")
        
        # Vérifier si l'article existe déjà
        domain = []
        if reference_rexel:
            domain = [('reference_rexel', '=', reference_rexel)]
        elif trigramme and reference:
            domain = [
                ('trigramme_fabricant', '=', trigramme),
                '|',
                ('reference_fabricant', '=', reference),
                ('reference_rexel', '=', f"{trigramme}{reference}")
            ]
        else:
            domain = [('reference_fabricant', '=', reference)]
        
        _logger.info(f"Recherche article existant avec domain: {domain}")
        existing = Article.search(domain, limit=1)
        _logger.info(f"Article existant trouvé: {existing.id if existing else 'Non'}")
        
        if existing and not self.update_existing:
            _logger.info(f"Article existant et update_existing=False, skip API")
            return {'status': 'exists', 'article': existing}
        
        # Appeler l'API productSalePrices pour récupérer les infos
        if not trigramme:
            return {'status': 'error', 'error': 'Trigramme fabricant requis'}
        
        # Construire la requête API
        product_data = self._fetch_product_from_api(config, trigramme, reference or reference_rexel)
        
        if not product_data:
            return {'status': 'error', 'error': f'Produit non trouvé dans l\'API Rexel (vérifiez {trigramme}/{reference or reference_rexel})'}
        
        # Récupérer les unités si demandé
        unit_data = None
        unit_warning = None
        if self.fetch_units:
            # Essayer avec la référence commerciale (sans trigramme)
            ref_for_units = reference or (reference_rexel[len(trigramme):] if reference_rexel and trigramme else None)
            if ref_for_units:
                unit_data = config.get_product_unit_from_api(trigramme, ref_for_units)
                if unit_data and unit_data.get('warning'):
                    unit_warning = unit_data['warning']
        
        # Préparer les valeurs de base depuis productSalePrices
        prix_base = float(product_data.get('clientBasePrice') or 0)
        prix_net = float(product_data.get('clientNetPrice') or 0)
        
        # Calculer la remise correctement (referenceRebate est un MONTANT, pas un %)
        remise = config._calculate_remise(
            product_data.get('referenceRebate'),
            prix_base,
            prix_net
        )
        
        # Récupérer le conditionnement et l'unité API
        conditionnement_raw = (
            product_data.get('packagingQuantity') or
            product_data.get('conditioningQuantity') or
            product_data.get('packageQty') or
            ''
        )
        condition_label = product_data.get('conditionLabel') or ''
        
        # Récupérer l'unité depuis l'API productSalePrices
        api_unit_from_prices = (
            product_data.get('salesUnit') or
            product_data.get('uom') or
            product_data.get('unit') or
            None
        )
        
        # Déterminer l'unité avec la méthode centralisée
        # Priorité: 1. Unité API (PIECE->U, METRE->ML)  2. Conditionnement (TOU->ML)  3. Défaut U
        unite_finale, unit_error = config._determine_unit_from_conditionnement(
            conditionnement_raw, condition_label, api_unit_from_prices
        )
        if unit_error:
            _logger.warning(f"⚠️ Import {trigramme}/{reference}: conditionnement '{unit_error}' inconnu -> défaut U - À VÉRIFIER")
        
        vals = {
            'reference_fabricant': reference or reference_rexel,
            'trigramme_fabricant': trigramme,
            'reference_rexel': product_data.get('rexelRef') or reference_rexel or f"{trigramme}{reference}",
            'designation': product_data.get('itemLabel', ''),
            'prix_base': prix_base,
            'prix_net': prix_net,
            'remise': remise,
            'unite_mesure': unite_finale,
            'conditionnement': conditionnement_raw if conditionnement_raw else None,
            'montant_d3e': float(product_data.get('D3ECost') or 0) if product_data.get('hasD3E') == 'true' else 0,
            'unite_d3e': float(product_data.get('D3EQuantity') or 0) if product_data.get('hasD3E') == 'true' else 0,
            'last_api_update': fields.Datetime.now(),
            'import_source': 'api',
        }
        
        # Extraire le code interne produit (idProduct) si disponible
        if product_data.get('idProduct'):
            vals['code_lidic_and_ref'] = product_data.get('idProduct')
        
        # Ajouter les informations de l'API units si disponibles
        if unit_data:
            # Récupérer d'abord les infos de l'API units
            api_unit = unit_data.get('unite')
            if unit_data.get('codeEAN13'):
                vals['code_ean13'] = unit_data['codeEAN13']
            if unit_data.get('typeConditionnement'):
                vals['conditionnement'] = unit_data['typeConditionnement']
                # Réappliquer la logique d'unité avec le nouveau conditionnement
                new_unite, _ = config._determine_unit_from_conditionnement(
                    unit_data['typeConditionnement'], condition_label, api_unit
                )
                vals['unite_mesure'] = new_unite
            elif api_unit:
                # Pas de nouveau conditionnement mais une unité API
                new_unite, _ = config._determine_unit_from_conditionnement(
                    conditionnement_raw, condition_label, api_unit
                )
                vals['unite_mesure'] = new_unite
            # Le libellé long de l'API units peut être plus complet
            if unit_data.get('libelleLong') and len(unit_data.get('libelleLong', '')) > len(vals.get('designation', '')):
                vals['designation'] = unit_data['libelleLong']
            # Nom du fabricant depuis l'API units
            if unit_data.get('codeMotFabricant'):
                vals['trigramme_fabricant'] = unit_data['codeMotFabricant']
        
        _logger.info(f"Valeurs préparées pour création/mise à jour: {vals}")
        
        if existing:
            existing.write(vals)
            return {'status': 'updated', 'article': existing, 'warning': unit_warning}
        else:
            article = Article.create(vals)
            return {'status': 'created', 'article': article, 'warning': unit_warning}

    def _fetch_product_from_api(self, config, trigramme, reference):
        """Appeler l'API productSalePrices pour un seul produit
        
        Args:
            config: configuration rexel.config
            trigramme: code fabricant (ex: NDX, BE4, SCH)
            reference: référence produit (peut être avec ou sans trigramme)
        """
        import requests
        
        _logger.info(f"=== _fetch_product_from_api appelé ===")
        _logger.info(f"trigramme reçu: '{trigramme}'")
        _logger.info(f"reference reçue: '{reference}'")
        
        # Vérifier que le token est valide
        if not config.access_token:
            _logger.info("Pas de token d'accès - tentative d'obtention")
            config._get_access_token()
            if not config.access_token:
                _logger.error("Impossible d'obtenir un token d'accès")
                return None
        
        url = f"{config.api_base_url}/external/productprices/productSalePrices"
        headers = config._get_api_headers()
        
        # Construire la référence Rexel complète (ex: NDX711277)
        # Si la référence commence déjà par le trigramme, on la garde telle quelle
        # Sinon on préfixe avec le trigramme
        if trigramme and reference:
            if reference.upper().startswith(trigramme.upper()):
                reference_rexel = reference.upper()
            else:
                reference_rexel = f"{trigramme.upper()}{reference}"
        else:
            reference_rexel = reference or ''
        
        _logger.info(f"reference_rexel construite: '{reference_rexel}'")
        
        request_data = {
            'getProductSalePricesExt': {
                'idCodOrigin': config.customer_scope,
                'idNumVersion': '1',
                'idCustomer': config.customer_id,
                'productDetails': [{
                    'supplierCode': trigramme,
                    'supplierComRef': reference_rexel,
                    'orderingQty': 1
                }],
            }
        }
        
        _logger.info(f"=== Appel API productSalePrices ===")
        _logger.info(f"URL: {url}")
        _logger.info(f"supplierCode: {trigramme}")
        _logger.info(f"supplierComRef: {reference_rexel}")
        _logger.info(f"Request data complet: {request_data}")
        
        try:
            response = requests.post(url, json=request_data, headers=headers, timeout=30)
            
            _logger.info(f"Réponse HTTP: {response.status_code}")
            _logger.info(f"Réponse brute (500 premiers chars): {response.text[:500]}")
            
            if response.status_code == 200:
                data = response.json()
                _logger.info(f"Réponse JSON parsée: {data}")
                
                if 'data' in data and 'productSalePricesExt' in data['data']:
                    product_details = data['data']['productSalePricesExt'].get('productDetails', [])
                    
                    # L'API peut retourner soit une liste, soit un dict unique
                    if isinstance(product_details, dict):
                        # Un seul produit retourné comme dict
                        products = [product_details]
                        _logger.info(f"productDetails est un dict - converti en liste")
                    else:
                        products = product_details
                    
                    _logger.info(f"Nombre de produits dans la réponse: {len(products)}")
                    
                    if products:
                        product = products[0]
                        _logger.info(f"Premier produit: {product}")
                        
                        # Vérifier si le produit a été trouvé (a un prix ou une référence)
                        has_data = (
                            product.get('clientBasePrice') or 
                            product.get('clientNetPrice') or
                            product.get('rexelRef') or 
                            product.get('itemLabel')
                        )
                        
                        if has_data:
                            _logger.info(f"✓ Produit trouvé: {product.get('rexelRef')} - {product.get('itemLabel')}")
                            return product
                        else:
                            _logger.warning(f"✗ Produit retourné mais sans données: {product}")
                    else:
                        _logger.warning(f"✗ Liste productDetails vide")
                else:
                    _logger.warning(f"✗ Structure de réponse inattendue - clés présentes: {data.keys() if isinstance(data, dict) else 'pas un dict'}")
                    
            elif response.status_code == 401:
                _logger.error("Token expiré (401) - tentative de rafraîchissement")
                config._get_access_token()
                headers = config._get_api_headers()
                response = requests.post(url, json=request_data, headers=headers, timeout=30)
                _logger.info(f"Retry - Réponse HTTP: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    if 'data' in data and 'productSalePricesExt' in data['data']:
                        products = data['data']['productSalePricesExt'].get('productDetails', [])
                        if products:
                            return products[0]
            else:
                _logger.error(f"Erreur HTTP {response.status_code}: {response.text[:500]}")
            
            return None
            
        except requests.exceptions.Timeout:
            _logger.error(f"Timeout lors de l'appel API pour {trigramme}/{reference}")
            return None
        except requests.exceptions.ConnectionError as e:
            _logger.error(f"Erreur de connexion API pour {trigramme}/{reference}: {e}")
            return None
        except Exception as e:
            _logger.error(f"Erreur API productSalePrices pour {trigramme}/{reference}: {type(e).__name__}: {e}")
            return None
            
            return None
        except requests.exceptions.Timeout:
            _logger.error(f"Timeout lors de l'appel API pour {trigramme}/{reference}")
            return None
        except requests.exceptions.ConnectionError as e:
            _logger.error(f"Erreur de connexion API pour {trigramme}/{reference}: {e}")
            return None
        except Exception as e:
            _logger.error(f"Erreur API productSalePrices pour {trigramme}/{reference}: {type(e).__name__}: {e}")
            return None

    def action_back(self):
        """Retour à la saisie"""
        self.write({
            'state': 'draft',
            'result_log': False,
            'articles_created': 0,
            'articles_updated': 0,
            'articles_errors': 0
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'import.reference.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_articles(self):
        """Voir les articles importés"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Articles importés',
            'res_model': 'rexel.article',
            'view_mode': 'list,form',
            'target': 'current',
        }
