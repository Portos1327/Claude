# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import re
import logging

_logger = logging.getLogger(__name__)


class CableProductMaster(models.Model):
    """Produit câble maître - SOURCE DE VÉRITÉ unique
    
    Le câble maître représente un câble technique unique défini par:
    - Type (R2V, AR2V, H07V-U, etc.)
    - Configuration (3G, 4X, 5G, etc.) - G=avec terre, X=sans terre
    - Section (1,5 / 2,5 / 4 / 6 / etc.)
    
    RÈGLE MÉTIER FONDAMENTALE:
    - Matching STRICT: TYPE + CONFIG + SECTION
    - Différencier R2V 3G1,5 de R2V 3G2,5
    - Différencier 3G (avec terre) de 3X (sans terre)
    """
    _name = 'cable.product.master'
    _description = 'Câble maître (source de vérité)'
    _order = 'cable_type_code, nb_conductors, section'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Désignation',
        required=True,
        tracking=True
    )
    
    # Référence unifiée format: TYPE-CONFIG-SECTION
    reference_unified = fields.Char(
        string='Référence unifiée',
        compute='_compute_reference_unified',
        store=True,
        help='Référence standardisée: TYPE-CONFIG-SECTION (ex: R2V-3G-1,5)'
    )
    
    # Type de câble
    cable_type_id = fields.Many2one(
        'cable.type',
        string='Type de câble',
        index=True
    )
    cable_type_code = fields.Char(
        string='Code type',
        required=True,
        help='R2V, AR2V, H07V-U, etc.'
    )
    
    # Caractéristiques techniques
    nb_conductors = fields.Integer(
        string='Nb conducteurs',
        default=1,
        help='Nombre de conducteurs (1, 2, 3, 4, 5...)'
    )
    has_ground = fields.Boolean(
        string='Avec terre (G)',
        default=True,
        help='G = avec conducteur de terre, X = sans terre'
    )
    conductor_config = fields.Char(
        string='Configuration',
        compute='_compute_conductor_config',
        store=True,
        help='Ex: 3G ou 4X (sans la section)'
    )
    section = fields.Float(
        string='Section (mm²)',
        digits=(6, 2),
        required=True
    )
    section_text = fields.Char(
        string='Section (texte)',
        compute='_compute_section_text',
        store=True,
        help='Section formatée avec virgule (ex: 1,5)'
    )
    
    conductor_material = fields.Selection([
        ('copper', 'Cuivre'),
        ('aluminum', 'Aluminium'),
    ], string='Matériau', default='copper')
    
    norme = fields.Char(string='Norme')
    voltage_class = fields.Selection([
        ('bt', 'Basse Tension'),
        ('hta', 'Moyenne Tension'),
        ('htb', 'Haute Tension'),
    ], string='Classe tension', default='bt')
    
    # CLÉ DE MATCHING STRICTE: TYPE-CONFIG-SECTION
    matching_key = fields.Char(
        string='Clé de matching',
        compute='_compute_matching_key',
        store=True,
        index=True,
        help='Clé unique: TYPE-CONFIG-SECTION (ex: R2V-3G-1,5)'
    )
    
    # === PRIX FOURNISSEURS ===
    supplier_price_ids = fields.One2many(
        'cable.supplier.price',
        'cable_master_id',
        string='Prix fournisseurs'
    )
    
    # Anciennes lignes de tarif (compatibilité)
    pricelist_line_ids = fields.One2many(
        'cable.pricelist.line',
        'master_product_id',
        string='Lignes tarifaires (legacy)'
    )
    
    # === STATISTIQUES PRIX ===
    supplier_count = fields.Integer(
        string='Nb fournisseurs',
        compute='_compute_price_stats',
        store=True
    )
    price_min = fields.Float(
        string='Prix min €/ml',
        compute='_compute_price_stats',
        store=True,
        digits=(12, 4)
    )
    price_max = fields.Float(
        string='Prix max €/ml',
        compute='_compute_price_stats',
        store=True,
        digits=(12, 4)
    )
    price_avg = fields.Float(
        string='Prix moyen €/ml',
        compute='_compute_price_stats',
        store=True,
        digits=(12, 4)
    )
    price_spread = fields.Float(
        string='Écart prix (%)',
        compute='_compute_price_stats',
        store=True
    )
    
    # Meilleur fournisseur
    best_supplier_id = fields.Many2one(
        'cable.supplier',
        string='Meilleur fournisseur',
        compute='_compute_price_stats',
        store=True
    )
    best_supplier_price_id = fields.Many2one(
        'cable.supplier.price',
        string='Meilleur prix fournisseur',
        compute='_compute_price_stats',
        store=True
    )
    best_price = fields.Float(
        string='Meilleur prix €/ml',
        compute='_compute_price_stats',
        store=True,
        digits=(12, 4)
    )
    avg_price_variation = fields.Float(
        string='Variation moyenne (%)',
        compute='_compute_price_stats',
        store=True,
        digits=(5, 2)
    )
    
    # === LIEN PRODUIT ODOO ===
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Produit Odoo'
    )
    product_id = fields.Many2one(
        'product.product',
        string='Variante produit',
        compute='_compute_product_id',
        store=True
    )
    
    # Médias du meilleur fournisseur
    best_image_url = fields.Char(
        string='Image (meilleur prix)',
        compute='_compute_best_media',
        store=True
    )
    best_datasheet_url = fields.Char(
        string='Fiche technique (meilleur prix)',
        compute='_compute_best_media',
        store=True
    )
    
    # Lien Rexel (optionnel)
    rexel_article_id = fields.Integer(string='ID Article Rexel')
    
    active = fields.Boolean(string='Actif', default=True)
    notes = fields.Text(string='Notes')
    
    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    
    @api.depends('nb_conductors', 'has_ground')
    def _compute_conductor_config(self):
        """Génère la configuration (ex: 3G ou 4X) SANS la section"""
        for rec in self:
            if rec.nb_conductors and rec.nb_conductors > 0:
                suffix = 'G' if rec.has_ground else 'X'
                # Pour les fils simples (1 conducteur), pas de préfixe
                if rec.nb_conductors == 1:
                    rec.conductor_config = ''
                else:
                    rec.conductor_config = f"{rec.nb_conductors}{suffix}"
            else:
                rec.conductor_config = ''
    
    @api.depends('section')
    def _compute_section_text(self):
        """Formate la section avec virgule (format français)"""
        for rec in self:
            if rec.section:
                # Convertir en texte avec virgule
                section_str = str(rec.section).replace('.', ',')
                # Enlever ,0 final si entier
                if section_str.endswith(',0'):
                    section_str = section_str[:-2]
                rec.section_text = section_str
            else:
                rec.section_text = ''
    
    @api.depends('cable_type_code', 'conductor_config', 'section_text')
    def _compute_reference_unified(self):
        """Génère la référence unifiée TYPE-CONFIG-SECTION"""
        for rec in self:
            parts = []
            if rec.cable_type_code:
                parts.append(rec.cable_type_code.upper().replace(' ', ''))
            if rec.conductor_config:
                parts.append(rec.conductor_config)
            if rec.section_text:
                parts.append(rec.section_text)
            rec.reference_unified = '-'.join(parts) if parts else False
    
    @api.depends('cable_type_code', 'conductor_config', 'section_text')
    def _compute_matching_key(self):
        """Génère la clé de matching STRICTE: TYPE-CONFIG-SECTION
        
        Exemples:
        - R2V-3G-1,5 (R2V 3 conducteurs avec terre, section 1,5mm²)
        - R2V-3X-2,5 (R2V 3 conducteurs sans terre, section 2,5mm²)
        - H07V-U--2,5 (fil simple, pas de config, section 2,5mm²)
        """
        for rec in self:
            parts = []
            
            # Type de câble (obligatoire)
            if rec.cable_type_code:
                type_code = rec.cable_type_code.upper().strip()
                type_code = re.sub(r'\s+', '', type_code)
                parts.append(type_code)
            
            # Configuration (peut être vide pour fils simples)
            parts.append(rec.conductor_config or '')
            
            # Section (obligatoire)
            if rec.section_text:
                parts.append(rec.section_text)
            
            # Construire la clé si au moins type et section
            if len(parts) >= 2 and parts[0] and parts[-1]:
                rec.matching_key = '-'.join(parts)
            else:
                rec.matching_key = False
    
    @api.depends('supplier_price_ids', 'supplier_price_ids.price_per_ml',
                 'supplier_price_ids.supplier_id', 'supplier_price_ids.price_variation',
                 'pricelist_line_ids', 'pricelist_line_ids.price_per_ml')
    def _compute_price_stats(self):
        """Calcule les statistiques de prix"""
        for rec in self:
            # Priorité aux prix fournisseurs (nouveau modèle)
            prices = rec.supplier_price_ids.filtered(
                lambda p: p.price_per_ml > 0 and p.active
            )
            
            # Fallback sur les lignes legacy
            if not prices:
                lines = rec.pricelist_line_ids.filtered(lambda l: l.price_per_ml > 0)
                if lines:
                    price_values = lines.mapped('price_per_ml')
                    suppliers = lines.mapped('supplier_id')
                    rec.supplier_count = len(set(suppliers.ids))
                    rec.price_min = min(price_values)
                    rec.price_max = max(price_values)
                    rec.price_avg = sum(price_values) / len(price_values)
                    if rec.price_min > 0:
                        rec.price_spread = (rec.price_max - rec.price_min) / rec.price_min * 100
                    else:
                        rec.price_spread = 0
                    best = min(lines, key=lambda l: l.price_per_ml)
                    rec.best_supplier_id = best.supplier_id.id
                    rec.best_supplier_price_id = False
                    rec.best_price = best.price_per_ml
                    variations = [l.price_variation for l in lines if l.price_variation]
                    rec.avg_price_variation = sum(variations) / len(variations) if variations else 0
                    continue
                else:
                    rec.supplier_count = 0
                    rec.price_min = 0
                    rec.price_max = 0
                    rec.price_avg = 0
                    rec.price_spread = 0
                    rec.best_supplier_id = False
                    rec.best_supplier_price_id = False
                    rec.best_price = 0
                    rec.avg_price_variation = 0
                    continue
            
            # Calcul depuis supplier_price_ids
            price_values = prices.mapped('price_per_ml')
            suppliers = prices.mapped('supplier_id')
            
            rec.supplier_count = len(suppliers)
            rec.price_min = min(price_values)
            rec.price_max = max(price_values)
            rec.price_avg = sum(price_values) / len(price_values)
            
            if rec.price_min > 0:
                rec.price_spread = (rec.price_max - rec.price_min) / rec.price_min * 100
            else:
                rec.price_spread = 0
            
            best = min(prices, key=lambda p: p.price_per_ml)
            rec.best_supplier_id = best.supplier_id.id
            rec.best_supplier_price_id = best.id
            rec.best_price = best.price_per_ml
            
            variations = [p.price_variation for p in prices if p.price_variation]
            rec.avg_price_variation = sum(variations) / len(variations) if variations else 0
    
    @api.depends('product_tmpl_id')
    def _compute_product_id(self):
        for rec in self:
            if rec.product_tmpl_id:
                rec.product_id = rec.product_tmpl_id.product_variant_id
            else:
                rec.product_id = False
    
    @api.depends('best_supplier_price_id', 'best_supplier_price_id.image_url',
                 'best_supplier_price_id.datasheet_url')
    def _compute_best_media(self):
        for rec in self:
            if rec.best_supplier_price_id:
                rec.best_image_url = rec.best_supplier_price_id.image_url
                rec.best_datasheet_url = rec.best_supplier_price_id.datasheet_url
            else:
                rec.best_image_url = False
                rec.best_datasheet_url = False
    
    # =========================================================================
    # ACTIONS
    # =========================================================================
    
    def action_create_odoo_product(self):
        """Crée ou met à jour un produit Odoo depuis ce câble maître
        
        - Nom produit = "Câble TYPE CONFIG SECTION" (ex: Câble R2V 3G1,5)
        - Référence = "TYPE+CONFIG+SECTION" sans espace (ex: R2V3G1,5)
        - Onglet Achats = liste des fournisseurs avec prix
        - Fiche technique = URL depuis les lignes tarif
        """
        self.ensure_one()
        
        if self.product_tmpl_id:
            # Mettre à jour le produit existant
            self._update_odoo_product()
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'product.template',
                'res_id': self.product_tmpl_id.id,
                'view_mode': 'form',
            }
        
        # Générer le nom et la référence
        product_name = self._generate_product_name()  # "Câble R2V 3G1,5"
        product_ref = self._generate_product_reference()  # "R2V3G1,5"
        
        # Construire la description technique
        description = self._build_technical_description()
        
        # Récupérer les URLs des fiches techniques depuis les lignes de tarif
        datasheet_url, dop_url = self._get_best_document_urls()
        
        product_vals = {
            'name': product_name,
            'default_code': product_ref,
            'type': 'consu',
            'purchase_ok': True,
            'sale_ok': False,
            'categ_id': self.env.ref('product.product_category_all').id,
            'description_purchase': description,
            # Lien vers le câble maître
            'cable_master_id': self.id,
            # Informations techniques
            'cable_type_code': self.cable_type_code,
            'cable_config': self.conductor_config,
            'cable_section': self.section,
            # URLs documents
            'datasheet_url': datasheet_url,
            'dop_url': dop_url,
        }
        
        # Prix standard = meilleur prix
        if self.best_price:
            product_vals['standard_price'] = self.best_price
        
        # Récupérer l'image depuis le meilleur fournisseur
        if self.best_image_url:
            image_data = self._fetch_image(self.best_image_url)
            if image_data:
                product_vals['image_1920'] = image_data
        
        # Créer le produit
        product = self.env['product.template'].create(product_vals)
        self.product_tmpl_id = product.id
        
        # Créer les lignes fournisseurs dans l'onglet Achats
        self._create_supplier_infos(product)
        
        # Mettre à jour le nom du câble maître
        self.name = product_name
        
        _logger.info(f"Produit Odoo créé: {product_name} [{product_ref}] (ID: {product.id})")
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': product.id,
            'view_mode': 'form',
        }
    
    def _generate_product_name(self):
        """Génère le nom du produit: "Câble TYPE CONFIG SECTION"
        
        Exemples:
        - Câble R2V 3G1,5
        - Câble AR2V 1X50
        - Câble H07V-U 2,5
        - Câble CUIVRE-NU 1X35
        """
        parts = ['Câble']
        
        # Type
        if self.cable_type_code:
            parts.append(self.cable_type_code.upper().replace(' ', ''))
        
        # Config (3G, 4X, 1X, etc.)
        if self.conductor_config:
            parts.append(self.conductor_config)
        elif self.nb_conductors == 1:
            # Pour mono-conducteur sans config explicite
            if self.cable_type_code and 'CUIVRE' in self.cable_type_code.upper():
                parts.append('1X')
        
        # Section
        if self.section_text:
            parts.append(self.section_text)
        
        return ' '.join(parts) if len(parts) > 1 else f"Câble-{self.id}"
    
    def _generate_product_reference(self):
        """Génère la référence du produit: "TYPE+CONFIG+SECTION" sans espace
        
        Exemples:
        - R2V3G1,5
        - AR2V1X50
        - H07V-U2,5
        """
        parts = []
        
        # Type
        if self.cable_type_code:
            parts.append(self.cable_type_code.upper().replace(' ', ''))
        
        # Config (3G, 4X, 1X, etc.)
        if self.conductor_config:
            parts.append(self.conductor_config)
        elif self.nb_conductors == 1:
            if self.cable_type_code and 'CUIVRE' in self.cable_type_code.upper():
                parts.append('1X')
        
        # Section
        if self.section_text:
            parts.append(self.section_text)
        
        return ''.join(parts) if parts else f"CABLE-{self.id}"
    
    def _build_technical_description(self):
        """Construit la description technique du produit"""
        lines = [
            f"Type: {self.cable_type_code or '-'}",
            f"Configuration: {self.conductor_config or '-'}",
            f"Section: {self.section} mm²",
        ]
        
        if self.conductor_material:
            mat = 'Cuivre' if self.conductor_material == 'copper' else 'Aluminium'
            lines.append(f"Matériau: {mat}")
        
        if self.norme:
            lines.append(f"Norme: {self.norme}")
        
        return "\n".join(lines)
    
    def _get_best_document_urls(self):
        """Récupère les meilleures URLs de documents depuis les lignes de tarif
        
        Priorité au fournisseur avec le meilleur prix qui a une fiche technique
        
        Returns:
            tuple (datasheet_url, dop_url)
        """
        datasheet_url = False
        dop_url = False
        
        # Chercher dans les lignes de tarif (triées par prix)
        lines_with_docs = self.pricelist_line_ids.filtered(
            lambda l: l.datasheet_url or l.dop_url
        ).sorted(key=lambda l: l.price_per_ml if l.price_per_ml > 0 else 999999)
        
        for line in lines_with_docs:
            if not datasheet_url and line.datasheet_url:
                datasheet_url = line.datasheet_url
            if not dop_url and line.dop_url:
                dop_url = line.dop_url
            if datasheet_url and dop_url:
                break
        
        # Chercher aussi dans supplier_price_ids
        if not datasheet_url or not dop_url:
            prices_with_docs = self.supplier_price_ids.filtered(
                lambda p: p.datasheet_url or p.active
            ).sorted(key=lambda p: p.price_per_ml if p.price_per_ml > 0 else 999999)
            
            for sp in prices_with_docs:
                if not datasheet_url and hasattr(sp, 'datasheet_url') and sp.datasheet_url:
                    datasheet_url = sp.datasheet_url
                if datasheet_url and dop_url:
                    break
        
        return datasheet_url, dop_url
    
    def _create_supplier_infos(self, product_tmpl):
        """Crée les lignes fournisseurs dans l'onglet Achats du produit
        
        Utilise product.supplierinfo pour remplir l'onglet Achats
        """
        SupplierInfo = self.env['product.supplierinfo']
        
        # Collecter les fournisseurs uniques avec leur meilleur prix
        suppliers_data = {}
        
        # Depuis les lignes de tarif (pricelist_line_ids)
        for line in self.pricelist_line_ids.filtered(lambda l: l.price_per_ml > 0):
            supplier = line.supplier_id
            if not supplier or not supplier.partner_id:
                continue
            
            partner_id = supplier.partner_id.id
            
            # Garder le meilleur prix pour chaque fournisseur
            if partner_id not in suppliers_data or line.price_per_ml < suppliers_data[partner_id]['price']:
                suppliers_data[partner_id] = {
                    'partner_id': partner_id,
                    'price': line.price_per_ml,
                    'product_code': line.reference,
                    'product_name': line.designation,
                    'min_qty': 1.0,
                }
        
        # Depuis supplier_price_ids (nouveau modèle)
        for sp in self.supplier_price_ids.filtered(lambda s: s.price_per_ml > 0 and s.active):
            supplier = sp.supplier_id
            if not supplier or not supplier.partner_id:
                continue
            
            partner_id = supplier.partner_id.id
            
            if partner_id not in suppliers_data or sp.price_per_ml < suppliers_data[partner_id]['price']:
                suppliers_data[partner_id] = {
                    'partner_id': partner_id,
                    'price': sp.price_per_ml,
                    'product_code': sp.supplier_reference,
                    'product_name': sp.supplier_designation,
                    'min_qty': 1.0,
                }
        
        # Créer les product.supplierinfo
        for data in suppliers_data.values():
            SupplierInfo.create({
                'product_tmpl_id': product_tmpl.id,
                'partner_id': data['partner_id'],
                'price': data['price'],
                'product_code': data.get('product_code') or '',
                'product_name': data.get('product_name') or '',
                'min_qty': data.get('min_qty', 1.0),
            })
        
        _logger.info(f"Créé {len(suppliers_data)} fournisseurs pour {product_tmpl.name}")
    
    def _update_odoo_product(self):
        """Met à jour le produit Odoo existant avec les nouvelles informations"""
        if not self.product_tmpl_id:
            return
        
        product_name = self._generate_product_name()
        product_ref = self._generate_product_reference()
        description = self._build_technical_description()
        
        vals = {
            'name': product_name,
            'default_code': product_ref,
            'description_purchase': description,
        }
        
        if self.best_price:
            vals['standard_price'] = self.best_price
        
        self.product_tmpl_id.write(vals)
        
        # Mettre à jour les fournisseurs
        # Supprimer les anciens et recréer
        self.product_tmpl_id.seller_ids.unlink()
        self._create_supplier_infos(self.product_tmpl_id)
        
        # Mettre à jour le nom du câble maître
        if self.name != product_name:
            self.name = product_name
    
    def _fetch_image(self, url):
        """Télécharge une image depuis une URL et retourne les données base64"""
        if not url:
            return False
        try:
            import requests
            import base64
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return base64.b64encode(response.content)
        except Exception as e:
            _logger.warning(f"Impossible de télécharger l'image {url}: {e}")
        return False
    
    def action_view_comparison(self):
        """Voir la comparaison des prix fournisseurs"""
        self.ensure_one()
        if self.supplier_price_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': f'Comparaison - {self.name}',
                'res_model': 'cable.supplier.price',
                'view_mode': 'list,form',
                'domain': [('cable_master_id', '=', self.id)],
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': f'Comparaison - {self.name}',
                'res_model': 'cable.pricelist.line',
                'view_mode': 'list,form',
                'domain': [('master_product_id', '=', self.id)],
                'context': {'search_default_group_by_supplier': 1},
            }
    
    def action_view_price_history(self):
        """Voir l'historique des prix"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Historique prix - {self.name}',
            'res_model': 'cable.pricelist.line',
            'view_mode': 'pivot,graph,list',
            'domain': [('master_product_id', '=', self.id)],
        }
    
    # =========================================================================
    # BUSINESS METHODS
    # =========================================================================
    
    @api.model
    def find_or_create_from_designation(self, designation, config_section=None):
        """Trouve ou crée un câble maître depuis une désignation
        
        Args:
            designation: Texte complet (ex: "R2V 3G1,5 MM²")
            config_section: Configuration+Section du fichier Excel (ex: "3G1,5")
        
        Returns:
            cable.product.master record ou False
        """
        if not designation:
            return self.browse()
        
        # Extraire le type
        type_code = self._extract_type_code(designation)
        if not type_code:
            _logger.warning(f"Type non reconnu dans: {designation}")
            return self.browse()
        
        # Extraire config et section
        nb_cond, has_ground, section = self._parse_config_section(config_section or designation)
        
        if not section:
            _logger.warning(f"Section non trouvée dans: {designation} / {config_section}")
            return self.browse()
        
        # Construire la clé de matching
        section_text = str(section).replace('.', ',')
        if section_text.endswith(',0'):
            section_text = section_text[:-2]
        
        if nb_cond > 1:
            config = f"{nb_cond}{'G' if has_ground else 'X'}"
            matching_key = f"{type_code}-{config}-{section_text}"
        else:
            matching_key = f"{type_code}--{section_text}"
        
        # Chercher existant
        existing = self.search([('matching_key', '=', matching_key)], limit=1)
        if existing:
            return existing
        
        # Créer nouveau
        return self.create({
            'name': designation,
            'cable_type_code': type_code,
            'nb_conductors': nb_cond,
            'has_ground': has_ground,
            'section': section,
        })
    
    def _extract_type_code(self, text):
        """Extrait le code type depuis un texte"""
        if not text:
            return ''
        
        text = text.upper()
        
        # Patterns ordonnés du plus spécifique au plus général
        patterns = [
            (r'(FR-N1X1G1-[URK])', 'FR-N1X1G1'),
            (r'(H07\s*V-[URK])', 'H07V'),
            (r'(H07\s*Z1-[UK])', 'H07Z1'),
            (r'(H05\s*V-[VK])', 'H05V'),
            (r'(H05\s*Z1-[K])', 'H05Z1'),
            (r'(H05\s*RN-F)', 'H05RN-F'),
            (r'(H07\s*RN-F)', 'H07RN-F'),
            (r'(AR2V)', 'AR2V'),
            (r'(R2V)', 'R2V'),
            (r'(U-?1000\s*R2V)', 'U1000R2V'),
            (r'(U-?1000\s*AR2V)', 'U1000AR2V'),
            (r'(CUIVRE\s*NU)', 'CUIVRE-NU'),
            (r'(CR1-C1)', 'CR1-C1'),
            (r'(C2X-C1)', 'C2X-C1'),
            (r'(SYS1)', 'SYS1'),
            (r'(SYT1)', 'SYT1'),
            (r'(RVFV)', 'RVFV'),
        ]
        
        for pattern, type_code in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).replace(' ', '')
        
        return ''
    
    def _parse_config_section(self, text):
        """Parse une configuration+section
        
        Args:
            text: ex: "3G1,5" ou "1X50" ou "2,5"
        
        Returns:
            tuple (nb_conductors, has_ground, section)
        """
        if not text:
            return (1, True, 0)
        
        text = text.upper().strip()
        
        # Pattern: [nb][G ou X][section]
        # Ex: 3G1,5 -> (3, True, 1.5)
        # Ex: 1X50 -> (1, False, 50)
        # Ex: 2,5 -> (1, True, 2.5)
        
        match = re.match(r'^(\d+)([GX])([\d,\.]+)$', text)
        if match:
            nb = int(match.group(1))
            has_g = match.group(2) == 'G'
            section = float(match.group(3).replace(',', '.'))
            return (nb, has_g, section)
        
        # Juste section (fil simple)
        match = re.match(r'^([\d,\.]+)$', text)
        if match:
            section = float(match.group(1).replace(',', '.'))
            return (1, True, section)
        
        # Extraire section depuis texte plus complexe
        match = re.search(r'(\d+)[,\.]?(\d*)\s*(?:MM²|MM2)?', text)
        if match:
            section_str = match.group(1)
            if match.group(2):
                section_str += '.' + match.group(2)
            try:
                section = float(section_str)
                
                # Chercher nb conducteurs
                nb_match = re.search(r'^(\d+)[GX]', text)
                if nb_match:
                    nb = int(nb_match.group(1))
                    has_g = 'G' in text[:5]
                    return (nb, has_g, section)
                
                return (1, True, section)
            except:
                pass
        
        return (1, True, 0)
    
    _sql_constraints = [
        ('matching_key_unique', 'UNIQUE(matching_key)', 
         'Un câble maître avec cette clé existe déjà (TYPE-CONFIG-SECTION).')
    ]
