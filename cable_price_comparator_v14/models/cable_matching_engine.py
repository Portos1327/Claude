# -*- coding: utf-8 -*-

from odoo import models, api
import re
import logging

_logger = logging.getLogger(__name__)


class CableMatchingEngine(models.AbstractModel):
    """Moteur de correspondance intelligent pour câbles électriques"""
    _name = 'cable.matching.engine'
    _description = 'Moteur de matching câbles'
    
    # Patterns de reconnaissance des types de câbles
    CABLE_TYPE_PATTERNS = [
        # Industriels rigides
        (r'\bU[\s-]*1000[\s-]*R2V\b', 'R2V', 'Cuivre rigide U-1000'),
        (r'\bR2V\b', 'R2V', 'Cuivre rigide'),
        (r'\bU[\s-]*1000[\s-]*AR2V\b', 'AR2V', 'Alu rigide U-1000'),
        (r'\bAR2V\b', 'AR2V', 'Alu rigide'),
        
        # Fils domestiques rigides
        (r'\bH07[\s-]*V[\s-]*U\b', 'H07V-U', 'Fil rigide'),
        (r'\bH07[\s-]*V[\s-]*R\b', 'H07V-R', 'Fil rigide fort'),
        (r'\bH07[\s-]*Z1[\s-]*U\b', 'H07Z1-U', 'Fil rigide halogène'),
        
        # Fils souples
        (r'\bH07[\s-]*V[\s-]*K\b', 'H07V-K', 'Fil souple'),
        (r'\bH05[\s-]*V[\s-]*K\b', 'H05V-K', 'Fil souple fin'),
        
        # Câbles souples
        (r'\bH05[\s-]*VV[\s-]*F\b', 'H05VV-F', 'Câble souple'),
        (r'\bH03[\s-]*VV[\s-]*F\b', 'H03VV-F', 'Câble léger'),
        (r'\bH07[\s-]*RN[\s-]*F\b', 'H07RN-F', 'Caoutchouc'),
        
        # Industriels
        (r'\bFR[\s-]*N[\s-]*05[\s-]*VV[\s-]*U\b', 'FRN05VV-U', 'Industriel rigide'),
        (r'\bFR[\s-]*N[\s-]*07[\s-]*V[\s-]*AR\b', 'FRN07V-AR', 'Industriel alu'),
        
        # Incendie
        (r'\bCR1[\s-]*C1\b', 'CR1-C1', 'Incendie CR1'),
        (r'\bC2\b', 'C2', 'Incendie C2'),
        
        # Torsades
        (r'\bTORS(?:ADE|\.?)[\s-]*(?:DIST|BRANCH)?\b', 'TORSADE', 'Torsade'),
        (r'\bHN[\s-]*33\b', 'HN33', 'BT souterrain'),
        
        # HTA
        (r'\bHTA\b', 'HTA', 'Moyenne tension'),
        (r'\bS26\b', 'S26', 'HTA souterrain'),
        
        # Spéciaux
        (r'\bÖLFLEX\b', 'ÖLFLEX', 'Lapp industriel'),
        (r'\bNYY\b', 'NYY', 'Allemand'),
        (r'\bAST(?:ER)?\b', 'ASTER', 'Aérien alu'),
    ]
    
    # Patterns pour extraire les caractéristiques
    CONFIG_PATTERNS = [
        # Format standard: 3G2,5 ou 3x2,5 ou 3X2.5
        (r'(\d+)\s*[GgXx]\s*(\d+(?:[,\.]\d+)?)', 'standard'),
        # Format avec neutre: 3x95+50
        (r'(\d+)\s*[Xx]\s*(\d+(?:[,\.]\d+)?)\s*\+\s*(\d+)', 'avec_neutre'),
        # Format simple section: 1X240 ou 1x240
        (r'1\s*[Xx]\s*(\d+)', 'mono'),
    ]
    
    SECTION_PATTERN = r'(\d+(?:[,\.]\d+)?)\s*(?:MM²|mm²|mm2|MM2)'
    
    COLOR_PATTERNS = {
        'BLEU': ['BLEU', 'BL', 'BLUE'],
        'ROUGE': ['ROUGE', 'RG', 'RED'],
        'VERT': ['VERT', 'VT', 'V/J', 'V/JAUNE', 'GREEN'],
        'JAUNE': ['JAUNE', 'JN', 'YELLOW'],
        'NOIR': ['NOIR', 'NR', 'BLACK'],
        'MARRON': ['MARRON', 'MR', 'BROWN'],
        'GRIS': ['GRIS', 'GR', 'GREY', 'GRAY'],
        'ORANGE': ['ORANGE', 'OR'],
        'BLANC': ['BLANC', 'BC', 'WHITE'],
        'VIOLET': ['VIOLET', 'VI', 'PURPLE'],
    }
    
    NORME_PATTERNS = [
        (r'NF\s*C\s*32[\s-]*321', 'NF C32-321'),
        (r'NF\s*C\s*33[\s-]*209', 'NF C33-209'),
        (r'NF\s*C\s*33[\s-]*210', 'NF C33-210'),
        (r'NF\s*C\s*33[\s-]*226', 'NF C33-226'),
        (r'ENEDIS', 'ENEDIS'),
        (r'HM[\s-]*24', 'ENEDIS HM-24'),
    ]
    
    @api.model
    def extract_characteristics(self, designation):
        """
        Extrait les caractéristiques techniques d'une désignation de câble.
        
        Returns:
            dict: {
                'type_code': str,     # Code type (R2V, H07V-U...)
                'type_name': str,     # Nom complet du type
                'section': float,     # Section en mm²
                'nb_conductors': int, # Nombre de conducteurs
                'config': str,        # Configuration (3G2,5)
                'color': str,         # Couleur si applicable
                'norme': str,         # Norme si détectée
            }
        """
        if not designation:
            return {}
        
        result = {}
        text = designation.upper()
        
        # 1. Détecter le type de câble
        for pattern, code, name in self.CABLE_TYPE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result['type_code'] = code
                result['type_name'] = name
                break
        
        # 2. Extraire la configuration des conducteurs
        for pattern, format_type in self.CONFIG_PATTERNS:
            match = re.search(pattern, text)
            if match:
                if format_type == 'standard':
                    nb_cond = int(match.group(1))
                    section = float(match.group(2).replace(',', '.'))
                    result['nb_conductors'] = nb_cond
                    result['section'] = section
                    result['config'] = f"{nb_cond}G{section}".replace('.', ',')
                elif format_type == 'avec_neutre':
                    nb_cond = int(match.group(1))
                    section = float(match.group(2).replace(',', '.'))
                    neutre = match.group(3)
                    result['nb_conductors'] = nb_cond + 1
                    result['section'] = section
                    result['config'] = f"{nb_cond}x{section}+{neutre}".replace('.', ',')
                elif format_type == 'mono':
                    section = float(match.group(1))
                    result['nb_conductors'] = 1
                    result['section'] = section
                    result['config'] = f"1x{section}"
                break
        
        # 3. Extraire la section si pas trouvée
        if 'section' not in result:
            match = re.search(self.SECTION_PATTERN, text, re.IGNORECASE)
            if match:
                result['section'] = float(match.group(1).replace(',', '.'))
        
        # 4. Détecter la couleur
        for color_name, patterns in self.COLOR_PATTERNS.items():
            for pattern in patterns:
                if re.search(rf'\b{pattern}\b', text):
                    result['color'] = color_name
                    break
            if 'color' in result:
                break
        
        # 5. Détecter la norme
        for pattern, norme in self.NORME_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                result['norme'] = norme
                break
        
        return result
    
    @api.model
    def normalize_reference(self, reference):
        """Normalise une référence pour comparaison"""
        if not reference:
            return ''
        ref = str(reference).upper().strip()
        ref = re.sub(r'[^A-Z0-9]', '', ref)
        return ref
    
    @api.model
    def build_matching_key(self, characteristics):
        """Construit une clé de matching à partir des caractéristiques"""
        parts = []
        if characteristics.get('type_code'):
            parts.append(characteristics['type_code'].upper())
        if characteristics.get('config'):
            config = characteristics['config'].upper()
            config = config.replace(',', '.').replace('X', 'G')
            parts.append(config)
        if characteristics.get('section') and 'config' not in characteristics:
            parts.append(f"{characteristics['section']:.1f}")
        return '|'.join(parts) if parts else None
    
    @api.model
    def find_best_match(self, pricelist_line):
        """
        Trouve la meilleure correspondance pour une ligne de tarif.
        
        Args:
            pricelist_line: record cable.pricelist.line
            
        Returns:
            dict or None: {
                'master_product_id': int,
                'score': int,
                'method': str,
                'details': str,
            }
        """
        MasterProduct = self.env['cable.product.master']
        
        results = []
        
        # Méthode 1: Correspondance exacte par référence
        if pricelist_line.reference:
            ref_norm = self.normalize_reference(pricelist_line.reference)
            master = MasterProduct.search([
                ('reference_unified', '=', ref_norm)
            ], limit=1)
            if master:
                results.append({
                    'master_product_id': master.id,
                    'score': 100,
                    'method': 'exact_ref',
                    'details': f"Référence exacte: {pricelist_line.reference}",
                })
        
        # Méthode 2: Correspondance par EAN
        if pricelist_line.ean:
            # Chercher dans les autres lignes avec même EAN
            other_lines = self.env['cable.pricelist.line'].search([
                ('ean', '=', pricelist_line.ean),
                ('master_product_id', '!=', False),
                ('id', '!=', pricelist_line.id),
            ], limit=1)
            if other_lines:
                results.append({
                    'master_product_id': other_lines.master_product_id.id,
                    'score': 100,
                    'method': 'ean',
                    'details': f"Code EAN: {pricelist_line.ean}",
                })
        
        # Méthode 3: Correspondance par clé de matching (caractéristiques)
        if pricelist_line.matching_key:
            master = MasterProduct.search([
                ('matching_key', '=', pricelist_line.matching_key)
            ], limit=1)
            if master:
                results.append({
                    'master_product_id': master.id,
                    'score': 85,
                    'method': 'characteristics',
                    'details': f"Clé matching: {pricelist_line.matching_key}",
                })
        
        # Méthode 4: Correspondance par type + section
        if pricelist_line.cable_type_code and pricelist_line.section:
            masters = MasterProduct.search([
                ('cable_type_code', '=ilike', pricelist_line.cable_type_code),
                ('section', '=', pricelist_line.section),
            ])
            if len(masters) == 1:
                results.append({
                    'master_product_id': masters.id,
                    'score': 75,
                    'method': 'characteristics',
                    'details': f"Type {pricelist_line.cable_type_code} section {pricelist_line.section}",
                })
        
        # Retourner le meilleur résultat
        if results:
            return max(results, key=lambda x: x['score'])
        
        return None
    
    @api.model
    def run_matching_batch(self, pricelist_ids=None, line_ids=None, create_masters=True):
        """
        Lance le matching pour un lot de lignes.
        
        Args:
            pricelist_ids: list of int - IDs des tarifs à traiter
            line_ids: list of int - IDs des lignes spécifiques
            create_masters: bool - Créer les produits maîtres si inexistants
            
        Returns:
            dict: {
                'processed': int,
                'matched': int,
                'created': int,
                'failed': int,
            }
        """
        stats = {'processed': 0, 'matched': 0, 'created': 0, 'failed': 0}
        
        # Récupérer les lignes à traiter
        domain = [('master_product_id', '=', False)]
        if pricelist_ids:
            domain.append(('pricelist_id', 'in', pricelist_ids))
        if line_ids:
            domain.append(('id', 'in', line_ids))
        
        lines = self.env['cable.pricelist.line'].search(domain)
        total = len(lines)
        
        _logger.info(f"Démarrage matching pour {total} lignes")
        
        MasterProduct = self.env['cable.product.master']
        
        for i, line in enumerate(lines):
            stats['processed'] += 1
            
            try:
                # Extraire les caractéristiques si pas fait
                if not line.cable_type_code:
                    characteristics = self.extract_characteristics(line.designation)
                    line.write({
                        'cable_type_code': characteristics.get('type_code'),
                        'section': characteristics.get('section'),
                        'nb_conductors': characteristics.get('nb_conductors'),
                        'conductor_config': characteristics.get('config'),
                        'color': characteristics.get('color'),
                        'norme': characteristics.get('norme'),
                    })
                
                # Chercher correspondance
                result = self.find_best_match(line)
                
                if result:
                    line.write({
                        'master_product_id': result['master_product_id'],
                        'match_score': result['score'],
                        'match_method': result['method'],
                    })
                    stats['matched'] += 1
                
                elif create_masters and line.cable_type_code:
                    # Créer un nouveau produit maître
                    characteristics = {
                        'type_code': line.cable_type_code,
                        'section': line.section,
                        'nb_conductors': line.nb_conductors,
                        'config': line.conductor_config,
                    }
                    master = MasterProduct.find_or_create(characteristics)
                    line.write({
                        'master_product_id': master.id,
                        'match_score': 90,
                        'match_method': 'designation',
                    })
                    stats['created'] += 1
                    stats['matched'] += 1
                
            except Exception as e:
                _logger.error(f"Erreur matching ligne {line.id}: {e}")
                stats['failed'] += 1
            
            # Log progression
            if (i + 1) % 100 == 0:
                _logger.info(f"Progression: {i + 1}/{total}")
        
        _logger.info(f"Matching terminé: {stats}")
        return stats
    
    @api.model
    def calculate_similarity(self, str1, str2):
        """Calcule un score de similarité entre deux chaînes (0-100)"""
        if not str1 or not str2:
            return 0
        
        s1 = str1.upper()
        s2 = str2.upper()
        
        if s1 == s2:
            return 100
        
        # Calcul Jaccard sur les tokens
        tokens1 = set(re.findall(r'\w+', s1))
        tokens2 = set(re.findall(r'\w+', s2))
        
        if not tokens1 or not tokens2:
            return 0
        
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        
        return int(intersection / union * 100) if union > 0 else 0
