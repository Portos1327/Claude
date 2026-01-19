# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class RexelUnitMapping(models.Model):
    _name = 'rexel.unit.mapping'
    _description = 'Correspondance Conditionnement → Unité'
    _order = 'sequence, conditionnement'
    _rec_name = 'conditionnement'

    conditionnement = fields.Char(
        string='Conditionnement',
        required=True,
        index=True,
        help='Code ou libellé du conditionnement (ex: TOU, MET, PIE, COU)'
    )
    
    unite = fields.Selection([
        ('U', 'U - Unité/Pièce'),
        ('ML', 'ML - Mètre linéaire'),
    ], string='Unité', required=True, default='U',
       help='Unité de mesure correspondante')
    
    sequence = fields.Integer(string='Séquence', default=10)
    
    active = fields.Boolean(string='Actif', default=True)
    
    description = fields.Char(
        string='Description',
        help='Description optionnelle pour comprendre cette correspondance'
    )
    
    # Statistiques
    usage_count = fields.Integer(
        string='Utilisations',
        default=0,
        help='Nombre de fois où cette correspondance a été utilisée'
    )
    
    is_system = fields.Boolean(
        string='Système',
        default=False,
        help='Correspondance système (non supprimable)'
    )
    
    _sql_constraints = [
        ('unique_conditionnement', 'UNIQUE(conditionnement)', 
         'Ce conditionnement existe déjà dans la table de correspondance !'),
    ]

    @api.model
    def init_default_mappings(self):
        """
        Initialise les correspondances par défaut.
        Appelé lors de l'installation du module.
        """
        default_mappings = [
            # Mètre linéaire
            {'conditionnement': 'TOU', 'unite': 'ML', 'description': 'Touret', 'is_system': True, 'sequence': 1},
            {'conditionnement': 'TOURET', 'unite': 'ML', 'description': 'Touret (complet)', 'is_system': True, 'sequence': 2},
            {'conditionnement': 'MET', 'unite': 'ML', 'description': 'Mètre', 'is_system': True, 'sequence': 3},
            {'conditionnement': 'METRE', 'unite': 'ML', 'description': 'Mètre (complet)', 'is_system': True, 'sequence': 4},
            {'conditionnement': 'COU', 'unite': 'ML', 'description': 'Couronne', 'is_system': True, 'sequence': 5},
            {'conditionnement': 'COURONNE', 'unite': 'ML', 'description': 'Couronne (complet)', 'is_system': True, 'sequence': 6},
            {'conditionnement': 'BOB', 'unite': 'ML', 'description': 'Bobine', 'is_system': True, 'sequence': 7},
            {'conditionnement': 'BOBINE', 'unite': 'ML', 'description': 'Bobine (complet)', 'is_system': True, 'sequence': 8},
            
            # Unité/Pièce
            {'conditionnement': 'PIE', 'unite': 'U', 'description': 'Pièce', 'is_system': True, 'sequence': 10},
            {'conditionnement': 'PIECE', 'unite': 'U', 'description': 'Pièce (complet)', 'is_system': True, 'sequence': 11},
            {'conditionnement': 'PCS', 'unite': 'U', 'description': 'Pièces', 'is_system': True, 'sequence': 12},
            {'conditionnement': 'BOI', 'unite': 'U', 'description': 'Boîte', 'is_system': True, 'sequence': 13},
            {'conditionnement': 'BOITE', 'unite': 'U', 'description': 'Boîte (complet)', 'is_system': True, 'sequence': 14},
            {'conditionnement': 'LOT', 'unite': 'U', 'description': 'Lot', 'is_system': True, 'sequence': 15},
            {'conditionnement': 'PAQ', 'unite': 'U', 'description': 'Paquet', 'is_system': True, 'sequence': 16},
            {'conditionnement': 'PAQUET', 'unite': 'U', 'description': 'Paquet (complet)', 'is_system': True, 'sequence': 17},
            {'conditionnement': 'SAC', 'unite': 'U', 'description': 'Sac', 'is_system': True, 'sequence': 18},
            {'conditionnement': 'CAR', 'unite': 'U', 'description': 'Carton', 'is_system': True, 'sequence': 19},
            {'conditionnement': 'CARTON', 'unite': 'U', 'description': 'Carton (complet)', 'is_system': True, 'sequence': 20},
            {'conditionnement': 'KIT', 'unite': 'U', 'description': 'Kit', 'is_system': True, 'sequence': 21},
            {'conditionnement': 'ENS', 'unite': 'U', 'description': 'Ensemble', 'is_system': True, 'sequence': 22},
            {'conditionnement': 'JEU', 'unite': 'U', 'description': 'Jeu', 'is_system': True, 'sequence': 23},
        ]
        
        created = 0
        for mapping in default_mappings:
            existing = self.search([('conditionnement', '=', mapping['conditionnement'])], limit=1)
            if not existing:
                self.create(mapping)
                created += 1
        
        if created:
            _logger.info(f"Correspondances unités initialisées: {created} créées")
        
        return created

    def increment_usage(self):
        """Incrémente le compteur d'utilisation"""
        for record in self:
            record.sudo().write({'usage_count': record.usage_count + 1})


class RexelUnknownConditionnement(models.Model):
    """
    Stocke les conditionnements inconnus rencontrés lors des mises à jour.
    Permet à l'utilisateur de voir lesquels doivent être ajoutés.
    """
    _name = 'rexel.unknown.conditionnement'
    _description = 'Conditionnement inconnu'
    _order = 'occurrence_count desc, last_seen desc'
    _rec_name = 'conditionnement'

    conditionnement = fields.Char(
        string='Conditionnement',
        required=True,
        index=True,
        help='Code du conditionnement inconnu'
    )
    
    occurrence_count = fields.Integer(
        string='Occurrences',
        default=1,
        help='Nombre de fois où ce conditionnement a été rencontré'
    )
    
    first_seen = fields.Datetime(
        string='Première occurrence',
        default=fields.Datetime.now,
    )
    
    last_seen = fields.Datetime(
        string='Dernière occurrence',
        default=fields.Datetime.now,
    )
    
    example_references = fields.Text(
        string='Exemples de références',
        help='Quelques références d\'articles ayant ce conditionnement'
    )
    
    suggested_unite = fields.Selection([
        ('U', 'U - Unité/Pièce'),
        ('ML', 'ML - Mètre linéaire'),
    ], string='Unité suggérée',
       help='Suggérez l\'unité pour créer la correspondance')
    
    is_resolved = fields.Boolean(
        string='Résolu',
        default=False,
        help='Cocher si une correspondance a été créée'
    )
    
    _sql_constraints = [
        ('unique_conditionnement', 'UNIQUE(conditionnement)', 
         'Ce conditionnement inconnu existe déjà !'),
    ]

    def action_create_mapping(self):
        """Crée une correspondance à partir de ce conditionnement inconnu"""
        self.ensure_one()
        
        if not self.suggested_unite:
            raise models.ValidationError("Veuillez d'abord suggérer une unité")
        
        # Créer la correspondance
        self.env['rexel.unit.mapping'].create({
            'conditionnement': self.conditionnement.upper(),
            'unite': self.suggested_unite,
            'description': f'Ajouté depuis conditionnement inconnu',
            'is_system': False,
        })
        
        # Marquer comme résolu
        self.write({'is_resolved': True})
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Correspondance créée',
                'message': f'{self.conditionnement} → {self.suggested_unite}',
                'type': 'success',
            }
        }

    @api.model
    def log_unknown(self, conditionnement, reference=None):
        """
        Enregistre un conditionnement inconnu rencontré.
        Appelé par _determine_unit_from_conditionnement.
        """
        if not conditionnement:
            return
        
        cond_upper = str(conditionnement).strip().upper()
        
        existing = self.search([('conditionnement', '=', cond_upper)], limit=1)
        
        if existing:
            # Mise à jour
            update_vals = {
                'occurrence_count': existing.occurrence_count + 1,
                'last_seen': fields.Datetime.now(),
            }
            
            # Ajouter la référence aux exemples (max 10)
            if reference:
                examples = existing.example_references or ''
                refs = [r.strip() for r in examples.split(',') if r.strip()]
                if reference not in refs and len(refs) < 10:
                    refs.append(reference)
                    update_vals['example_references'] = ', '.join(refs)
            
            existing.write(update_vals)
        else:
            # Création
            self.create({
                'conditionnement': cond_upper,
                'example_references': reference or '',
            })
