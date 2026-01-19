# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class CableType(models.Model):
    """Types de câbles électriques (R2V, AR2V, H07V-U, etc.)"""
    _name = 'cable.type'
    _description = 'Type de câble électrique'
    _order = 'sequence, name'

    name = fields.Char(
        string='Nom',
        required=True,
        help='Nom complet du type (ex: U-1000 R2V)'
    )
    code = fields.Char(
        string='Code',
        required=True,
        help='Code court (ex: R2V)'
    )
    sequence = fields.Integer(string='Séquence', default=10)
    
    # Catégorie (depuis fichier TURQUAND)
    category = fields.Selection([
        ('fil_rigide', 'Fil rigide'),
        ('fil_souple', 'Fil souple'),
        ('cable_rigide', 'Câble industriel rigide'),
        ('cable_souple', 'Câble industriel souple'),
        ('securite_incendie', 'Sécurité incendie'),
        ('telephonique', 'Téléphonique / Data'),
    ], string='Catégorie')
    
    # Patterns de reconnaissance
    pattern_regex = fields.Char(
        string='Pattern Regex',
        help='Expression régulière pour détecter ce type dans les désignations'
    )
    
    # Caractéristiques
    conductor_material = fields.Selection([
        ('copper', 'Cuivre'),
        ('aluminum', 'Aluminium'),
        ('copper_tinned', 'Cuivre étamé'),
    ], string='Matériau conducteur')
    
    insulation_type = fields.Selection([
        ('pvc', 'PVC'),
        ('xlpe', 'XLPE (PR)'),
        ('rubber', 'Caoutchouc'),
        ('silicone', 'Silicone'),
        ('mineral', 'Minéral'),
    ], string='Type isolation')
    
    flexibility = fields.Selection([
        ('rigid', 'Rigide'),
        ('flexible', 'Souple'),
        ('extra_flexible', 'Extra souple'),
    ], string='Flexibilité')
    
    voltage_class = fields.Selection([
        ('bt', 'Basse Tension (< 1kV)'),
        ('hta', 'Moyenne Tension (1-36kV)'),
        ('htb', 'Haute Tension (> 36kV)'),
    ], string='Classe de tension', default='bt')
    
    norme = fields.Char(
        string='Norme',
        help='Norme de référence (ex: NF C32-321)'
    )
    
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Actif', default=True)
    
    # Compteurs
    master_product_count = fields.Integer(
        string='Produits maîtres',
        compute='_compute_counts'
    )
    
    @api.depends()
    def _compute_counts(self):
        for record in self:
            record.master_product_count = self.env['cable.product.master'].search_count([
                ('cable_type_id', '=', record.id)
            ])
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Le code du type de câble doit être unique.')
    ]
    
    @api.model
    def init_default_types(self):
        """Initialise les types de câbles par défaut (sans doublons)
        
        Cette méthode peut être appelée manuellement ou via un bouton.
        Elle ne crée que les types qui n'existent pas encore.
        """
        default_types = [
            # FILS RIGIDES
            {'code': 'H07V-U', 'name': 'H07 V-U - Fil rigide PVC', 'category': 'fil_rigide', 
             'conductor_material': 'copper', 'flexibility': 'rigid', 'sequence': 10},
            {'code': 'H07V-R', 'name': 'H07 V-R - Fil rigide PVC grosses sections', 'category': 'fil_rigide',
             'conductor_material': 'copper', 'flexibility': 'rigid', 'sequence': 11},
            {'code': 'H07Z1-U', 'name': 'H07 Z1-U - Fil rigide sans halogène', 'category': 'fil_rigide',
             'conductor_material': 'copper', 'flexibility': 'rigid', 'sequence': 12},
            
            # FILS SOUPLES
            {'code': 'H05V-K', 'name': 'H05 V-K - Fil souple PVC', 'category': 'fil_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 20},
            {'code': 'H07V-K', 'name': 'H07 V-K - Fil souple PVC', 'category': 'fil_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 21},
            {'code': 'H05Z1-K', 'name': 'H05 Z1-K - Fil souple sans halogène', 'category': 'fil_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 22},
            {'code': 'H07Z1-K', 'name': 'H07 Z1-K - Fil souple sans halogène', 'category': 'fil_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 23},
            {'code': 'H05VV-F', 'name': 'H05 VV-F - Câble souple PVC', 'category': 'fil_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 24},
            {'code': 'H05RN-F', 'name': 'H05 RN-F - Câble caoutchouc léger', 'category': 'fil_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 25},
            
            # CÂBLES INDUSTRIELS RIGIDES
            {'code': 'CUIVRE-NU', 'name': 'Cuivre Nu Recuit', 'category': 'cable_rigide',
             'conductor_material': 'copper', 'flexibility': 'rigid', 'sequence': 30},
            {'code': 'R2V', 'name': 'R2V - Câble rigide U1000', 'category': 'cable_rigide',
             'conductor_material': 'copper', 'flexibility': 'rigid', 'norme': 'NF C32-321', 'sequence': 31},
            {'code': 'AR2V', 'name': 'AR2V - Câble rigide aluminium U1000', 'category': 'cable_rigide',
             'conductor_material': 'aluminum', 'flexibility': 'rigid', 'norme': 'NF C32-321', 'sequence': 32},
            {'code': 'U1000R2V', 'name': 'U-1000 R2V', 'category': 'cable_rigide',
             'conductor_material': 'copper', 'flexibility': 'rigid', 'sequence': 33},
            {'code': 'RVFV', 'name': 'RVFV - Câble armé acier', 'category': 'cable_rigide',
             'conductor_material': 'copper', 'flexibility': 'rigid', 'sequence': 70},
            
            # CÂBLES INDUSTRIELS SOUPLES
            {'code': 'H07RN-F', 'name': 'H07 RN-F - Câble caoutchouc industriel', 'category': 'cable_souple',
             'conductor_material': 'copper', 'flexibility': 'flexible', 'sequence': 40},
            
            # SÉCURITÉ INCENDIE
            {'code': 'SYS1', 'name': 'SYS1 - Câble alarme incendie', 'category': 'securite_incendie', 'sequence': 50},
            {'code': 'SYT1', 'name': 'SYT1 - Câble téléphonique sécurité', 'category': 'securite_incendie', 'sequence': 51},
            {'code': 'FR-N1X1G1-U', 'name': 'FR-N1X1G1 - Câble résistant au feu', 'category': 'securite_incendie', 'sequence': 52},
            {'code': 'CR1-C1', 'name': 'CR1-C1 - Câble résistant au feu', 'category': 'securite_incendie', 'sequence': 53},
            {'code': 'C2X-C1', 'name': 'C2X-C1 - Câble résistant au feu sans halogène', 'category': 'securite_incendie', 'sequence': 54},
            
            # TÉLÉPHONIQUE / DATA
            {'code': 'LIYCY', 'name': 'LIYCY - Câble blindé data', 'category': 'telephonique', 'sequence': 60},
        ]
        
        created = 0
        for type_data in default_types:
            existing = self.search([('code', '=', type_data['code'])], limit=1)
            if not existing:
                self.create(type_data)
                created += 1
                _logger.info(f"Type de câble créé: {type_data['code']}")
        
        _logger.info(f"Initialisation types de câbles: {created} créés sur {len(default_types)}")
        return created
