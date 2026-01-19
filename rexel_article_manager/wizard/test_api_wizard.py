# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json
import logging
import urllib.parse

_logger = logging.getLogger(__name__)

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TestApiWizard(models.TransientModel):
    _name = 'test.api.wizard'
    _description = 'Test API Rexel - Visualisation données brutes'

    # Entrée
    trigramme = fields.Char(
        string='Trigramme fabricant',
        required=True,
        help='Code 3 lettres du fabricant (ex: LEG, SCH, BE4)'
    )
    
    reference_fabricant = fields.Char(
        string='Référence fabricant',
        required=True,
        help='Référence du produit chez le fabricant (ex: 600391A, 13201)'
    )
    
    # APIs à tester - Pack Découverte
    test_prices = fields.Boolean(string='💰 Prix (productSalePrices)', default=True,
        help='Pack Découverte - Prix de vente client')
    test_units = fields.Boolean(string='📦 Unités (units)', default=True,
        help='Pack Découverte - Unités et conditionnement')
    test_stocks = fields.Boolean(string='📊 Stocks (positions)', default=False,
        help='Pack Découverte - Disponibilité stock')
    
    # APIs Premium
    test_images = fields.Boolean(string='🖼️ Images (full-image)', default=False,
        help='Pack Premium - URL images produit')
    test_fiches = fields.Boolean(string='📄 Fiches techniques', default=False,
        help='Pack Premium - Liens fiches techniques')
    test_cee = fields.Boolean(string='🌿 CEE (éco-énergie)', default=False,
        help='Pack Premium - Certificats économies énergie')
    test_env = fields.Boolean(string='♻️ Attributs environnementaux', default=False,
        help='Pack Premium - Attributs développement durable')
    test_replacement = fields.Boolean(string='🔄 Remplacements', default=False,
        help='Pack Premium - Produits de remplacement')
    
    # Résultats
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('done', 'Résultats')
    ], default='draft')
    
    result_prices = fields.Text(string='Résultat API Prix', readonly=True)
    result_units = fields.Text(string='Résultat API Unités', readonly=True)
    result_stocks = fields.Text(string='Résultat API Stocks', readonly=True)
    result_images = fields.Text(string='Résultat API Images', readonly=True)
    result_fiches = fields.Text(string='Résultat API Fiches', readonly=True)
    result_cee = fields.Text(string='Résultat API CEE', readonly=True)
    result_env = fields.Text(string='Résultat API Environnement', readonly=True)
    result_replacement = fields.Text(string='Résultat API Remplacements', readonly=True)
    
    result_unite_calculee = fields.Char(string='Unité calculée', readonly=True)
    result_unite_explication = fields.Text(string='Explication du calcul', readonly=True)

    def action_test_api(self):
        """Lancer le test de l'API"""
        self.ensure_one()
        
        if not REQUESTS_AVAILABLE:
            raise UserError(_("La bibliothèque 'requests' n'est pas installée."))
        
        config = self.env['rexel.config'].get_config()
        if not config.api_enabled:
            raise UserError(_('L\'API Rexel n\'est pas activée dans la configuration.'))
        
        trigramme = self.trigramme.strip().upper()
        ref_fab = self.reference_fabricant.strip()
        
        if not trigramme or not ref_fab:
            raise UserError(_('Veuillez saisir le trigramme et la référence fabricant.'))
        
        # Encoder pour les URLs
        trigramme_enc = urllib.parse.quote(trigramme, safe='')
        ref_fab_enc = urllib.parse.quote(ref_fab, safe='')
        
        results = {
            'result_prices': '',
            'result_units': '',
            'result_stocks': '',
            'result_images': '',
            'result_fiches': '',
            'result_cee': '',
            'result_env': '',
            'result_replacement': '',
            'result_unite_calculee': '',
            'result_unite_explication': '',
        }
        
        # Headers avec subscription key
        headers = config._get_api_headers()
        if not headers.get('Authorization'):
            raise UserError(_("Impossible d'obtenir un token d'authentification. Vérifiez la configuration API."))
        
        # Variables pour le calcul d'unité
        api_data_for_unit = {}
        
        # ========== API PRIX (Pack Découverte) ==========
        if self.test_prices:
            try:
                url = f"{config.api_base_url}/external/productprices/productSalePrices"
                payload = {
                    'getProductSalePricesExt': {
                        'idCustomer': config.customer_id,
                        'productDetails': [{
                            'supplierCode': trigramme,
                            'supplierComRef': ref_fab,
                            'orderingQty': 1
                        }]
                    }
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                results['result_prices'] = self._format_api_response(
                    'productSalePrices (POST) - Pack Découverte',
                    response.status_code, response.text, payload
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        prices_ext = data.get('data', {}).get('productSalePricesExt', {})
                        product_details = prices_ext.get('productDetails', [])
                        if isinstance(product_details, dict):
                            product_details = [product_details]
                        if product_details:
                            api_data_for_unit = product_details[0]
                    except:
                        pass
            except Exception as e:
                results['result_prices'] = f"❌ Erreur: {str(e)}"
        
        # ========== API UNITÉS (Pack Découverte) ==========
        if self.test_units:
            try:
                url = f"{config.api_base_url}/products/v2/units/{trigramme_enc}/{ref_fab_enc}"
                response = requests.get(url, headers=headers, timeout=30)
                results['result_units'] = self._format_api_response(
                    f'units (GET) - Pack Découverte\nURL: {url}',
                    response.status_code, response.text, {'supplierCode': trigramme, 'supplierComRef': ref_fab}
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if isinstance(data, list) and data:
                            api_data_for_unit.update(data[0])
                        elif isinstance(data, dict):
                            api_data_for_unit.update(data)
                    except:
                        pass
            except Exception as e:
                results['result_units'] = f"❌ Erreur: {str(e)}"
        
        # ========== API STOCKS (Pack Découverte) ==========
        if self.test_stocks:
            try:
                url = f"{config.api_base_url}/external/stocks/positions"
                payload = {
                    'getStockPositions': {
                        'idCustomer': config.customer_id,
                        'productDetails': [{
                            'supplierCode': trigramme,
                            'supplierComRef': ref_fab,
                        }]
                    }
                }
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                results['result_stocks'] = self._format_api_response(
                    'stocks/positions (POST) - Pack Découverte',
                    response.status_code, response.text, payload
                )
            except Exception as e:
                results['result_stocks'] = f"❌ Erreur: {str(e)}"
        
        # ========== API IMAGES (Pack Premium) ==========
        if self.test_images:
            try:
                url = f"{config.api_base_url}/rexel-medias/v1/full-image/commercialReference/{ref_fab_enc}/supplierCode/{trigramme_enc}"
                response = requests.get(url, headers=headers, timeout=30)
                results['result_images'] = self._format_api_response(
                    f'full-image (GET) - Pack Premium\nURL: {url}',
                    response.status_code, response.text, {'supplierCode': trigramme, 'commercialReference': ref_fab}
                )
            except Exception as e:
                results['result_images'] = f"❌ Erreur: {str(e)}"
        
        # ========== API FICHES TECHNIQUES (Pack Premium) ==========
        if self.test_fiches:
            try:
                url = f"{config.api_base_url}/rexel-medias/v1/technical-sheets-links/commercialReference/{ref_fab_enc}/supplierCode/{trigramme_enc}"
                response = requests.get(url, headers=headers, timeout=30)
                results['result_fiches'] = self._format_api_response(
                    f'technical-sheets-links (GET) - Pack Premium\nURL: {url}',
                    response.status_code, response.text, {'supplierCode': trigramme, 'commercialReference': ref_fab}
                )
            except Exception as e:
                results['result_fiches'] = f"❌ Erreur: {str(e)}"
        
        # ========== API CEE (Pack Premium) ==========
        if self.test_cee:
            try:
                url = f"{config.api_base_url}/products/v2/productCEE/{trigramme_enc}/{ref_fab_enc}"
                response = requests.get(url, headers=headers, timeout=30)
                results['result_cee'] = self._format_api_response(
                    f'productCEE (GET) - Pack Premium\nURL: {url}',
                    response.status_code, response.text, {'supplierCode': trigramme, 'supplierComRef': ref_fab}
                )
            except Exception as e:
                results['result_cee'] = f"❌ Erreur: {str(e)}"
        
        # ========== API ENVIRONNEMENT (Pack Premium) ==========
        if self.test_env:
            try:
                url = f"{config.api_base_url}/products/v2/productEnvironmentalAttributes/{trigramme_enc}/{ref_fab_enc}"
                response = requests.get(url, headers=headers, timeout=30)
                results['result_env'] = self._format_api_response(
                    f'productEnvironmentalAttributes (GET) - Pack Premium\nURL: {url}',
                    response.status_code, response.text, {'supplierCode': trigramme, 'supplierComRef': ref_fab}
                )
            except Exception as e:
                results['result_env'] = f"❌ Erreur: {str(e)}"
        
        # ========== API REMPLACEMENTS (Pack Premium) ==========
        if self.test_replacement:
            try:
                url = f"{config.api_base_url}/products/v2/productReplacementLinks/{trigramme_enc}/{ref_fab_enc}"
                response = requests.get(url, headers=headers, timeout=30)
                results['result_replacement'] = self._format_api_response(
                    f'productReplacementLinks (GET) - Pack Premium\nURL: {url}',
                    response.status_code, response.text, {'supplierCode': trigramme, 'supplierComRef': ref_fab}
                )
            except Exception as e:
                results['result_replacement'] = f"❌ Erreur: {str(e)}"
        
        # ========== CALCUL DE L'UNITÉ ==========
        if api_data_for_unit:
            self._calculate_unit_explanation(config, api_data_for_unit, results)
        
        # Mettre à jour le wizard
        results['state'] = 'done'
        self.write(results)
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'test.api.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _format_api_response(self, api_name, status_code, response_text, request_data):
        """Formate la réponse API pour affichage"""
        output = []
        output.append(f"{'='*60}")
        output.append(f"API: {api_name}")
        output.append(f"{'='*60}")
        output.append(f"")
        output.append(f"📤 REQUÊTE:")
        output.append(json.dumps(request_data, indent=2, ensure_ascii=False))
        output.append(f"")
        
        # Status avec emoji
        if status_code == 200:
            status_emoji = "✅"
        elif status_code == 401:
            status_emoji = "🔐"
        elif status_code == 404:
            status_emoji = "❓"
        else:
            status_emoji = "❌"
        
        output.append(f"📥 RÉPONSE: {status_emoji} Status {status_code}")
        output.append(f"")
        
        # Parser et formater le JSON
        try:
            data = json.loads(response_text)
            formatted_json = json.dumps(data, indent=2, ensure_ascii=False)
            output.append(formatted_json)
        except:
            output.append(response_text[:3000])
            if len(response_text) > 3000:
                output.append(f"... (tronqué, {len(response_text)} caractères au total)")
        
        return '\n'.join(output)

    def _calculate_unit_explanation(self, config, api_data, results):
        """Calcule l'unité et explique le raisonnement"""
        explanation = []
        explanation.append("="*60)
        explanation.append("CALCUL DE L'UNITÉ DE MESURE")
        explanation.append("="*60)
        explanation.append("")
        
        # Étape 1: Unité API
        api_unit = (
            api_data.get('salesUnit') or
            api_data.get('uom') or
            api_data.get('unit') or
            api_data.get('motUnite') or
            None
        )
        explanation.append("ÉTAPE 1 - Unité API:")
        explanation.append(f"   salesUnit: {api_data.get('salesUnit')}")
        explanation.append(f"   uom: {api_data.get('uom')}")
        explanation.append(f"   unit: {api_data.get('unit')}")
        explanation.append(f"   motUnite: {api_data.get('motUnite')}")
        explanation.append(f"   → Unité API retenue: {api_unit or '(aucune)'}")
        explanation.append("")
        
        # Étape 2: Conditionnement
        conditionnement = (
            api_data.get('packagingType') or
            api_data.get('packagingQuantity') or
            api_data.get('typeConditionnement') or
            api_data.get('conditioningQuantity') or
            ''
        )
        condition_label = api_data.get('conditionLabel') or ''
        
        explanation.append("ÉTAPE 2 - Conditionnement:")
        explanation.append(f"   packagingType: {api_data.get('packagingType')}")
        explanation.append(f"   packagingQuantity: {api_data.get('packagingQuantity')}")
        explanation.append(f"   typeConditionnement: {api_data.get('typeConditionnement')}")
        explanation.append(f"   conditionLabel: {api_data.get('conditionLabel')}")
        explanation.append(f"   → Conditionnement retenu: {conditionnement or '(aucun)'}")
        explanation.append("")
        
        # Étape 3: Calcul avec la méthode centralisée
        unite_finale, unit_error = config._determine_unit_from_conditionnement(
            conditionnement, condition_label, api_unit
        )
        
        explanation.append("ÉTAPE 3 - Résultat:")
        explanation.append(f"   → UNITÉ CALCULÉE: {unite_finale}")
        if unit_error:
            explanation.append(f"   ⚠️ Conditionnement inconnu: {unit_error}")
            explanation.append(f"   → Défaut U appliqué")
        explanation.append("")
        
        # Règles appliquées
        explanation.append("─"*60)
        explanation.append("RÈGLES DE CONVERSION:")
        explanation.append("─"*60)
        explanation.append("   Priorité 1 - Unité API:")
        explanation.append("      PIECE/PCS/UNITE → U")
        explanation.append("      METRE/ML/M → ML")
        explanation.append("   Priorité 2 - Conditionnement:")
        explanation.append("      TOU/TOURET → ML")
        explanation.append("      MET/METRE → ML")
        explanation.append("      PIE/PIECE/PCS → U")
        explanation.append("      BOI/LOT/PAQ/SAC → U")
        explanation.append("   Priorité 3 - Défaut: U")
        
        results['result_unite_calculee'] = unite_finale
        results['result_unite_explication'] = '\n'.join(explanation)

    def action_back(self):
        """Retour à la configuration"""
        self.write({
            'state': 'draft',
            'result_prices': False,
            'result_units': False,
            'result_stocks': False,
            'result_images': False,
            'result_fiches': False,
            'result_cee': False,
            'result_env': False,
            'result_replacement': False,
            'result_unite_calculee': False,
            'result_unite_explication': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'test.api.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
