# -*- coding: utf-8 -*-

import os
import logging
import time
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ImportVstWizard(models.TransientModel):
    _name = 'import.vst.wizard'
    _description = 'Assistant d\'import VST'

    mode = fields.Selection([
        ('file', 'Importer depuis le fichier existant'),
        ('execute_and_import', 'Lancer l\'exécutable puis importer'),
    ], string='Mode', default='file', required=True)
    
    update_existing = fields.Boolean(
        string='Mettre à jour les articles existants',
        default=True
    )
    auto_create_product = fields.Boolean(
        string='Créer automatiquement les produits Odoo',
        default=False
    )
    create_price_history = fields.Boolean(
        string='Créer un historique des prix',
        default=True
    )
    detect_deleted = fields.Boolean(
        string='Détecter les articles supprimés',
        default=True,
        help='Marque comme supprimés les articles qui ne sont plus dans le catalogue VST'
    )
    archive_deleted_products = fields.Boolean(
        string='Archiver les produits Odoo supprimés',
        default=False,
        help='Archive automatiquement les produits Odoo liés aux articles supprimés'
    )
    
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('importing', 'Import en cours'),
        ('done', 'Terminé'),
        ('error', 'Erreur'),
    ], string='État', default='draft')
    
    articles_created = fields.Integer(string='Articles créés', readonly=True)
    articles_updated = fields.Integer(string='Articles mis à jour', readonly=True)
    articles_deleted = fields.Integer(string='Articles supprimés', readonly=True)
    articles_total = fields.Integer(string='Total traités', readonly=True)
    errors_count = fields.Integer(string='Erreurs', readonly=True)
    log_message = fields.Text(string='Log', readonly=True)
    
    progress = fields.Float(string='Progression', readonly=True)
    duration = fields.Float(string='Durée (secondes)', readonly=True)
    speed = fields.Float(string='Articles/seconde', readonly=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        config = self.env['vst.config'].get_config()
        res.update({
            'update_existing': config.update_existing,
            'auto_create_product': config.auto_create_product,
            'create_price_history': config.create_price_history,
        })
        return res

    def action_import(self):
        """Lance l'import"""
        self.ensure_one()
        config = self.env['vst.config'].get_config()
        
        if self.mode == 'execute_and_import':
            config.action_run_executable()
        
        file_path = os.path.join(config.output_folder, config.output_filename)
        
        if not os.path.exists(file_path):
            raise UserError(_(
                'Le fichier BATIGEST n\'a pas été trouvé à l\'emplacement :\n%s\n\n'
                'Assurez-vous que l\'exécutable a été lancé au moins une fois.'
            ) % file_path)
        
        self.write({'state': 'importing'})
        self.env.cr.commit()
        
        start_time = time.time()
        created_count = 0
        updated_count = 0
        deleted_count = 0
        errors = 0
        error_messages = []
        deleted_articles_log = []
        
        try:
            _logger.info("VST Import - Lecture du fichier...")
            
            with open(file_path, 'r', encoding='cp1252', errors='replace') as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            _logger.info("VST Import: %d lignes à traiter", total_lines)
            
            all_data = []
            imported_codes = set()
            
            for i, line in enumerate(lines):
                try:
                    fields_data = line.strip().split('\t')
                    if len(fields_data) >= 22:
                        line_data = self._parse_line(fields_data)
                        if line_data.get('code_article'):
                            all_data.append(line_data)
                            imported_codes.add(line_data['code_article'])
                except Exception as e:
                    errors += 1
                    if len(error_messages) < 20:
                        error_messages.append(f"Ligne {i+1}: Erreur parsing - {str(e)}")
            
            if not all_data:
                raise UserError(_('Aucun article valide trouvé dans le fichier.'))
            
            # Charger le cache
            existing_articles = self._load_existing_articles_cache()
            existing_familles = self._load_existing_familles_cache()
            
            # Traitement par lots
            batch_size = 100
            total_batches = (len(all_data) + batch_size - 1) // batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * batch_size
                end_idx = min(start_idx + batch_size, len(all_data))
                batch_data = all_data[start_idx:end_idx]
                
                try:
                    batch_created, batch_updated, batch_errors = self._process_batch(
                        batch_data, existing_articles, existing_familles
                    )
                    
                    created_count += batch_created
                    updated_count += batch_updated
                    errors += batch_errors
                    
                    self.env.cr.commit()
                    
                    progress = ((batch_num + 1) / total_batches) * 90
                    self.write({'progress': progress})
                    self.env.cr.commit()
                    
                except Exception as e:
                    self.env.cr.rollback()
                    errors += len(batch_data)
                    if len(error_messages) < 20:
                        error_messages.append(f"Lot {batch_num + 1}: {str(e)}")
            
            # Détection des articles supprimés
            if self.detect_deleted:
                deleted_count, deleted_articles_log = self._detect_deleted_articles(
                    imported_codes, existing_articles, self.archive_deleted_products
                )
            
            # Résultats
            end_time = time.time()
            duration = end_time - start_time
            total_processed = created_count + updated_count
            speed = total_processed / duration if duration > 0 else 0
            
            log_msg = self._build_log_message(
                created_count, updated_count, deleted_count, errors,
                duration, speed, error_messages, deleted_articles_log
            )
            
            self.write({
                'state': 'done',
                'articles_created': created_count,
                'articles_updated': updated_count,
                'articles_deleted': deleted_count,
                'articles_total': total_processed,
                'errors_count': errors,
                'log_message': log_msg,
                'progress': 100,
                'duration': duration,
                'speed': speed,
            })
            self.env.cr.commit()
            
            config.write({
                'last_import_date': fields.Datetime.now(),
                'last_import_count': total_processed,
                'last_log': log_msg,
            })
            self.env.cr.commit()
            
        except Exception as e:
            self.env.cr.rollback()
            error_log = f"Erreur lors de l'import:\n{str(e)}"
            _logger.error("Erreur import VST: %s", str(e), exc_info=True)
            
            try:
                self.write({'state': 'error', 'log_message': error_log})
                self.env.cr.commit()
            except:
                pass
            
            raise UserError(_('Erreur lors de l\'import :\n%s') % str(e))
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'import.vst.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _detect_deleted_articles(self, imported_codes, existing_articles, archive_products):
        """Détecte les articles supprimés du catalogue"""
        deleted_count = 0
        deleted_log = []
        
        Article = self.env['vst.article']
        
        for code, article_data in existing_articles.items():
            if code not in imported_codes:
                article_id = article_data['id']
                
                try:
                    article = Article.browse(article_id)
                    
                    if article.exists() and not article.is_deleted:
                        log_entry = f"[{code}] {article.designation or 'Sans désignation'}"
                        if article.product_id:
                            log_entry += f" (Produit: {article.product_id.default_code or article.product_id.name})"
                        
                        deleted_log.append(log_entry)
                        
                        vals = {
                            'is_deleted': True,
                            'date_suppression': fields.Datetime.now(),
                        }
                        
                        if archive_products and article.product_id:
                            article.product_id.write({'active': False})
                        
                        article.write(vals)
                        deleted_count += 1
                        
                except Exception as e:
                    _logger.error("Erreur marquage suppression article %s: %s", code, str(e))
        
        if deleted_count > 0:
            self.env.cr.commit()
        
        return deleted_count, deleted_log

    def _process_batch(self, batch_data, existing_articles, existing_familles):
        """Traite un lot d'articles"""
        created = 0
        updated = 0
        errors = 0
        
        Article = self.env['vst.article'].with_context(
            tracking_disable=True,
            mail_create_nosubscribe=True,
            mail_create_nolog=True,
        )
        
        to_create = []
        to_update = []
        price_history = []
        
        for data in batch_data:
            try:
                code = data['code_article']
                
                famille_id = self._get_or_create_famille(data, existing_familles)
                vals = self._prepare_article_vals(data)
                
                if famille_id:
                    vals['famille_id'] = famille_id
                
                vals['is_deleted'] = False
                vals['date_suppression'] = False
                
                if code in existing_articles:
                    if self.update_existing:
                        existing = existing_articles[code]
                        
                        if self.create_price_history:
                            old_prix = existing.get('prix_achat_adherent', 0.0)
                            new_prix = vals.get('prix_achat_adherent', 0.0)
                            if abs(old_prix - new_prix) > 0.001:
                                price_history.append({
                                    'article_id': existing['id'],
                                    'prix_ancien': old_prix,
                                    'prix_nouveau': new_prix,
                                    'type_prix': 'achat_adherent',
                                })
                        
                        vals['id'] = existing['id']
                        to_update.append(vals)
                else:
                    vals['date_import'] = fields.Datetime.now()
                    to_create.append(vals)
                    
            except Exception as e:
                errors += 1
        
        if to_create:
            try:
                Article.create(to_create)
                created = len(to_create)
            except Exception as e:
                for vals in to_create:
                    try:
                        Article.create(vals)
                        created += 1
                    except:
                        errors += 1
        
        for vals in to_update:
            try:
                article_id = vals.pop('id')
                Article.browse(article_id).write(vals)
                updated += 1
            except:
                errors += 1
        
        if price_history:
            try:
                self.env['vst.price.history'].create(price_history)
            except:
                pass
        
        return created, updated, errors

    def _get_or_create_famille(self, data, existing_familles):
        """Récupère ou crée la famille pour un article"""
        famille_code = data.get('nouvelle_famille_code') or data.get('famille_code')
        if not famille_code:
            return None
        
        if famille_code in existing_familles:
            return existing_familles[famille_code]['id']
        
        parts = famille_code.split('.')
        if not parts:
            return None
        
        levels = ['activite', 'marque', 'famille', 'sous_famille', 'sous_sous_famille']
        libelles = [
            data.get('libelle_activite'),
            data.get('libelle_marque'),
            data.get('libelle_famille'),
            data.get('libelle_sous_famille'),
            None
        ]
        
        Famille = self.env['vst.famille']
        cumul_code = ''
        parent_id = None
        last_id = None
        
        for i, part in enumerate(parts):
            if not part:
                continue
            
            cumul_code = f"{cumul_code}.{part}" if cumul_code else part
            
            if cumul_code in existing_familles:
                parent_id = existing_familles[cumul_code]['id']
                last_id = parent_id
                continue
            
            level = levels[i] if i < len(levels) else 'sous_sous_famille'
            libelle = libelles[i] if i < len(libelles) else None
            
            try:
                famille = Famille.create({
                    'code': cumul_code,
                    'name': libelle or part,
                    'level': level,
                    'parent_id': parent_id,
                })
                
                existing_familles[cumul_code] = {
                    'id': famille.id,
                    'code': cumul_code,
                }
                
                parent_id = famille.id
                last_id = famille.id
                
            except Exception as e:
                famille = Famille.search([('code', '=', cumul_code)], limit=1)
                if famille:
                    existing_familles[cumul_code] = {'id': famille.id, 'code': cumul_code}
                    parent_id = famille.id
                    last_id = famille.id
        
        return last_id

    def _load_existing_articles_cache(self):
        """Charge tous les articles existants en cache"""
        self.env.cr.execute("""
            SELECT id, code_article, prix_achat_adherent, prix_public_ht, 
                   famille_id, product_id, is_deleted
            FROM vst_article
            WHERE active = true
        """)
        
        cache = {}
        for row in self.env.cr.fetchall():
            cache[row[1]] = {
                'id': row[0],
                'code_article': row[1],
                'prix_achat_adherent': row[2] or 0.0,
                'prix_public_ht': row[3] or 0.0,
                'famille_id': row[4],
                'product_id': row[5],
                'is_deleted': row[6],
            }
        return cache

    def _load_existing_familles_cache(self):
        """Charge toutes les familles existantes en cache"""
        self.env.cr.execute("SELECT id, code FROM vst_famille")
        return {row[1]: {'id': row[0], 'code': row[1]} for row in self.env.cr.fetchall() if row[1]}

    def _prepare_article_vals(self, data):
        """Prépare les valeurs d'un article"""
        date_str = data.get('date_dernier_prix', '')
        date_dernier_prix = None
        if date_str and len(date_str) == 8:
            try:
                date_dernier_prix = datetime.strptime(date_str, '%d%m%Y').date()
            except ValueError:
                pass
        
        return {
            'code_article': data['code_article'],
            'famille_code': data.get('famille_code'),
            'nouvelle_famille_code': data.get('nouvelle_famille_code'),
            'source': data.get('source', 'VST'),
            'designation': data.get('designation'),
            'code_alpha': data.get('code_alpha'),
            'prix_achat_adherent': data.get('prix_achat_adherent', 0.0),
            'prix_public_ht': data.get('prix_public_ht', 0.0),
            'prix_public_ttc': data.get('prix_public_ttc', 0.0),
            'ecotaxe_ht': data.get('ecotaxe_ht', 0.0),
            'ecotaxe_ttc': data.get('ecotaxe_ttc', 0.0),
            'code_fabricant': data.get('code_fabricant'),
            'nom_fabricant': data.get('nom_fabricant'),
            'reference_fabricant': data.get('reference_fabricant'),
            'date_dernier_prix': date_dernier_prix,
            'designation_majuscule': data.get('designation_majuscule'),
            'libelle_activite': data.get('libelle_activite'),
            'libelle_marque': data.get('libelle_marque'),
            'libelle_famille': data.get('libelle_famille'),
            'libelle_sous_famille': data.get('libelle_sous_famille'),
            'unite': data.get('unite'),
            'type_article': data.get('type_article'),
            'date_derniere_maj': fields.Datetime.now(),
        }

    def _parse_line(self, fields_data):
        """Parse une ligne du fichier BATIGEST"""
        
        def safe_float(value):
            if not value:
                return 0.0
            try:
                return float(value.replace(',', '.').replace(' ', ''))
            except:
                return 0.0
        
        def safe_str(index):
            try:
                val = fields_data[index].strip() if index < len(fields_data) else ''
                return val[:255] if val else ''
            except:
                return ''
        
        type_art = safe_str(21)
        
        return {
            'code_article': safe_str(0)[:64],
            'famille_code': safe_str(1),
            'source': safe_str(2) or 'VST',
            'designation': safe_str(3),
            'code_alpha': safe_str(4)[:64],
            'prix_achat_adherent': safe_float(safe_str(5)),
            'prix_public_ht': safe_float(safe_str(6)),
            'prix_public_ttc': safe_float(safe_str(7)),
            'ecotaxe_ht': safe_float(safe_str(8)),
            'ecotaxe_ttc': safe_float(safe_str(9)),
            'code_fabricant': safe_str(10)[:64],
            'nom_fabricant': safe_str(11),
            'reference_fabricant': safe_str(12),
            'date_dernier_prix': safe_str(13),
            'designation_majuscule': safe_str(14),
            'nouvelle_famille_code': safe_str(15),
            'libelle_activite': safe_str(16),
            'libelle_marque': safe_str(17),
            'libelle_famille': safe_str(18),
            'libelle_sous_famille': safe_str(19),
            'unite': safe_str(20)[:16],
            'type_article': type_art if type_art in ('DIV', 'ART', 'KIT', 'LOV') else None,
        }

    def _build_log_message(self, created, updated, deleted, errors, duration, speed, 
                          error_messages, deleted_articles_log=None):
        """Construit le message de log final"""
        log = []
        log.append("=" * 60)
        log.append("IMPORT VST - RAPPORT")
        log.append("=" * 60)
        log.append("")
        log.append(f"Durée totale: {duration:.2f} secondes")
        log.append(f"Vitesse: {speed:.1f} articles/seconde")
        log.append("")
        log.append("RÉSULTATS:")
        log.append(f"   Articles créés: {created}")
        log.append(f"   Articles mis à jour: {updated}")
        log.append(f"   Articles supprimés du catalogue: {deleted}")
        log.append(f"   Erreurs: {errors}")
        log.append("")
        
        if deleted_articles_log:
            log.append("-" * 60)
            log.append("ARTICLES SUPPRIMÉS:")
            for entry in deleted_articles_log[:50]:
                log.append(f"   - {entry}")
            if len(deleted_articles_log) > 50:
                log.append(f"   ... et {len(deleted_articles_log) - 50} autres")
            log.append("")
        
        if error_messages:
            log.append("-" * 60)
            log.append("ERREURS:")
            for msg in error_messages[:20]:
                log.append(f"   - {msg}")
        
        return "\n".join(log)

    def action_view_articles(self):
        """Ouvre la liste des articles"""
        return {
            'name': _('Articles VST'),
            'type': 'ir.actions.act_window',
            'res_model': 'vst.article',
            'view_mode': 'list,form',
            'target': 'current',
        }

    def action_view_deleted_articles(self):
        """Ouvre la liste des articles supprimés"""
        return {
            'name': _('Articles supprimés'),
            'type': 'ir.actions.act_window',
            'res_model': 'vst.article',
            'view_mode': 'list,form',
            'domain': [('is_deleted', '=', True)],
            'target': 'current',
        }
