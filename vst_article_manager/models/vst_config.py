# -*- coding: utf-8 -*-

import os
import subprocess
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class VstConfig(models.Model):
    _name = 'vst.config'
    _description = 'Configuration VST'
    _rec_name = 'name'

    name = fields.Char(string='Nom', default='Configuration VST', readonly=True)
    
    # Chemins de configuration
    executable_path = fields.Char(
        string='Chemin de l\'exécutable',
        default=r'C:\Program Files\Odoo 18.0.20251211\server\odoo\addons\VST\BATIGEST.exe',
        help='Chemin complet vers l\'exécutable BATIGEST.exe fourni par VST'
    )
    output_folder = fields.Char(
        string='Dossier de sortie',
        default=r'C:\TARIFVST',
        help='Dossier où le fichier BATIGEST est généré'
    )
    output_filename = fields.Char(
        string='Nom du fichier',
        default='BATIGEST',
        help='Nom du fichier généré (sans extension)'
    )
    
    # Options d'import
    auto_create_product = fields.Boolean(
        string='Créer automatiquement les produits Odoo',
        default=False,
        help='Si coché, crée automatiquement un produit Odoo pour chaque article VST'
    )
    update_existing = fields.Boolean(
        string='Mettre à jour les articles existants',
        default=True,
        help='Si coché, met à jour les articles existants lors de l\'import'
    )
    create_price_history = fields.Boolean(
        string='Créer un historique des prix',
        default=True,
        help='Si coché, enregistre l\'historique des changements de prix'
    )
    
    # Fournisseur associé
    supplier_id = fields.Many2one(
        'res.partner',
        string='Fournisseur VST',
        domain="[('is_company', '=', True)]",
        help='Fournisseur Odoo associé à VST. Sera ajouté automatiquement lors de la création des produits.'
    )
    supplier_delay = fields.Integer(
        string='Délai de livraison (jours)',
        default=1,
        help='Délai de livraison par défaut pour ce fournisseur'
    )
    
    # Templates d'export
    template_beg = fields.Char(
        string='Template BEG',
        default=r'C:\Program Files\Odoo 18.0.20251211\server\templates\MAJ Base_Article - BEG avec formules V1.xlsx',
        help='Chemin du fichier template pour export Naviwest BEG'
    )
    template_niedax = fields.Char(
        string='Template NIEDAX',
        default=r'C:\Program Files\Odoo 18.0.20251211\server\templates\MAJ Base_Article - NIEDAX avec formules V1.xlsx',
        help='Chemin du fichier template pour export Naviwest NIEDAX'
    )
    template_cables = fields.Char(
        string='Template CÂBLES',
        default=r'C:\Program Files\Odoo 18.0.20251211\server\templates\MAJ Base_Article - CABLES avec formules V1.xlsx',
        help='Chemin du fichier template pour export Naviwest CÂBLES'
    )
    
    # Planification
    auto_update_enabled = fields.Boolean(
        string='Mise à jour automatique activée',
        default=False,
        help='Activer la mise à jour automatique mensuelle'
    )
    
    # Statistiques
    last_import_date = fields.Datetime(
        string='Dernière importation',
        readonly=True
    )
    last_import_count = fields.Integer(
        string='Articles importés',
        readonly=True
    )
    total_articles = fields.Integer(
        string='Total articles',
        compute='_compute_total_articles',
        store=False
    )
    total_products = fields.Integer(
        string='Produits Odoo liés',
        compute='_compute_total_articles',
        store=False
    )
    
    # Logs
    last_log = fields.Text(
        string='Dernier log',
        readonly=True
    )

    @api.model
    def get_config(self):
        """Récupère ou crée la configuration unique"""
        config = self.search([], limit=1)
        if not config:
            config = self.create({})
        return config

    @api.depends()
    def _compute_total_articles(self):
        for record in self:
            record.total_articles = self.env['vst.article'].search_count([])
            record.total_products = self.env['vst.article'].search_count([('product_id', '!=', False)])

    def action_test_executable(self):
        """Teste si l'exécutable est accessible"""
        self.ensure_one()
        if not self.executable_path:
            raise UserError(_('Le chemin de l\'exécutable n\'est pas configuré.'))
        
        if not os.path.exists(self.executable_path):
            raise UserError(_(
                'L\'exécutable n\'a pas été trouvé à l\'emplacement :\n%s\n\n'
                'Vérifiez que le fichier BATIGEST.exe est bien présent.'
            ) % self.executable_path)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test réussi'),
                'message': _('L\'exécutable BATIGEST.exe a été trouvé.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_output_folder(self):
        """Teste si le dossier de sortie existe"""
        self.ensure_one()
        if not self.output_folder:
            raise UserError(_('Le dossier de sortie n\'est pas configuré.'))
        
        if not os.path.exists(self.output_folder):
            try:
                os.makedirs(self.output_folder)
                msg = _('Le dossier a été créé avec succès.')
            except Exception as e:
                raise UserError(_(
                    'Impossible de créer le dossier :\n%s\n\nErreur: %s'
                ) % (self.output_folder, str(e)))
        else:
            msg = _('Le dossier de sortie existe.')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test réussi'),
                'message': msg,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_test_templates(self):
        """Vérifie que les templates d'export existent"""
        self.ensure_one()
        missing = []
        
        templates = [
            ('BEG', self.template_beg),
            ('NIEDAX', self.template_niedax),
            ('CÂBLES', self.template_cables),
        ]
        
        for name, path in templates:
            if path and not os.path.exists(path):
                missing.append(f"- {name}: {path}")
        
        if missing:
            raise UserError(_(
                'Templates manquants :\n\n%s\n\n'
                'Ces fichiers sont nécessaires pour les exports Naviwest.'
            ) % '\n'.join(missing))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Templates OK'),
                'message': _('Tous les templates d\'export sont présents.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_run_executable(self):
        """Lance l'exécutable BATIGEST.exe"""
        self.ensure_one()
        
        if not self.executable_path:
            raise UserError(_('Le chemin de l\'exécutable n\'est pas configuré.'))
        
        if not os.path.exists(self.executable_path):
            raise UserError(_('L\'exécutable n\'existe pas : %s') % self.executable_path)
        
        try:
            _logger.info("Lancement de l'exécutable VST: %s", self.executable_path)
            
            # Méthode 1: Utiliser os.startfile (Windows uniquement, non bloquant)
            # Cela lance l'exécutable comme si on double-cliquait dessus
            if hasattr(os, 'startfile'):
                os.startfile(self.executable_path)
                
                # Attendre quelques secondes que le fichier soit généré
                import time
                output_file = os.path.join(self.output_folder, self.output_filename)
                
                # Attendre jusqu'à 30 secondes
                for i in range(30):
                    time.sleep(1)
                    if os.path.exists(output_file):
                        # Vérifier que le fichier a été modifié récemment (dans les 60 dernières secondes)
                        file_mtime = os.path.getmtime(output_file)
                        import datetime
                        file_age = datetime.datetime.now().timestamp() - file_mtime
                        if file_age < 60:
                            break
                
                log_msg = "Exécutable lancé avec os.startfile"
            else:
                # Méthode 2: Fallback pour Linux/Mac (ne devrait pas arriver)
                result = subprocess.Popen(
                    [self.executable_path],
                    cwd=os.path.dirname(self.executable_path),
                    shell=True
                )
                result.wait(timeout=60)
                log_msg = f"Exécutable lancé avec subprocess. Code retour: {result.returncode}"
            
            self.write({'last_log': log_msg})
            _logger.info(log_msg)
            
            # Vérifier si le fichier a été généré
            output_file = os.path.join(self.output_folder, self.output_filename)
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Succès'),
                        'message': _('Fichier généré avec succès (%s octets)') % file_size,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Attention'),
                        'message': _('L\'exécutable a été lancé mais le fichier n\'a pas été trouvé après 30 secondes.'),
                        'type': 'warning',
                        'sticky': True,
                    }
                }
                
        except subprocess.TimeoutExpired:
            raise UserError(_('L\'exécutable a dépassé le délai d\'attente.'))
        except Exception as e:
            _logger.error("Erreur lors du lancement de l'exécutable VST: %s", str(e))
            raise UserError(_('Erreur lors du lancement de l\'exécutable :\n%s') % str(e))

    def action_open_import_wizard(self):
        """Ouvre l'assistant d'import"""
        self.ensure_one()
        return {
            'name': _('Importer les articles VST'),
            'type': 'ir.actions.act_window',
            'res_model': 'import.vst.wizard',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_full_update(self):
        """Exécute une mise à jour complète : lance l'exécutable puis importe"""
        self.ensure_one()
        
        # 1. Lancer l'exécutable
        self.action_run_executable()
        
        # 2. Ouvrir le wizard d'import
        return self.action_open_import_wizard()

    @api.model
    def cron_auto_update(self):
        """Méthode appelée par le cron pour la mise à jour automatique"""
        config = self.get_config()
        if not config.auto_update_enabled:
            return
        
        try:
            # Lancer l'exécutable
            config.action_run_executable()
            
            # Créer et exécuter le wizard d'import
            wizard = self.env['import.vst.wizard'].create({
                'mode': 'file',
                'update_existing': config.update_existing,
                'create_price_history': config.create_price_history,
                'detect_deleted': True,
            })
            wizard.action_import()
            
        except Exception as e:
            _logger.error("Erreur import VST automatique: %s", str(e))
