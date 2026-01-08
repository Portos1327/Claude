# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class RexelArticle(models.Model):
    _name = 'rexel.article'
    _description = 'Article Rexel Cloud'
    _order = 'famille_libelle, sous_famille_libelle, fonction_libelle, fabricant_libelle, reference_fabricant'
    _rec_name = 'reference_fabricant'

    # ========== IDENTIFICATION ARTICLE ==========
    reference_fabricant = fields.Char(
        string='Référence fabricant',
        required=True,
        index=True,
        help='REF - Référence fabricant de l\'article'
    )
    
    reference_rexel = fields.Char(
        string='Référence commerciale Rexel',
        index=True,
        help='REF_REXEL - Référence commerciale Rexel de l\'article'
    )
    
    code_lidic_and_ref = fields.Char(
        string='Référence Rexel complète',
        index=True,
        help='CODE_LIDIC_AND_REF - Trigramme + référence fabricant'
    )
    
    designation = fields.Text(
        string='Désignation',
        required=True,
        help='DESIGNATION - Désignation de l\'article'
    )
    
    code_ean13 = fields.Char(
        string='Code EAN13',
        help='CODE_EAN13 - Code GTIN ou EAN13'
    )

    # ========== FABRICANT ==========
    trigramme_fabricant = fields.Char(
        string='Trigramme fabricant',
        index=True,
        help='CODE_LIDIC - Trigramme Fabricant (3 lettres)'
    )
    
    fabricant_libelle = fields.Char(
        string='Nom du fabricant',
        index=True,
        help='LIBELLE_FABRICANT - Nom complet du fabricant'
    )

    # ========== PRIX ET TARIFICATION ==========
    prix_base = fields.Float(
        string='Prix de base',
        digits=(10, 5),
        help='PRIX_BASE - Tarif de base de l\'article (sans conditions commerciales)'
    )
    
    prix_net = fields.Float(
        string='Prix net client',
        digits=(10, 5),
        help='PRIX_NET - Tarif client appliqué'
    )
    
    prix_vente = fields.Float(
        string='Prix de vente',
        digits=(10, 5),
        help='PRIX_VENTE - Tarif client selon les conditions commerciales classiques'
    )
    
    remise = fields.Float(
        string='Remise (%)',
        digits=(5, 2),
        help='REMISE - Condition commerciale sur l\'article'
    )
    
    date_tarif = fields.Date(
        string='Date de tarif',
        help='DATE_TARIF - Date de référence du tarif de l\'article'
    )
    
    date_peremption = fields.Date(
        string='Date de péremption',
        help='DATE_PEREMPTION - Date de péremption éventuelle de l\'article'
    )

    # ========== CONDITIONNEMENT ET UNITÉS ==========
    conditionnement = fields.Char(
        string='Conditionnement de vente',
        help='CONDITIONNEMENT - Conditionnement de vente Rexel'
    )
    
    unite_mesure = fields.Char(
        string='Unité de mesure',
        help='UOM - Unité de mesure de l\'article (ex: U, M, KG, BOI...)'
    )
    
    unite_mesure_forcee = fields.Boolean(
        string='Unité forcée',
        default=False,
        help='Cocher pour empêcher la mise à jour automatique de l\'unité lors des synchronisations API'
    )

    # ========== CLASSIFICATION REXEL (codes) ==========
    famille_code = fields.Char(
        string='Code famille',
        index=True,
        help='FAMILLE - Code famille Rexel de l\'article'
    )
    
    sous_famille_code = fields.Char(
        string='Code sous-famille',
        index=True,
        help='SOUS_FAMILLE - Code sous-famille Rexel de l\'article'
    )
    
    fonction_code = fields.Char(
        string='Code fonction',
        index=True,
        help='FONCTION - Code fonction Rexel de l\'article'
    )

    # ========== CLASSIFICATION REXEL (libellés) ==========
    famille_libelle = fields.Char(
        string='Famille',
        index=True,
        help='LIBELLE_FAMILLE - Libellé famille Rexel de l\'article'
    )
    
    sous_famille_libelle = fields.Char(
        string='Sous-famille',
        index=True,
        help='LIBELLE_SOUS_FAMILLE - Libellé sous-famille Rexel de l\'article'
    )
    
    fonction_libelle = fields.Char(
        string='Fonction',
        index=True,
        help='LIBELLE_FONCTION - Libellé fonction Rexel de l\'article'
    )

    # ========== ÉCOTAXE D3E ==========
    ref_d3e = fields.Char(
        string='Référence écotaxe',
        help='REF_D3E - Référence de l\'écotaxe'
    )
    
    libelle_d3e = fields.Char(
        string='Libellé écotaxe',
        help='LIBELLE_D3E - Désignation de l\'écotaxe'
    )
    
    code_d3e = fields.Char(
        string='Code écotaxe',
        help='CODE_D3E - Code de l\'écotaxe'
    )
    
    unite_d3e = fields.Float(
        string='Unité écotaxe',
        digits=(10, 2),
        help='UNITE_D3E - Unité d\'écotaxe dans l\'article'
    )
    
    montant_d3e = fields.Float(
        string='Montant écotaxe',
        digits=(10, 5),
        help='MONTANT_D3E - Montant de l\'écotaxe pour l\'article'
    )

    # ========== ENVIRONNEMENTAL ==========
    ecoscore = fields.Char(
        string='Ecoscore',
        help='ECOSCORE - Ecoscore de l\'article'
    )
    
    selection_durable = fields.Boolean(
        string='Sélection durable',
        help='SELECTION_DURABLE - Choix sélection durable'
    )
    
    url_image = fields.Char(
        string='URL image',
        help='URL_IMAGE - Url de l\'image article'
    )

    # ========== CHAMPS TECHNIQUES ==========
    active = fields.Boolean(string='Actif', default=True)
    import_source = fields.Selection([
        ('excel', 'Fichier Excel'),
        ('api', 'API Rexel Cloud'),
    ], string='Source d\'import', default='excel')
    
    # ========== OBSOLESCENCE ==========
    is_obsolete = fields.Boolean(
        string='Article obsolète',
        default=False,
        help='Indique que l\'article n\'a pas été retrouvé lors de la dernière mise à jour API'
    )
    obsolete_date = fields.Datetime(
        string='Date obsolescence',
        help='Date à laquelle l\'article a été marqué comme obsolète'
    )
    obsolete_reason = fields.Char(
        string='Raison obsolescence',
        help='Raison pour laquelle l\'article est marqué obsolète'
    )
    last_api_update = fields.Datetime(
        string='Dernière MAJ API',
        help='Date de la dernière mise à jour réussie via API Rexel'
    )
    
    # Champ calculé pour afficher la date de validité des prix
    date_prix_valide = fields.Datetime(
        string='Prix valide au',
        compute='_compute_date_prix_valide',
        store=False,
        help='Date la plus récente entre la date de tarif Excel et la dernière MAJ API'
    )
    
    @api.depends('date_tarif', 'last_api_update')
    def _compute_date_prix_valide(self):
        """Calcule la date de validité effective des prix"""
        for article in self:
            date_tarif_dt = None
            if article.date_tarif:
                # Convertir date en datetime pour comparaison
                from datetime import datetime
                date_tarif_dt = datetime.combine(article.date_tarif, datetime.min.time())
            
            if article.last_api_update and date_tarif_dt:
                # Prendre la plus récente
                article.date_prix_valide = max(article.last_api_update, date_tarif_dt)
            elif article.last_api_update:
                article.date_prix_valide = article.last_api_update
            elif date_tarif_dt:
                article.date_prix_valide = date_tarif_dt
            else:
                article.date_prix_valide = False
    
    # ========== HISTORIQUE DES PRIX ==========
    price_history_ids = fields.One2many(
        'rexel.price.history',
        'article_id',
        string='Historique des prix'
    )
    price_history_count = fields.Integer(
        string='Nb changements prix',
        compute='_compute_price_history_count'
    )
    
    # ========== LIEN HIÉRARCHIE ==========
    family_node_id = fields.Many2one(
        'rexel.product.family',
        string='Nœud hiérarchie',
        ondelete='set null',
        index=True
    )
    
    # ========== LIEN PRODUIT ODOO ==========
    product_id = fields.Many2one(
        'product.product',
        string='Produit Odoo',
        ondelete='set null',
        index=True
    )
    product_template_id = fields.Many2one(
        'product.template',
        string='Template Produit',
        related='product_id.product_tmpl_id',
        store=True
    )
    is_product_created = fields.Boolean(
        string='Produit créé',
        compute='_compute_is_product_created',
        store=True
    )
    
    # ==========================================================
    # ========== DONNÉES API REXEL - PACK DÉCOUVERTE ===========
    # ==========================================================
    
    # ========== API UNITS (Découverte) ==========
    # URL: /products/v2/units/{supplierCode}/{supplierComRef}
    api_code_interne_produit = fields.Char(
        string='Code interne produit Rexel',
        help='codeInterneProduit - Identifiant interne du produit chez Rexel'
    )
    api_code_ean_unite = fields.Char(
        string='Code EAN Unité',
        help='codeEANUnite - Code-barres EAN de l\'unité'
    )
    api_type_conditionnement = fields.Char(
        string='Type conditionnement',
        help='typeConditionnement - Type de conditionnement (PIE=pièce, MET=mètre, etc.)'
    )
    api_mot_unite = fields.Char(
        string='Mot unité API',
        help='motUnite - Libellé de l\'unité retourné par l\'API (PIECE, METRE, etc.)'
    )
    api_libelle_long = fields.Text(
        string='Libellé long',
        help='libelleLong - Libellé long / description détaillée'
    )
    api_libelle_court = fields.Char(
        string='Libellé court',
        help='libelleCourt - Libellé court'
    )
    api_libelle = fields.Char(
        string='Libellé produit API',
        help='libelle - Libellé du produit'
    )
    api_nombre_conversion = fields.Float(
        string='Facteur conversion',
        digits=(10, 4),
        help='nombreConversionPrincipale - Facteur de conversion vers l\'unité principale'
    )
    api_flag_unite_principale = fields.Char(
        string='Unité principale',
        help='flagUnitePrincipale - Indicateur unité principale (O/N)'
    )
    api_flag_unite_preparable = fields.Char(
        string='Unité préparable',
        help='flagUnitePreparable - Indicateur si l\'unité est préparable (O/N)'
    )
    api_poids_brut = fields.Float(
        string='Poids brut (g)',
        digits=(10, 2),
        help='poidsBrut - Poids brut en grammes'
    )
    api_poids_net = fields.Float(
        string='Poids net (g)',
        digits=(10, 2),
        help='poidsNet - Poids net en grammes'
    )
    api_longueur_ext = fields.Float(
        string='Longueur ext. (mm)',
        digits=(10, 2),
        help='longueurExterieure - Longueur extérieure en mm'
    )
    api_largeur_ext = fields.Float(
        string='Largeur ext. (mm)',
        digits=(10, 2),
        help='largeurExterieure - Largeur extérieure en mm'
    )
    api_hauteur_ext = fields.Float(
        string='Hauteur ext. (mm)',
        digits=(10, 2),
        help='hauteurExterieure - Hauteur extérieure en mm'
    )
    api_longueur_int = fields.Float(
        string='Longueur int. (mm)',
        digits=(10, 2),
        help='longueurInterieure - Longueur intérieure en mm'
    )
    api_largeur_int = fields.Float(
        string='Largeur int. (mm)',
        digits=(10, 2),
        help='largeurInterieure - Largeur intérieure en mm'
    )
    api_hauteur_int = fields.Float(
        string='Hauteur int. (mm)',
        digits=(10, 2),
        help='hauteurInterieure - Hauteur intérieure en mm'
    )
    api_volume_ext = fields.Float(
        string='Volume ext. (mm³)',
        digits=(12, 2),
        help='volumeExterieur - Volume extérieur en mm³'
    )
    api_volume_int = fields.Float(
        string='Volume int. (mm³)',
        digits=(12, 2),
        help='volumeInterieur - Volume intérieur en mm³'
    )
    
    # ========== API STOCKS (Découverte) ==========
    # URL: /external/stocks/positions
    api_stock_agence = fields.Float(
        string='Stock agence',
        digits=(10, 2),
        help='availableBranchStock - Stock disponible en agence'
    )
    api_stock_clr = fields.Float(
        string='Stock centre logistique',
        digits=(10, 2),
        help='availableCLRStock - Stock disponible en centre logistique'
    )
    api_stock_csc = fields.Float(
        string='Stock CSC',
        digits=(10, 2),
        help='availableServiceCenterStock - Stock disponible au centre de service'
    )
    api_delai_agence = fields.Char(
        string='Délai agence',
        help='branchAvailabilityDelay - Délai produit agence'
    )
    api_delai_clr = fields.Char(
        string='Délai centre logistique',
        help='DCAvailabilityDelay - Délai produit centre logistique'
    )
    api_code_centre_livraison = fields.Char(
        string='Code centre livraison',
        help='DCCode - Code du centre de livraison'
    )
    api_min_vente_agence = fields.Float(
        string='Min. vente agence',
        digits=(10, 2),
        help='branchMinimumQuantity - Minimum de vente agence'
    )
    api_multiple_vente_agence = fields.Float(
        string='Multiple vente agence',
        digits=(10, 2),
        help='branchMultipleQuantity - Multiple de vente agence'
    )
    api_min_vente_clr = fields.Float(
        string='Min. vente CLR',
        digits=(10, 2),
        help='DCMinimumQuantity - Minimum de vente centre logistique'
    )
    api_multiple_vente_clr = fields.Float(
        string='Multiple vente CLR',
        digits=(10, 2),
        help='DCMultipleQuantity - Multiple de vente centre logistique'
    )
    api_date_livraison = fields.Date(
        string='Date livraison estimée',
        help='deliveryDate - Date de livraison estimée'
    )
    api_date_livraison_reliquat = fields.Date(
        string='Date livraison reliquat',
        help='backOrderDeliveryDate - Date de livraison des reliquats'
    )
    api_cutoff_livraison = fields.Char(
        string='Cut-off livraison',
        help='cutOffDelivery - Heure limite pour livraison'
    )
    api_last_stock_update = fields.Datetime(
        string='Dernière MAJ stock',
        help='Date de la dernière mise à jour des informations de stock'
    )
    
    # ========== API PRODUCTPRICE (Découverte) ==========
    # URL: /external/productprices/productSalePrices
    api_prix_base = fields.Float(
        string='Prix base API',
        digits=(10, 5),
        help='clientBasePrice - Prix de base retourné par l\'API'
    )
    api_prix_net = fields.Float(
        string='Prix net API',
        digits=(10, 5),
        help='clientNetPrice - Prix net client retourné par l\'API'
    )
    api_has_d3e = fields.Boolean(
        string='Écotaxe D3E',
        help='hasD3E - Indique si le produit a une écotaxe'
    )
    api_d3e_quantite = fields.Float(
        string='Quantité écotaxe',
        digits=(10, 4),
        help='D3EQuantity - Quantité écotaxe'
    )
    api_d3e_cout = fields.Float(
        string='Coût écotaxe',
        digits=(10, 5),
        help='D3ECost - Montant écotaxe'
    )
    api_remise_pct = fields.Float(
        string='Remise API (%)',
        digits=(5, 2),
        help='referenceRebate - Pourcentage de remise retourné par l\'API'
    )
    api_condition_label = fields.Char(
        string='Libellé conditions',
        help='conditionLabel - Libellé des conditions commerciales'
    )
    api_prix_label = fields.Char(
        string='Libellé prix',
        help='priceLabel - Libellé du prix'
    )
    api_derogation = fields.Char(
        string='Dérogation appliquée',
        help='salesAgreement - Code de dérogation appliquée'
    )
    api_last_price_update = fields.Datetime(
        string='Dernière MAJ prix API',
        help='Date de la dernière mise à jour des prix via API'
    )
    
    # ==========================================================
    # ========== DONNÉES API REXEL - PACK PREMIUM ==============
    # ==========================================================
    # Ces champs seront remplis quand vous passerez au Pack Premium
    
    # ========== API REXEL-MEDIAS (Premium) ==========
    # URL: /rexel-medias/v1/full-image/...
    api_image_url = fields.Char(
        string='URL Image API',
        help='[PREMIUM] URL de l\'image du produit via API Rexel-Medias'
    )
    api_image_data = fields.Binary(
        string='Image produit',
        help='[PREMIUM] Image du produit récupérée via API'
    )
    api_fiche_technique_url = fields.Char(
        string='URL Fiche technique',
        help='[PREMIUM] url - URL vers la fiche technique'
    )
    api_catalog_media_id = fields.Char(
        string='ID Média catalogue',
        help='[PREMIUM] catalogMediaId - ID du média pour récupérer la fiche technique'
    )
    api_rexel_id = fields.Char(
        string='Rexel ID',
        help='[PREMIUM] rexelId - ID interne Rexel du produit'
    )
    api_fiche_technique_data = fields.Binary(
        string='Fiche technique',
        help='[PREMIUM] Fiche technique PDF récupérée via API'
    )
    api_last_media_update = fields.Datetime(
        string='Dernière MAJ médias',
        help='[PREMIUM] Date de la dernière mise à jour des médias'
    )
    
    # ========== API PRODUCTCEE (Premium) ==========
    # URL: /products/v2/productCEE/{supplierCode}/{supplierComRef}
    api_cee_id_operation = fields.Char(
        string='ID Opération CEE',
        help='[PREMIUM] idOperationCEE - Identifiant de l\'opération standardisée CEE'
    )
    api_cee_code_secteur = fields.Char(
        string='Code secteur CEE',
        help='[PREMIUM] codeSecteurOperationCEE - Code externe du secteur'
    )
    api_cee_code_sous_secteur = fields.Char(
        string='Code sous-secteur CEE',
        help='[PREMIUM] codeSousSecteurOperationCEE - Code externe du sous-secteur'
    )
    api_cee_reference = fields.Char(
        string='Référence opération CEE',
        help='[PREMIUM] referenceOperationCEE - Référence de l\'opération standardisée'
    )
    api_cee_reference_rexel = fields.Char(
        string='Référence Rexel CEE',
        help='[PREMIUM] referenceRexelOperationCEE - Référence Rexel de l\'opération'
    )
    api_cee_certificat = fields.Char(
        string='Certificat CEE',
        help='[PREMIUM] certificatCEE - Certificats requis'
    )
    api_cee_url_fiche = fields.Char(
        string='URL Fiche CEE',
        help='[PREMIUM] urlFicheOperationCEE - URL vers la fiche opération CEE'
    )
    api_cee_statut = fields.Char(
        string='Statut CEE',
        help='[PREMIUM] statutCEE - Statut du lien CEE'
    )
    api_cee_eligibilite_primexel = fields.Char(
        string='Éligibilité Primexel',
        help='[PREMIUM] flagEligibilitePrimexel - Indicateur d\'éligibilité Primexel'
    )
    api_cee_date_debut = fields.Date(
        string='Date début validité CEE',
        help='[PREMIUM] dateDebutValidite - Date de début de validité'
    )
    api_cee_date_fin = fields.Date(
        string='Date fin validité CEE',
        help='[PREMIUM] dateFinValidite - Date de fin de validité'
    )
    
    # ========== API PRODUCTENVIRONMENTALATTRIBUTES (Premium) ==========
    # URL: /products/v2/productEnvironmentalAttributes/{supplierCode}/{supplierComRef}
    api_note_ecoscore = fields.Char(
        string='Note Ecoscore API',
        help='[PREMIUM] noteEcoscore - Note eco-score retournée par l\'API'
    )
    api_code_critere_env = fields.Char(
        string='Code critère environnemental',
        help='[PREMIUM] codeCritereEnvironemental - Code du critère environnemental'
    )
    
    # ========== API PRODUCTREPLACEMENTLINKS (Premium) ==========
    # URL: /products/v2/productReplacementLinks/{supplierCode}/{supplierComRef}
    api_remplacement_sens = fields.Char(
        string='Sens remplacement',
        help='[PREMIUM] sens - PAR (remplacé par) ou DE (remplaçant de)'
    )
    api_remplacement_code_interne = fields.Char(
        string='Code produit remplacement',
        help='[PREMIUM] codeInterneProduitRemplacement - Code interne du produit de remplacement'
    )
    api_remplacement_ref_rexel = fields.Char(
        string='Réf. Rexel remplacement',
        help='[PREMIUM] referenceRexelRemplacement - Référence Rexel du produit de remplacement'
    )
    api_remplacement_date_debut = fields.Date(
        string='Date début lien remplacement',
        help='[PREMIUM] dateDebutLien - Date d\'application du lien'
    )
    api_remplacement_date_fin = fields.Date(
        string='Date fin lien remplacement',
        help='[PREMIUM] dateFinLien - Date de fin du lien'
    )
    api_date_peremption = fields.Date(
        string='Date péremption API',
        help='[PREMIUM] datePeremption - Date de péremption du produit'
    )
    
    # ========== API PRODUCTSUSTAINABLEOFFER (Premium - non documenté) ==========
    # Sélection durable - alternatives à faible empreinte CO2
    api_sustainable_alternative = fields.Boolean(
        string='Alternative durable disponible',
        help='[PREMIUM] Indique si une alternative durable existe'
    )
    api_sustainable_ref = fields.Char(
        string='Réf. alternative durable',
        help='[PREMIUM] Référence du produit alternatif durable'
    )
    
    _sql_constraints = [
        ('reference_unique', 'unique(reference_fabricant)', 'La référence fabricant doit être unique !'),
    ]

    @api.depends('price_history_ids')
    def _compute_price_history_count(self):
        """Compte le nombre d'entrées dans l'historique"""
        for record in self:
            record.price_history_count = len(record.price_history_ids)
    
    @api.depends('product_id')
    def _compute_is_product_created(self):
        """Vérifie si le produit Odoo existe"""
        for record in self:
            record.is_product_created = bool(record.product_id)

    def name_get(self):
        """Affichage personnalisé dans les listes"""
        result = []
        for record in self:
            name = f"[{record.reference_fabricant}] {record.designation[:50]}"
            if record.fabricant_libelle:
                name = f"[{record.trigramme_fabricant}] {name}"
            result.append((record.id, name))
        return result

    # ========== MÉTHODES CRÉATION PRODUIT ODOO ==========
    
    def _get_uom_id(self):
        """Convertit l'unité de mesure Rexel en UoM Odoo"""
        uom_mapping = {
            'U': 'Units',
            'M': 'm',
            'KG': 'kg',
            'L': 'L',
            'BOI': 'Units',  # Boîte
            'ROU': 'Units',  # Rouleau
            'SAC': 'Units',  # Sac
            'PAQ': 'Units',  # Paquet
            'ENS': 'Units',  # Ensemble
        }
        
        unite = self.unite_mesure or 'U'
        uom_name = uom_mapping.get(unite.upper(), 'Units')
        
        uom = self.env['uom.uom'].search([('name', '=', uom_name)], limit=1)
        return uom.id if uom else self.env.ref('uom.product_uom_unit').id

    def _prepare_product_values(self):
        """Prépare les valeurs pour la création du produit Odoo"""
        self.ensure_one()
        
        # Créer ou récupérer la catégorie produit
        categ_id = self.env.ref('product.product_category_all').id
        if self.famille_libelle:
            category = self.env['product.category'].search([
                ('name', '=', self.famille_libelle)
            ], limit=1)
            if not category:
                category = self.env['product.category'].create({
                    'name': self.famille_libelle,
                })
            categ_id = category.id
        
        return {
            'name': self.designation,
            'default_code': self.reference_fabricant,
            'barcode': self.code_ean13 or self.reference_rexel,
            'list_price': self.prix_base or 0.0,
            'standard_price': self.prix_net or 0.0,
            'uom_id': self._get_uom_id(),
            'uom_po_id': self._get_uom_id(),
            'categ_id': categ_id,
            'sale_ok': True,
            'purchase_ok': True,
        }

    def action_create_product(self):
        """Crée un produit Odoo depuis l'article Rexel"""
        for article in self:
            if article.product_id:
                raise UserError(_('Un produit Odoo existe déjà pour cet article.'))
            
            values = article._prepare_product_values()
            product = self.env['product.product'].create(values)
            article.product_id = product.id
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Produit créé'),
                    'message': _('Le produit Odoo a été créé avec succès.'),
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_update_product(self):
        """Met à jour le produit Odoo avec les données Rexel"""
        for article in self:
            if not article.product_id:
                raise UserError(_('Aucun produit Odoo associé à cet article.'))
            
            values = article._prepare_product_values()
            article.product_id.write(values)
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Produit mis à jour'),
                    'message': _('Le produit Odoo a été mis à jour.'),
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_view_product(self):
        """Ouvre la fiche produit Odoo"""
        self.ensure_one()
        if not self.product_id:
            raise UserError(_('Aucun produit Odoo associé à cet article.'))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'res_id': self.product_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_price_history(self):
        """Affiche l'historique des prix avec graphique"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Historique des prix'),
            'res_model': 'rexel.price.history',
            'view_mode': 'graph,list',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }

    def action_mark_not_obsolete(self):
        """Réactive un article marqué comme obsolète"""
        self.ensure_one()
        self.write({
            'is_obsolete': False,
            'obsolete_date': False,
            'obsolete_reason': False,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Article réactivé'),
                'message': _('L\'article n\'est plus marqué comme obsolète.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_fetch_units_batch(self):
        """
        Récupère les unités de mesure pour les articles sélectionnés en BATCH (parallèle)
        Beaucoup plus rapide que la méthode séquentielle !
        
        Logique des unités (dans l'ordre de priorité):
        1. Unité API : PIECE → U, METRE → ML
        2. Conditionnement : TOU → ML, MET → ML, PIE → U
        3. Défaut : U + message d'erreur
        """
        if not self:
            raise UserError(_('Veuillez sélectionner au moins un article.'))
        
        config = self.env['rexel.config'].get_config()
        if not config.api_enabled:
            raise UserError(_('L\'API Rexel n\'est pas activée dans la configuration.'))
        
        # Préparer la liste des produits à récupérer
        products_list = []
        article_map = {}  # Pour retrouver l'article depuis le tuple
        
        for article in self:
            if article.trigramme_fabricant and article.reference_fabricant:
                key = (article.trigramme_fabricant, article.reference_fabricant)
                products_list.append(key)
                article_map[key] = article
        
        if not products_list:
            raise UserError(_('Aucun article avec trigramme et référence fabricant.'))
        
        _logger.info(f"Lancement récupération batch unités pour {len(products_list)} articles")
        
        # Appel batch parallèle
        units_data = config.get_product_units_batch(products_list)
        
        # Mettre à jour les articles avec TOUS les champs API units
        updated = 0
        warnings = []
        unit_errors = []  # Articles avec conditionnement inconnu
        skipped_forced = 0  # Articles avec unité forcée
        
        for key, unit_data in units_data.items():
            article = article_map.get(key)
            if article and unit_data:
                vals = {
                    'last_api_update': fields.Datetime.now(),
                }
                
                # ========== LOGIQUE DES UNITÉS CENTRALISÉE ==========
                # Respecter le flag unite_mesure_forcee
                if not article.unite_mesure_forcee:
                    # Récupérer l'unité API brute et le conditionnement
                    api_unit_raw = unit_data.get('motUnite') or unit_data.get('unite_api')
                    conditionnement = unit_data.get('typeConditionnement') or article.conditionnement or ''
                    
                    # Utiliser la méthode centralisée pour déterminer l'unité
                    unite_finale, unit_error = config._determine_unit_from_conditionnement(
                        conditionnement, None, api_unit_raw
                    )
                    
                    if unit_error:
                        unit_errors.append(f"{article.reference_fabricant} (cond: {unit_error})")
                    
                    vals['unite_mesure'] = unite_finale
                    _logger.info(f"Article {article.reference_fabricant}: API unit={api_unit_raw}, cond={conditionnement} -> {unite_finale}")
                else:
                    skipped_forced += 1
                    _logger.info(f"Article {article.reference_fabricant}: unité forcée, pas de mise à jour")
                
                # Code EAN
                if unit_data.get('codeEAN13') and not article.code_ean13:
                    vals['code_ean13'] = unit_data['codeEAN13']
                
                # Conditionnement (toujours mettre à jour si présent)
                if unit_data.get('typeConditionnement'):
                    vals['conditionnement'] = unit_data['typeConditionnement']
                
                # ========== NOUVEAUX CHAMPS API UNITS ==========
                # Identification
                if unit_data.get('codeInterneProduit'):
                    vals['api_code_interne_produit'] = str(unit_data['codeInterneProduit'])
                if unit_data.get('codeEANUnite'):
                    vals['api_code_ean_unite'] = unit_data['codeEANUnite']
                if unit_data.get('typeConditionnement'):
                    vals['api_type_conditionnement'] = unit_data['typeConditionnement']
                if unit_data.get('motUnite'):
                    vals['api_mot_unite'] = unit_data['motUnite']
                
                # Libellés
                if unit_data.get('libelleLong'):
                    vals['api_libelle_long'] = unit_data['libelleLong']
                if unit_data.get('libelleCourt'):
                    vals['api_libelle_court'] = unit_data['libelleCourt']
                if unit_data.get('libelle'):
                    vals['api_libelle'] = unit_data['libelle']
                
                # Conversion
                if unit_data.get('nombreConversionPrincipale'):
                    vals['api_nombre_conversion'] = unit_data['nombreConversionPrincipale']
                if unit_data.get('flagUnitePrincipale'):
                    vals['api_flag_unite_principale'] = unit_data['flagUnitePrincipale']
                if unit_data.get('flagUnitePreparable'):
                    vals['api_flag_unite_preparable'] = unit_data['flagUnitePreparable']
                
                # Poids
                if unit_data.get('poidsBrut'):
                    vals['api_poids_brut'] = unit_data['poidsBrut']
                if unit_data.get('poidsNet'):
                    vals['api_poids_net'] = unit_data['poidsNet']
                
                # Dimensions extérieures
                if unit_data.get('longueurExterieure'):
                    vals['api_longueur_ext'] = unit_data['longueurExterieure']
                if unit_data.get('largeurExterieure'):
                    vals['api_largeur_ext'] = unit_data['largeurExterieure']
                if unit_data.get('hauteurExterieure'):
                    vals['api_hauteur_ext'] = unit_data['hauteurExterieure']
                if unit_data.get('volumeExterieur'):
                    vals['api_volume_ext'] = unit_data['volumeExterieur']
                
                # Dimensions intérieures
                if unit_data.get('longueurInterieure'):
                    vals['api_longueur_int'] = unit_data['longueurInterieure']
                if unit_data.get('largeurInterieure'):
                    vals['api_largeur_int'] = unit_data['largeurInterieure']
                if unit_data.get('hauteurInterieure'):
                    vals['api_hauteur_int'] = unit_data['hauteurInterieure']
                if unit_data.get('volumeInterieur'):
                    vals['api_volume_int'] = unit_data['volumeInterieur']
                
                if vals:
                    article.write(vals)
                    updated += 1
                
                if unit_data.get('warning'):
                    warnings.append(f"{article.reference_rexel}: {unit_data['warning']}")
        
        # Construire le message de résultat
        message_parts = [f"✓ {updated}/{len(products_list)} articles mis à jour"]
        
        if skipped_forced > 0:
            message_parts.append(f"🔒 {skipped_forced} articles avec unité forcée (ignorés)")
        
        if unit_errors:
            message_parts.append(f"⚠️ {len(unit_errors)} conditionnements inconnus (défaut U)")
            # Afficher les 5 premiers
            for ref in unit_errors[:5]:
                message_parts.append(f"  • {ref}")
            if len(unit_errors) > 5:
                message_parts.append(f"  ... et {len(unit_errors) - 5} autres")
        
        if warnings:
            message_parts.append(f"⚠️ {len(warnings)} avertissements API")
        
        message = "\n".join(message_parts)
        
        # Log détaillé
        _logger.info(f"=== RÉSULTAT RÉCUPÉRATION UNITÉS ===")
        _logger.info(f"Articles traités: {len(products_list)}")
        _logger.info(f"Articles mis à jour: {updated}")
        _logger.info(f"Unités forcées (ignorées): {skipped_forced}")
        _logger.info(f"Conditionnements inconnus: {len(unit_errors)}")
        if unit_errors:
            for ref in unit_errors:
                _logger.warning(f"  Conditionnement inconnu: {ref}")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Récupération des unités terminée'),
                'message': message,
                'type': 'success' if not (warnings or unit_errors) else 'warning',
                'sticky': bool(warnings),
            }
        }

    def action_recalculate_discount(self):
        """
        Recalcule la remise à partir du prix base et prix net
        Formule: remise = ((prix_base - prix_net) / prix_base) * 100
        """
        if not self:
            raise UserError(_('Veuillez sélectionner au moins un article.'))
        
        updated = 0
        skipped = 0
        
        for article in self:
            if article.prix_base and article.prix_base > 0 and article.prix_net:
                remise_calculee = ((article.prix_base - article.prix_net) / article.prix_base) * 100
                article.write({'remise': round(remise_calculee, 2)})
                updated += 1
            else:
                skipped += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recalcul des remises terminé'),
                'message': f"✓ {updated} remises recalculées\n⚠️ {skipped} articles ignorés (prix manquants)",
                'type': 'success' if skipped == 0 else 'warning',
                'sticky': False,
            }
        }

    def action_fetch_stocks_batch(self):
        """
        Récupère les informations de stock via l'API Stocks
        Pack: Découverte et Premium
        """
        if not self:
            raise UserError(_('Veuillez sélectionner au moins un article.'))
        
        config = self.env['rexel.config'].get_config()
        if not config.api_enabled:
            raise UserError(_('L\'API Rexel n\'est pas activée dans la configuration.'))
        
        # Préparer la liste des produits
        products_list = []
        article_map = {}
        
        for article in self:
            if article.trigramme_fabricant and article.reference_fabricant:
                key = (article.trigramme_fabricant, article.reference_fabricant)
                products_list.append((article.trigramme_fabricant, article.reference_fabricant, 1))
                article_map[key] = article
        
        if not products_list:
            raise UserError(_('Aucun article avec trigramme et référence fabricant.'))
        
        _logger.info(f"Récupération stocks pour {len(products_list)} articles")
        
        # Appel API
        stocks_data = config.get_product_stocks(products_list)
        
        # Mettre à jour les articles
        updated = 0
        for key, data in stocks_data.items():
            article = article_map.get(key)
            if article and data:
                vals = {
                    'api_last_stock_update': fields.Datetime.now(),
                }
                
                # Stocks
                if data.get('availableBranchStock'):
                    try:
                        vals['api_stock_agence'] = float(data['availableBranchStock'])
                    except: pass
                if data.get('availableCLRStock'):
                    try:
                        vals['api_stock_clr'] = float(data['availableCLRStock'])
                    except: pass
                if data.get('availableServiceCenterStock'):
                    try:
                        vals['api_stock_csc'] = float(data['availableServiceCenterStock'])
                    except: pass
                
                # Délais
                if data.get('branchAvailabilityDelay'):
                    vals['api_delai_agence'] = data['branchAvailabilityDelay']
                if data.get('DCAvailabilityDelay'):
                    vals['api_delai_clr'] = data['DCAvailabilityDelay']
                if data.get('DCCode'):
                    vals['api_code_centre_livraison'] = data['DCCode']
                if data.get('cutOffDelivery'):
                    vals['api_cutoff_livraison'] = data['cutOffDelivery']
                
                # Quantités min/multiple
                if data.get('branchMinimumQuantity'):
                    try:
                        vals['api_min_vente_agence'] = float(data['branchMinimumQuantity'])
                    except: pass
                if data.get('branchMultipleQuantity'):
                    try:
                        vals['api_multiple_vente_agence'] = float(data['branchMultipleQuantity'])
                    except: pass
                if data.get('DCMinimumQuantity'):
                    try:
                        vals['api_min_vente_clr'] = float(data['DCMinimumQuantity'])
                    except: pass
                if data.get('DCMultipleQuantity'):
                    try:
                        vals['api_multiple_vente_clr'] = float(data['DCMultipleQuantity'])
                    except: pass
                
                article.write(vals)
                updated += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Récupération des stocks terminée'),
                'message': f"✓ {updated}/{len(products_list)} articles mis à jour",
                'type': 'success',
                'sticky': False,
            }
        }

    def action_fetch_prices_batch(self):
        """
        Récupère les informations de prix via l'API ProductPrice
        Pack: Découverte et Premium
        """
        if not self:
            raise UserError(_('Veuillez sélectionner au moins un article.'))
        
        config = self.env['rexel.config'].get_config()
        if not config.api_enabled:
            raise UserError(_('L\'API Rexel n\'est pas activée dans la configuration.'))
        
        # Préparer la liste des produits
        products_list = []
        article_map = {}
        
        for article in self:
            if article.trigramme_fabricant and article.reference_fabricant:
                key = (article.trigramme_fabricant, article.reference_fabricant)
                products_list.append((article.trigramme_fabricant, article.reference_fabricant, 1))
                article_map[key] = article
        
        if not products_list:
            raise UserError(_('Aucun article avec trigramme et référence fabricant.'))
        
        _logger.info(f"Récupération prix pour {len(products_list)} articles")
        
        # Appel API
        prices_data = config.get_product_prices(products_list)
        
        # Mettre à jour les articles
        updated = 0
        for key, data in prices_data.items():
            article = article_map.get(key)
            if article and data:
                vals = {
                    'api_last_price_update': fields.Datetime.now(),
                    'last_api_update': fields.Datetime.now(),
                    # Retirer le flag obsolète si l'article est trouvé
                    'is_obsolete': False,
                    'obsolete_date': False,
                    'obsolete_reason': False,
                }
                
                prix_base = None
                prix_net = None
                
                # Prix
                if data.get('clientBasePrice'):
                    try:
                        prix_base = float(data['clientBasePrice'])
                        vals['api_prix_base'] = prix_base
                        vals['prix_base'] = prix_base
                    except: pass
                if data.get('clientNetPrice'):
                    try:
                        prix_net = float(data['clientNetPrice'])
                        vals['api_prix_net'] = prix_net
                        vals['prix_net'] = prix_net
                    except: pass
                
                # Remise: utiliser API ou calculer
                remise_api = data.get('referenceRebate')
                if remise_api:
                    try:
                        vals['api_remise_pct'] = float(remise_api)
                        vals['remise'] = float(remise_api)
                    except: pass
                elif prix_base and prix_base > 0 and prix_net is not None:
                    # Calculer la remise si l'API ne la fournit pas
                    remise_calculee = ((prix_base - prix_net) / prix_base) * 100
                    vals['remise'] = round(remise_calculee, 2)
                
                # Écotaxe
                if data.get('hasD3E'):
                    vals['api_has_d3e'] = str(data['hasD3E']).lower() in ('true', '1', 'o', 'oui')
                if data.get('D3EQuantity'):
                    try:
                        vals['api_d3e_quantite'] = float(data['D3EQuantity'])
                    except: pass
                if data.get('D3ECost'):
                    try:
                        vals['api_d3e_cout'] = float(data['D3ECost'])
                    except: pass
                
                # Conditions
                if data.get('conditionLabel'):
                    vals['api_condition_label'] = data['conditionLabel']
                if data.get('priceLabel'):
                    vals['api_prix_label'] = data['priceLabel']
                if data.get('salesAgreement'):
                    vals['api_derogation'] = data['salesAgreement']
                
                article.write(vals)
                updated += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Récupération des prix terminée'),
                'message': f"✓ {updated}/{len(products_list)} articles mis à jour",
                'type': 'success',
                'sticky': False,
            }
        }

    def action_fetch_premium_data(self):
        """
        Récupère les données Premium (CEE, Environnemental, Remplacement)
        Pack: Premium uniquement
        """
        if not self:
            raise UserError(_('Veuillez sélectionner au moins un article.'))
        
        config = self.env['rexel.config'].get_config()
        if not config.api_enabled:
            raise UserError(_('L\'API Rexel n\'est pas activée dans la configuration.'))
        
        if config.api_pack != 'premium':
            raise UserError(_('Cette fonctionnalité nécessite le Pack Premium.\n\n'
                             'Vous pouvez activer le Pack Premium dans Configuration → Pack API Rexel.'))
        
        import time
        updated = 0
        cee_count = 0
        env_count = 0
        repl_count = 0
        tech_count = 0
        
        rate_limit = config.rate_limit_per_second if config.rate_limit_enabled else 20
        
        for i, article in enumerate(self):
            if not article.trigramme_fabricant or not article.reference_fabricant:
                continue
            
            # Rate limiting
            if config.rate_limit_enabled and i > 0 and i % rate_limit == 0:
                time.sleep(1)
            
            vals = {}
            
            # CEE
            cee_data = config.get_product_cee(article.trigramme_fabricant, article.reference_fabricant)
            if cee_data:
                if cee_data.get('idOperationCEE'):
                    vals['api_cee_id_operation'] = str(cee_data['idOperationCEE'])
                if cee_data.get('codeSecteurOperationCEE'):
                    vals['api_cee_code_secteur'] = cee_data['codeSecteurOperationCEE']
                if cee_data.get('codeSousSecteurOperationCEE'):
                    vals['api_cee_code_sous_secteur'] = cee_data['codeSousSecteurOperationCEE']
                if cee_data.get('referenceOperationCEE'):
                    vals['api_cee_reference'] = cee_data['referenceOperationCEE']
                if cee_data.get('referenceRexelOperationCEE'):
                    vals['api_cee_reference_rexel'] = cee_data['referenceRexelOperationCEE']
                if cee_data.get('certificatCEE'):
                    vals['api_cee_certificat'] = cee_data['certificatCEE']
                if cee_data.get('urlFicheOperationCEE'):
                    vals['api_cee_url_fiche'] = cee_data['urlFicheOperationCEE']
                if cee_data.get('statutCEE'):
                    vals['api_cee_statut'] = cee_data['statutCEE']
                if cee_data.get('flagEligibilitePrimexel'):
                    vals['api_cee_eligibilite_primexel'] = cee_data['flagEligibilitePrimexel']
                cee_count += 1
            
            # Environnemental
            env_data = config.get_product_environmental(article.trigramme_fabricant, article.reference_fabricant)
            if env_data:
                if env_data.get('noteEcoscore'):
                    vals['api_note_ecoscore'] = env_data['noteEcoscore']
                    vals['ecoscore'] = env_data['noteEcoscore']
                if env_data.get('codeCritereEnvironemental'):
                    vals['api_code_critere_env'] = env_data['codeCritereEnvironemental']
                env_count += 1
            
            # Remplacement
            repl_data = config.get_product_replacement(article.trigramme_fabricant, article.reference_fabricant)
            if repl_data:
                if repl_data.get('sens'):
                    vals['api_remplacement_sens'] = repl_data['sens']
                if repl_data.get('codeInterneProduitRemplacement'):
                    vals['api_remplacement_code_interne'] = repl_data['codeInterneProduitRemplacement']
                if repl_data.get('referenceRexelRemplacement'):
                    vals['api_remplacement_ref_rexel'] = repl_data['referenceRexelRemplacement']
                repl_count += 1
            
            # Fiche technique
            tech_data = config.get_technical_sheet_links(article.trigramme_fabricant, article.reference_fabricant)
            if tech_data:
                if tech_data.get('catalogMediaId'):
                    vals['api_catalog_media_id'] = tech_data['catalogMediaId']
                if tech_data.get('rexelId'):
                    vals['api_rexel_id'] = tech_data['rexelId']
                if tech_data.get('url'):
                    vals['api_fiche_technique_url'] = tech_data['url']
                vals['api_last_media_update'] = fields.Datetime.now()
                tech_count += 1
            
            if vals:
                article.write(vals)
                updated += 1
            
            if (i + 1) % 50 == 0:
                _logger.info(f"Progression Premium: {i + 1}/{len(self)}")
        
        message = f"✓ {updated} articles mis à jour\n"
        message += f"📋 CEE: {cee_count} | 🌱 Eco: {env_count} | 🔄 Repl: {repl_count} | 📄 Tech: {tech_count}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Récupération données Premium terminée'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_fetch_all_api_data(self):
        """
        Récupère TOUTES les données API disponibles selon le pack
        Pack Découverte: Units, Stocks, Prix
        Pack Premium: + CEE, Environnemental, Remplacement, Fiches techniques
        """
        if not self:
            raise UserError(_('Veuillez sélectionner au moins un article.'))
        
        config = self.env['rexel.config'].get_config()
        if not config.api_enabled:
            raise UserError(_('L\'API Rexel n\'est pas activée dans la configuration.'))
        
        # Récupérer Units
        self.action_fetch_units_batch()
        
        # Récupérer Stocks
        self.action_fetch_stocks_batch()
        
        # Récupérer Prix
        self.action_fetch_prices_batch()
        
        # Si Premium, récupérer les données supplémentaires
        if config.api_pack == 'premium':
            self.action_fetch_premium_data()
        
        pack_name = "Premium" if config.api_pack == 'premium' else "Découverte"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Récupération complète terminée'),
                'message': f"✓ Toutes les données API ({pack_name}) ont été récupérées pour {len(self)} articles.",
                'type': 'success',
                'sticky': False,
            }
        }
