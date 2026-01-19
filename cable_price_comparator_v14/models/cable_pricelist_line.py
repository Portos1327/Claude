# -*- coding: utf-8 -*-

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
import re
import logging

_logger = logging.getLogger(__name__)


class CablePricelistLine(models.Model):
    """Ligne de tarif câble (un article fournisseur)"""
    _name = 'cable.pricelist.line'
    _description = 'Ligne de tarif câble'
    _order = 'pricelist_id, family, designation'
    _rec_name = 'display_name'

    pricelist_id = fields.Many2one(
        'cable.pricelist',
        string='Tarif',
        required=True,
        ondelete='cascade',
        index=True
    )
    supplier_id = fields.Many2one(
        related='pricelist_id.supplier_id',
        string='Fournisseur',
        store=True,
        index=True
    )
    supplier_code = fields.Char(
        related='pricelist_id.supplier_code',
        string='Code fournisseur',
        store=True
    )
    
    date_tarif = fields.Date(
        related='pricelist_id.date_validity',
        string='Date tarif',
        store=True
    )
    
    # Référence et désignation
    reference = fields.Char(
        string='Référence',
        required=True,
        index=True
    )
    reference_normalized = fields.Char(
        string='Référence normalisée',
        compute='_compute_normalized_values',
        store=True,
        index=True
    )
    designation = fields.Char(
        string='Désignation',
        required=True
    )
    designation_normalized = fields.Char(
        string='Désignation normalisée',
        compute='_compute_normalized_values',
        store=True
    )
    display_name = fields.Char(
        string='Nom affiché',
        compute='_compute_display_name',
        store=True
    )
    
    # Prix - UNITÉ PAR DÉFAUT: €/ml (mètre linéaire)
    price_gross = fields.Float(
        string='Prix brut',
        digits='Product Price'
    )
    discount = fields.Float(
        string='Remise (%)',
        digits=(5, 2)
    )
    price_net = fields.Float(
        string='Prix net',
        digits='Product Price',
        index=True
    )
    price_unit = fields.Selection([
        ('m', '€/ml'),
        ('km', '€/km'),
        ('100m', '€/100m'),
        ('unit', '€/unité'),
        ('kg', '€/kg'),
    ], string='Unité prix', default='m')  # DÉFAUT: €/ml
    
    # Prix normalisé au MÈTRE LINÉAIRE pour comparaison
    price_per_ml = fields.Float(
        string='€/ml',
        compute='_compute_price_per_ml',
        store=True,
        digits=(12, 4),
        help='Prix normalisé au mètre linéaire'
    )
    
    # Compatibilité
    price_per_km = fields.Float(
        string='€/km',
        compute='_compute_price_per_ml',
        store=True,
        digits='Product Price'
    )
    
    # Variation
    price_previous_month = fields.Float(
        string='Prix M-1 €/ml',
        digits=(12, 4)
    )
    price_variation = fields.Float(
        string='Variation (%)',
        compute='_compute_price_variation',
        store=True,
        digits=(5, 2)
    )
    price_variation_abs = fields.Float(
        string='Variation €/ml',
        compute='_compute_price_variation',
        store=True,
        digits=(12, 4)
    )
    price_trend = fields.Selection([
        ('up', '↗ Hausse'),
        ('down', '↘ Baisse'),
        ('stable', '→ Stable'),
        ('new', '✦ Nouveau'),
    ], string='Tendance', compute='_compute_price_variation', store=True)
    
    tarif_freshness = fields.Selection([
        ('current', 'Mois courant'),
        ('previous', 'Mois précédent'),
        ('old', 'Ancien'),
    ], string='Fraîcheur tarif', compute='_compute_tarif_freshness', store=True)
    
    # Informations produit
    family = fields.Char(string='Famille')
    family_code = fields.Char(string='Code famille')
    weight = fields.Float(string='Poids (kg/km)')
    ean = fields.Char(string='Code EAN', index=True)
    
    # ===========================================================
    # FABRICANT (informations du fabricant original)
    # ===========================================================
    manufacturer_ref = fields.Char(
        string='Réf. fabricant',
        help='Référence article chez le fabricant'
    )
    manufacturer_name = fields.Char(
        string='Marque/Fabricant',
        help='Nom du fabricant (Nexans, Prysmian, etc.)'
    )
    
    # ===========================================================
    # DISTRIBUTEUR (informations du distributeur)
    # ===========================================================
    distributor_ref = fields.Char(
        string='Réf. distributeur',
        help='Référence article chez le distributeur (Rexel, Sonepar, etc.)'
    )
    distributor_name = fields.Char(
        string='Distributeur',
        help='Nom du distributeur'
    )
    
    # ===========================================================
    # DOCUMENTS ET IMAGES
    # ===========================================================
    image_url = fields.Char(string='URL Image')
    datasheet_url = fields.Char(string='URL Fiche technique')
    dop_url = fields.Char(string='URL DOP')
    
    # Lien vers le produit Odoo (product.product)
    product_id = fields.Many2one(
        'product.product',
        string='Produit Odoo',
        help='Produit Odoo associé pour gestion stock/achat'
    )
    
    # Caractéristiques extraites
    cable_type_id = fields.Many2one(
        'cable.type',
        string='Type câble',
        index=True
    )
    cable_type_code = fields.Char(
        string='Code type',
        help='R2V, AR2V, H07V-U...'
    )
    
    # Configuration SANS section (ex: 3G ou 4X)
    nb_conductors = fields.Integer(
        string='Nb conducteurs',
        help='Nombre de conducteurs'
    )
    has_ground = fields.Boolean(
        string='Avec terre (G)',
        default=True,
        help='G = avec terre, X = sans terre'
    )
    conductor_config = fields.Char(
        string='Configuration',
        compute='_compute_conductor_config',
        store=True,
        help='Ex: 3G ou 4X (SANS la section)'
    )
    
    # Section séparée
    section = fields.Float(
        string='Section (mm²)',
        digits=(6, 2)
    )
    section_text = fields.Char(
        string='Section (texte)',
        compute='_compute_section_text',
        store=True
    )
    
    color = fields.Char(string='Couleur')
    norme = fields.Char(string='Norme')
    
    # Clé de matching: TYPE-CONFIG-SECTION
    matching_key = fields.Char(
        string='Clé de matching',
        compute='_compute_matching_key',
        store=True,
        index=True,
        help='TYPE-CONFIG-SECTION (ex: R2V-3G-1,5)'
    )
    
    # Correspondance produit maître
    master_product_id = fields.Many2one(
        'cable.product.master',
        string='Produit maître',
        index=True
    )
    match_score = fields.Integer(string='Score correspondance')
    match_method = fields.Selection([
        ('auto_create', 'Création automatique'),
        ('exact_key', 'Clé exacte'),
        ('exact_ref', 'Référence exacte'),
        ('ean', 'Code EAN'),
        ('characteristics', 'Caractéristiques'),
        ('manual', 'Manuel'),
    ], string='Méthode correspondance')
    is_matched = fields.Boolean(
        string='Correspondance',
        compute='_compute_is_matched',
        store=True
    )
    
    notes = fields.Text(string='Notes')
    
    # =========================================================================
    # COMPUTED FIELDS
    # =========================================================================
    
    @api.depends('reference', 'designation')
    def _compute_display_name(self):
        for line in self:
            line.display_name = f"[{line.reference}] {line.designation or ''}"[:100]
    
    @api.depends('reference', 'designation')
    def _compute_normalized_values(self):
        for line in self:
            ref = line.reference or ''
            ref = ref.upper().strip()
            ref = re.sub(r'[^A-Z0-9]', '', ref)
            line.reference_normalized = ref
            
            des = line.designation or ''
            des = des.upper().strip()
            des = re.sub(r'\s+', ' ', des)
            line.designation_normalized = des
    
    @api.depends('nb_conductors', 'has_ground')
    def _compute_conductor_config(self):
        """Génère la configuration SANS section (ex: 3G ou 4X)"""
        for line in self:
            if line.nb_conductors and line.nb_conductors > 1:
                suffix = 'G' if line.has_ground else 'X'
                line.conductor_config = f"{line.nb_conductors}{suffix}"
            else:
                line.conductor_config = ''
    
    @api.depends('section')
    def _compute_section_text(self):
        """Formate la section avec virgule"""
        for line in self:
            if line.section:
                section_str = str(line.section).replace('.', ',')
                if section_str.endswith(',0'):
                    section_str = section_str[:-2]
                line.section_text = section_str
            else:
                line.section_text = ''
    
    @api.depends('cable_type_code', 'conductor_config', 'section_text')
    def _compute_matching_key(self):
        """Clé de matching: TYPE-CONFIG-SECTION"""
        for line in self:
            parts = []
            
            if line.cable_type_code:
                type_code = line.cable_type_code.upper().strip()
                type_code = re.sub(r'\s+', '', type_code)
                parts.append(type_code)
            
            # Configuration (peut être vide pour fils simples)
            parts.append(line.conductor_config or '')
            
            if line.section_text:
                parts.append(line.section_text)
            
            if len(parts) >= 2 and parts[0] and parts[-1]:
                line.matching_key = '-'.join(parts)
            else:
                line.matching_key = False
    
    @api.depends('price_net', 'price_unit')
    def _compute_price_per_ml(self):
        """Convertit en €/ml"""
        for line in self:
            if not line.price_net:
                line.price_per_ml = 0
                line.price_per_km = 0
                continue
            
            conversions_to_ml = {
                'm': 1,
                'km': 0.001,
                '100m': 0.01,
                'unit': 1,
                'kg': 1,
            }
            factor = conversions_to_ml.get(line.price_unit, 1)
            line.price_per_ml = line.price_net * factor
            line.price_per_km = line.price_per_ml * 1000
    
    @api.depends('price_per_ml', 'price_previous_month')
    def _compute_price_variation(self):
        for line in self:
            if not line.price_previous_month:
                line.price_variation = 0
                line.price_variation_abs = 0
                line.price_trend = 'new'
            elif line.price_per_ml and line.price_previous_month:
                variation = line.price_per_ml - line.price_previous_month
                line.price_variation_abs = variation
                line.price_variation = (variation / line.price_previous_month) * 100
                
                if abs(line.price_variation) < 0.5:
                    line.price_trend = 'stable'
                elif line.price_variation > 0:
                    line.price_trend = 'up'
                else:
                    line.price_trend = 'down'
            else:
                line.price_variation = 0
                line.price_variation_abs = 0
                line.price_trend = 'new'
    
    @api.depends('date_tarif')
    def _compute_tarif_freshness(self):
        today = fields.Date.today()
        current_month_start = today.replace(day=1)
        previous_month_start = (current_month_start - relativedelta(months=1))
        
        for line in self:
            if not line.date_tarif:
                line.tarif_freshness = 'old'
            elif line.date_tarif >= current_month_start:
                line.tarif_freshness = 'current'
            elif line.date_tarif >= previous_month_start:
                line.tarif_freshness = 'previous'
            else:
                line.tarif_freshness = 'old'
    
    @api.depends('master_product_id')
    def _compute_is_matched(self):
        for line in self:
            line.is_matched = bool(line.master_product_id)
    
    # =========================================================================
    # ACTIONS
    # =========================================================================
    
    def action_extract_characteristics(self):
        """Extraire les caractéristiques de la désignation et créer le produit maître"""
        for line in self:
            designation = line.designation or ''
            
            # Extraire type
            type_code = self._extract_type_code(designation)
            
            # Extraire config et section
            nb_cond, has_ground, section = self._parse_designation_config(designation)
            
            # Mise à jour
            vals = {
                'cable_type_code': type_code,
                'nb_conductors': nb_cond,
                'has_ground': has_ground,
                'section': section,
            }
            
            # Chercher le type de câble
            cable_type = False
            if type_code:
                cable_type = self.env['cable.type'].search([
                    ('code', '=ilike', type_code)
                ], limit=1)
                if cable_type:
                    vals['cable_type_id'] = cable_type.id
            
            line.write(vals)
            
            # =====================================================
            # CRÉATION AUTOMATIQUE DU PRODUIT MAÎTRE
            # Si on a une clé matching valide, créer le produit maître
            # =====================================================
            if line.matching_key and not line.master_product_id:
                # Chercher produit maître existant
                master = self.env['cable.product.master'].search([
                    ('matching_key', '=', line.matching_key)
                ], limit=1)
                
                if not master:
                    # Générer le nom du produit maître depuis la clé
                    # Ex: R2V-3G-1,5 -> R2V3G1,5
                    master_name = line.matching_key.replace('-', '')
                    
                    # Créer le produit maître
                    master = self.env['cable.product.master'].create({
                        'name': master_name,
                        'cable_type_code': type_code,
                        'cable_type_id': cable_type.id if cable_type else False,
                        'nb_conductors': nb_cond,
                        'has_ground': has_ground,
                        'section': section,
                    })
                    _logger.info(f"Produit maître créé automatiquement: {master.name} ({master.matching_key})")
                
                # Lier la ligne au produit maître
                line.write({
                    'master_product_id': master.id,
                    'match_score': 100,
                    'match_method': 'auto_create',
                })
    
    def action_find_or_create_master(self):
        """Trouve ou crée le produit maître correspondant"""
        for line in self:
            if line.master_product_id:
                continue
            
            # Extraire caractéristiques si nécessaire
            if not line.cable_type_code:
                line.action_extract_characteristics()
            
            if not line.matching_key:
                continue
            
            # Chercher produit maître existant
            master = self.env['cable.product.master'].search([
                ('matching_key', '=', line.matching_key)
            ], limit=1)
            
            if not master:
                # Créer le produit maître
                master = self.env['cable.product.master'].create({
                    'name': line.designation,
                    'cable_type_code': line.cable_type_code,
                    'cable_type_id': line.cable_type_id.id if line.cable_type_id else False,
                    'nb_conductors': line.nb_conductors or 1,
                    'has_ground': line.has_ground,
                    'section': line.section,
                })
                _logger.info(f"Produit maître créé: {master.matching_key}")
            
            # Lier
            line.write({
                'master_product_id': master.id,
                'match_score': 100,
                'match_method': 'exact_key',
            })
    
    def action_create_master_product(self):
        """Créer manuellement un produit maître"""
        self.ensure_one()
        if self.master_product_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'cable.product.master',
                'res_id': self.master_product_id.id,
                'view_mode': 'form',
            }
        
        self.action_find_or_create_master()
        
        if self.master_product_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'cable.product.master',
                'res_id': self.master_product_id.id,
                'view_mode': 'form',
            }
    
    def action_view_comparison(self):
        """Voir la comparaison de prix"""
        self.ensure_one()
        if not self.master_product_id:
            return {'type': 'ir.actions.act_window_close'}
        return self.master_product_id.action_view_comparison()
    
    # =========================================================================
    # PARSING METHODS
    # =========================================================================
    
    def _extract_type_code(self, text):
        """Extrait le code type depuis une désignation"""
        if not text:
            return ''
        
        text = text.upper()
        
        patterns = [
            (r'(FR-N1X1G1-[URK])', None),
            (r'(H07\s*V-[URK])', None),
            (r'(H07\s*Z1-[UK])', None),
            (r'(H05\s*V-[VK])', None),
            (r'(H05\s*Z1-[K])', None),
            (r'(H05\s*RN-F)', None),
            (r'(H07\s*RN-F)', None),
            (r'(AR2V)', None),
            (r'(R2V)', None),
            (r'(U-?1000\s*R2V)', 'U1000R2V'),
            (r'(U-?1000\s*AR2V)', 'U1000AR2V'),
            (r'(CUIVRE\s*NU)', 'CUIVRE-NU'),
            (r'(CR1-C1)', None),
            (r'(C2X-C1)', None),
            (r'(SYS1)', None),
            (r'(SYT1)', None),
            (r'(RVFV)', None),
        ]
        
        for pattern, replacement in patterns:
            match = re.search(pattern, text)
            if match:
                result = match.group(1).replace(' ', '')
                return replacement if replacement else result
        
        return ''
    
    def _parse_designation_config(self, text):
        """Parse la désignation pour extraire config et section
        
        RÈGLES MÉTIER:
        - nG = n conducteurs AVEC terre (ex: 3G1,5)
        - nX = n conducteurs SANS terre (ex: 1X50, 4X16)
        - CUIVRE NU = toujours Config 1X, section = premier nombre
        
        Ex: "AR2V 1X50" -> nb=1, has_ground=False, section=50
        Ex: "R2V 3G1,5" -> nb=3, has_ground=True, section=1.5
        Ex: "CUIVRE NU 35 RECUIT" -> nb=1, has_ground=False, section=35
        
        Returns:
            tuple (nb_conductors, has_ground, section)
        """
        if not text:
            return (1, False, 0)
        
        text_upper = text.upper()
        
        # Fonction utilitaire pour convertir en float avec protection
        def safe_float(s):
            """Convertit une chaîne en float, retourne 0 si invalide"""
            if not s:
                return 0
            try:
                # Nettoyer la chaîne
                cleaned = s.replace(',', '.').strip()
                # Vérifier que c'est un nombre valide (pas juste des points)
                if not cleaned or cleaned == '.' or cleaned == '..' or not any(c.isdigit() for c in cleaned):
                    return 0
                return float(cleaned)
            except (ValueError, TypeError):
                return 0
        
        # =====================================================
        # CAS SPÉCIAL: CUIVRE NU - toujours Config 1X
        # Ex: "CUIVRE NU 35 RECUIT C100" -> 1X, section=35
        # =====================================================
        if 'CUIVRE' in text_upper and 'NU' in text_upper:
            # Chercher le premier nombre dans la désignation (c'est la section)
            match = re.search(r'\b(\d+(?:[,\.]\d+)?)\b', text_upper)
            if match:
                section = safe_float(match.group(1))
                if section > 0:
                    return (1, False, section)  # 1X = sans terre
            return (1, False, 0)
        
        # =====================================================
        # Pattern principal: nGsection ou nXsection
        # Ex: 3G1,5 ou 1X50 ou 4X16
        # =====================================================
        match = re.search(r'(\d+)\s*([GX])\s*(\d+(?:[,\.]\d+)?)', text_upper)
        if match:
            nb = int(match.group(1))
            has_ground = match.group(2) == 'G'  # G = avec terre, X = sans terre
            section = safe_float(match.group(3))
            if section > 0:
                return (nb, has_ground, section)
        
        # =====================================================
        # Pattern fils: section seule en mm² (ex: "2,5 MM²")
        # Pour les fils simples, on considère Config 1X par défaut
        # =====================================================
        match = re.search(r'(\d+(?:[,\.]\d+)?)\s*MM', text_upper)
        if match:
            section = safe_float(match.group(1))
            if section > 0:
                return (1, False, section)  # Fil simple = 1X
        
        # =====================================================
        # Pattern de secours: juste un nombre (section)
        # =====================================================
        match = re.search(r'\b(\d+(?:[,\.]\d+)?)\s*$', text_upper)
        if match:
            section = safe_float(match.group(1))
            if section > 0:
                return (1, False, section)
        
        return (1, False, 0)
