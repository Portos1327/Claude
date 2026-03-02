# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Surveillance et synchronisation automatique (CRON)
Vérifie chaque jour si les fichiers .qdb ou Rebates.qdbr ont changé
(date de modification ET taille) et synchronise automatiquement si besoin.

Stocke un snapshot de l'état connu de chaque fichier dans qdv.tarif.file.snapshot
afin de détecter les changements au prochain passage.
"""
from odoo import models, fields, api, _
import logging
import os
import sqlite3

_logger = logging.getLogger(__name__)


class QdvTarifFileSnapshot(models.Model):
    """
    Snapshot de l'état d'un fichier surveillé au dernier passage du CRON.
    Un enregistrement par fichier (clé = chemin absolu).
    """
    _name = 'qdv.tarif.file.snapshot'
    _description = 'Snapshot fichier QDV (surveillance CRON)'
    _order = 'file_path'

    file_path = fields.Char(
        string='Chemin fichier',
        required=True,
        index=True,
        help='Chemin absolu du fichier surveillé'
    )
    file_name = fields.Char(
        string='Nom fichier',
        compute='_compute_file_name',
        store=True
    )
    file_type = fields.Selection([
        ('qdb', 'Base tarif (.qdb)'),
        ('rebates', 'Rebates.qdbr'),
        ('browser_local', 'BrowserFromLocal.txt'),
        ('browser_web', 'BrowserFromWeb.txt'),
    ], string='Type', default='qdb')

    # État connu au dernier passage
    known_mtime = fields.Float(
        string='Date modif connue (timestamp)',
        help='os.path.getmtime au dernier passage CRON'
    )
    known_size = fields.Integer(
        string='Taille connue (octets)',
        help='os.path.getsize au dernier passage CRON'
    )

    # Lien vers la base concernée (pour .qdb uniquement)
    base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Base associée',
        ondelete='cascade'
    )

    # Historique des synchros
    last_sync_date = fields.Datetime(string='Dernière synchro', readonly=True)
    last_sync_result = fields.Selection([
        ('ok', 'Succès'),
        ('error', 'Erreur'),
        ('no_change', 'Pas de changement'),
    ], string='Résultat dernier passage', readonly=True, default='no_change')
    last_sync_message = fields.Text(string='Message dernier passage', readonly=True)
    sync_count = fields.Integer(string='Nb synchros effectuées', default=0, readonly=True)

    @api.depends('file_path')
    def _compute_file_name(self):
        for rec in self:
            rec.file_name = os.path.basename(rec.file_path) if rec.file_path else ''

    def has_changed(self):
        """
        Vérifie si le fichier a changé depuis le dernier snapshot.
        Retourne (changed: bool, reason: str)
        """
        self.ensure_one()
        path = self.file_path
        if not path or not os.path.isfile(path):
            return False, 'Fichier absent'

        current_mtime = os.path.getmtime(path)
        current_size = os.path.getsize(path)

        reasons = []
        if abs(current_mtime - (self.known_mtime or 0)) > 1:  # tolérance 1 seconde
            reasons.append('date modif changée (%.0f → %.0f)' % (self.known_mtime or 0, current_mtime))
        if current_size != (self.known_size or 0):
            reasons.append('taille changée (%d → %d octets)' % (self.known_size or 0, current_size))

        if reasons:
            return True, ', '.join(reasons)
        return False, 'Pas de changement'

    def update_snapshot(self):
        """Met à jour le snapshot avec l'état actuel du fichier"""
        self.ensure_one()
        path = self.file_path
        if path and os.path.isfile(path):
            self.write({
                'known_mtime': os.path.getmtime(path),
                'known_size': os.path.getsize(path),
            })


class QdvTarifSyncLog(models.Model):
    """Journal de toutes les synchronisations automatiques effectuées par le CRON"""
    _name = 'qdv.tarif.sync.log'
    _description = 'Journal synchro automatique QDV'
    _order = 'sync_date desc'

    sync_date = fields.Datetime(
        string='Date/heure',
        default=fields.Datetime.now,
        readonly=True
    )
    trigger = fields.Selection([
        ('cron', 'CRON automatique'),
        ('manual', 'Déclenchement manuel'),
    ], string='Déclencheur', default='cron', readonly=True)

    files_checked = fields.Integer(string='Fichiers vérifiés', readonly=True)
    files_changed = fields.Integer(string='Fichiers changés', readonly=True)
    bases_synced = fields.Integer(string='Bases synchronisées', readonly=True)
    articles_updated = fields.Integer(string='Articles mis à jour', readonly=True)
    articles_created = fields.Integer(string='Nouveaux articles', readonly=True)
    rebates_updated = fields.Integer(string='Remises mises à jour', readonly=True)

    status = fields.Selection([
        ('ok', 'Succès'),
        ('partial', 'Partiel (erreurs)'),
        ('nothing', 'Rien à faire'),
        ('error', 'Erreur'),
    ], string='Statut', readonly=True, default='ok')

    detail = fields.Text(string='Détail', readonly=True)
    duration = fields.Float(string='Durée (s)', digits=(8, 2), readonly=True)


class QdvTarifCronMixin(models.AbstractModel):
    """
    Mixin contenant la logique principale du CRON.
    Appelé par ir.actions.server (action serveur CRON).
    """
    _name = 'qdv.tarif.cron.mixin'
    _description = 'Mixin CRON QDV Tarifs'

    @api.model
    def run_daily_check(self):
        """
        Point d'entrée principal du CRON journalier.
        1. Récupère la configuration
        2. Vérifie chaque fichier surveillé (snapshots)
        3. Synchronise les bases modifiées
        4. Met à jour les snapshots
        5. Crée un log de synthèse
        6. Envoie une notification si des changements ont été détectés
        """
        import time
        start_time = time.time()

        config = self.env['qdv.tarif.config'].get_config()
        folder = config.tarifs_folder

        log_lines = ['=== CRON QDV Tarifs - %s ===' % fields.Datetime.now()]
        files_checked = 0
        files_changed = 0
        bases_synced = 0
        articles_updated = 0
        articles_created = 0
        rebates_updated = 0
        errors = []

        if not folder or not os.path.isdir(folder):
            msg = 'Dossier inaccessible: %s' % folder
            _logger.warning(msg)
            self._create_sync_log(
                trigger='cron', files_checked=0, files_changed=0,
                bases_synced=0, articles_updated=0, articles_created=0,
                rebates_updated=0, status='error',
                detail=msg, duration=time.time() - start_time
            )
            return

        # =====================================================================
        # 1. Vérifier Rebates.qdbr
        # =====================================================================
        rebates_path = os.path.join(folder, 'Rebates.qdbr')
        rebates_changed = False

        if os.path.isfile(rebates_path):
            files_checked += 1
            snap_rebates = self._get_or_create_snapshot(rebates_path, 'rebates')
            changed, reason = snap_rebates.has_changed()
            if changed:
                rebates_changed = True
                files_changed += 1
                log_lines.append('✅ Rebates.qdbr modifié: %s' % reason)
            else:
                log_lines.append('— Rebates.qdbr: inchangé')

        # =====================================================================
        # 2. Scanner et vérifier chaque fichier .qdb
        # =====================================================================
        try:
            qdb_files = [f for f in os.listdir(folder) if f.lower().endswith('.qdb')]
        except Exception as e:
            _logger.error('Erreur lecture dossier: %s', str(e))
            errors.append('Lecture dossier: %s' % str(e))
            qdb_files = []

        log_lines.append('\nFichiers .qdb trouvés: %d' % len(qdb_files))

        # Charger toutes les bases connues (code -> base)
        bases_by_code = {b.manufacturer_code: b for b in self.env['qdv.tarif.base'].search([])}

        for fname in sorted(qdb_files):
            fpath = os.path.join(folder, fname)
            files_checked += 1

            # Parser le code fabricant depuis le nom de fichier
            base_model = self.env['qdv.tarif.base']
            parsed = base_model.parse_filename(fname)
            if not parsed:
                log_lines.append('  ⚠ Nom non parsable: %s' % fname)
                continue

            code = parsed['manufacturer_code']
            base = bases_by_code.get(code)

            if not base:
                # Base inconnue (jamais découverte) → on ignore
                log_lines.append('  ⚠ Base non enregistrée: %s (passer par Découverte)' % code)
                continue

            snap = self._get_or_create_snapshot(fpath, 'qdb', base_id=base.id)
            qdb_changed, reason = snap.has_changed()

            if not qdb_changed and not rebates_changed:
                log_lines.append('  — %s: inchangé' % code)
                continue

            # Fichier changé (ou rebates changé) → synchroniser
            change_reasons = []
            if qdb_changed:
                change_reasons.append('qdb: ' + reason)
            if rebates_changed:
                change_reasons.append('Rebates.qdbr modifié')

            log_lines.append('  ✅ %s (%s): synchronisation... [%s]' % (
                base.manufacturer_name, code, ', '.join(change_reasons)))
            files_changed += 1

            try:
                result = self._sync_base(base, folder, rebates_changed)
                created = result.get('created', 0)
                updated = result.get('updated', 0)
                rebates = result.get('rebates', 0)
                articles_created += created
                articles_updated += updated
                rebates_updated += rebates
                bases_synced += 1
                log_lines.append('     → %d créés, %d MAJ, %d remises' % (created, updated, rebates))

                # Mettre à jour le snapshot du .qdb
                snap.write({
                    'last_sync_date': fields.Datetime.now(),
                    'last_sync_result': 'ok',
                    'last_sync_message': ', '.join(change_reasons),
                    'sync_count': snap.sync_count + 1,
                })
                snap.update_snapshot()

                # Mettre à jour la fiche base
                base.write({
                    'import_state': 'imported',
                    'last_import_date': fields.Datetime.now(),
                    'import_error': '',
                })

            except Exception as e:
                err_msg = str(e)[:500]
                errors.append('%s: %s' % (code, err_msg))
                log_lines.append('     ❌ Erreur: %s' % err_msg)
                _logger.error('Erreur synchro base %s: %s', code, err_msg)
                snap.write({
                    'last_sync_date': fields.Datetime.now(),
                    'last_sync_result': 'error',
                    'last_sync_message': err_msg,
                })
                base.write({'import_state': 'error', 'import_error': err_msg})

        # Mettre à jour le snapshot de Rebates.qdbr après traitement
        if rebates_changed and os.path.isfile(rebates_path):
            snap_rebates = self._get_or_create_snapshot(rebates_path, 'rebates')
            snap_rebates.update_snapshot()

        duration = time.time() - start_time
        log_lines.append('\n=== RÉSUMÉ ===')
        log_lines.append('Fichiers vérifiés: %d' % files_checked)
        log_lines.append('Fichiers changés:  %d' % files_changed)
        log_lines.append('Bases synchronisées: %d' % bases_synced)
        log_lines.append('Articles créés: %d / mis à jour: %d' % (articles_created, articles_updated))
        log_lines.append('Remises mises à jour: %d' % rebates_updated)
        log_lines.append('Durée: %.2f s' % duration)
        if errors:
            log_lines.append('Erreurs: %d' % len(errors))
            for e in errors:
                log_lines.append('  ❌ ' + e)

        detail_text = '\n'.join(log_lines)
        _logger.info('CRON QDV Tarifs:\n%s', detail_text)

        # Statut global
        if errors and bases_synced == 0:
            status = 'error'
        elif errors:
            status = 'partial'
        elif files_changed == 0:
            status = 'nothing'
        else:
            status = 'ok'

        sync_log = self._create_sync_log(
            trigger='cron',
            files_checked=files_checked,
            files_changed=files_changed,
            bases_synced=bases_synced,
            articles_updated=articles_updated,
            articles_created=articles_created,
            rebates_updated=rebates_updated,
            status=status,
            detail=detail_text,
            duration=duration,
        )

        # Notification Odoo si des changements ont eu lieu ou erreurs
        if files_changed > 0 or errors:
            self._notify_users(sync_log, bases_synced, errors)

    # =========================================================================
    # SYNCHRONISATION D'UNE BASE
    # =========================================================================
    def _sync_base(self, base, folder, sync_rebates=True):
        """
        Synchronise une base .qdb:
        1. Relit les métadonnées (taille, date) depuis BrowserFromLocal
        2. Si sync_rebates: reimporte les remises depuis Rebates.qdbr
        3. Réimporte les articles (update_existing=True)
        Retourne dict {created, updated, rebates}
        """
        result = {'created': 0, 'updated': 0, 'rebates': 0}

        # --- Remises ---
        if sync_rebates:
            rebates_path = os.path.join(folder, 'Rebates.qdbr')
            if os.path.isfile(rebates_path):
                rebates_data = self._read_rebates_for_base(rebates_path, base.manufacturer_code)
                if rebates_data:
                    base.rebate_ids.unlink()
                    for r in rebates_data:
                        r['base_id'] = base.id
                        self.env['qdv.tarif.rebate'].create(r)
                        result['rebates'] += 1

        # --- Métadonnées depuis BrowserFromLocal ---
        local_path = os.path.join(folder, 'BrowserFromLocal.txt')
        if os.path.isfile(local_path):
            browser_data = self._read_browser_entry(local_path, base.manufacturer_code)
            if browser_data:
                tarif_date = self._parse_date_str(browser_data.get('date', ''))
                update_vals = {
                    'total_size': browser_data.get('total_size', base.total_size),
                    'local_size': browser_data.get('total_size', base.local_size),
                    'version': browser_data.get('version', base.version),
                }
                if tarif_date:
                    update_vals['tarif_date'] = tarif_date
                base.write(update_vals)

        # --- Articles (si le .qdb lui-même a changé) ---
        if base.file_path and os.path.isfile(base.file_path):
            import_wizard = self.env['qdv.tarif.import.wizard'].create({
                'single_base_id': base.id,
                'update_existing': True,
                'apply_rebates': True,
                'create_odoo_products': False,
                'limit_rows': 0,
            })
            created, updated, errors = import_wizard._import_base(base)
            result['created'] = created
            result['updated'] = updated

        return result

    # =========================================================================
    # HELPERS
    # =========================================================================
    def _get_or_create_snapshot(self, file_path, file_type, base_id=None):
        """Retourne le snapshot existant ou en crée un (avec état actuel comme base)"""
        snap = self.env['qdv.tarif.file.snapshot'].search(
            [('file_path', '=', file_path)], limit=1
        )
        if not snap:
            vals = {
                'file_path': file_path,
                'file_type': file_type,
                'known_mtime': os.path.getmtime(file_path) if os.path.isfile(file_path) else 0,
                'known_size': os.path.getsize(file_path) if os.path.isfile(file_path) else 0,
            }
            if base_id:
                vals['base_id'] = base_id
            snap = self.env['qdv.tarif.file.snapshot'].create(vals)
        elif base_id and not snap.base_id:
            snap.write({'base_id': base_id})
        return snap

    def _read_rebates_for_base(self, rebates_path, manufacturer_code):
        """Lit les remises d'un fabricant depuis Rebates.qdbr"""
        lines = []
        try:
            conn = sqlite3.connect(rebates_path)
            cur = conn.cursor()
            cur.execute("""
                SELECT RebateCode, Rebate, DerogationRebate, UseDerogation, RebateLabel, RebateComment
                FROM Rebates WHERE ManufacturerCode = ?
                ORDER BY RebateCode
            """, (manufacturer_code,))
            for row in cur.fetchall():
                (rebate_code, rebate_val, derog_val, use_derog, label, comment) = row
                lines.append({
                    'rebate_code': rebate_code or '',
                    'rebate_label': label or '',
                    'rebate_value': float(rebate_val or 0),
                    'negotiated_value': float(derog_val or 0),
                    'use_negotiated': bool(use_derog),
                    'rebate_comment': comment or '',
                })
            conn.close()
        except Exception as e:
            _logger.error('Erreur lecture remises %s: %s', manufacturer_code, str(e))
        return lines

    def _read_browser_entry(self, browser_path, manufacturer_code):
        """Lit l'entrée d'un fabricant dans BrowserFromLocal.txt"""
        try:
            with open(browser_path, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(';')
                    if parts[0].strip() == manufacturer_code:
                        return {
                            'name': parts[1].strip() if len(parts) > 1 else manufacturer_code,
                            'date': parts[2].strip() if len(parts) > 2 else '',
                            'version': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 1,
                            'total_size': int(parts[4]) if len(parts) > 4 and parts[4].isdigit() else 0,
                        }
        except Exception as e:
            _logger.warning('Erreur lecture BrowserFromLocal: %s', str(e))
        return {}

    def _parse_date_str(self, date_str):
        """Convertit YYYYMMDD en date Odoo"""
        if not date_str or len(date_str) < 8:
            return False
        try:
            d = date_str.replace('.', '').replace('-', '')[:8]
            if len(d) == 8 and d.isdigit():
                return '%s-%s-%s' % (d[:4], d[4:6], d[6:8])
        except Exception:
            pass
        return False

    def _create_sync_log(self, trigger='cron', files_checked=0, files_changed=0,
                         bases_synced=0, articles_updated=0, articles_created=0,
                         rebates_updated=0, status='ok', detail='', duration=0.0):
        """Crée un enregistrement dans le journal de synchro"""
        return self.env['qdv.tarif.sync.log'].create({
            'trigger': trigger,
            'files_checked': files_checked,
            'files_changed': files_changed,
            'bases_synced': bases_synced,
            'articles_updated': articles_updated,
            'articles_created': articles_created,
            'rebates_updated': rebates_updated,
            'status': status,
            'detail': detail,
            'duration': duration,
        })

    def _notify_users(self, sync_log, bases_synced, errors):
        """Envoie une notification Odoo aux utilisateurs du groupe admin"""
        if errors:
            title = '⚠️ QDV Tarifs: %d erreur(s) de synchronisation' % len(errors)
            msg_type = 'warning'
        else:
            title = '✅ QDV Tarifs: %d base(s) synchronisée(s)' % bases_synced
            msg_type = 'success'

        # Notification dans le chatter du log (visible dans l'interface)
        # Odoo 18: on passe par bus.bus ou activity - ici on utilise une simple note
        try:
            admin_users = self.env['res.users'].search([
                ('groups_id', 'in', [self.env.ref('base.group_system').id])
            ])
            for user in admin_users:
                self.env['bus.bus']._sendone(
                    user.partner_id,
                    'simple_notification',
                    {
                        'title': title,
                        'message': 'Voir le journal QDV Tarifs pour le détail.',
                        'type': msg_type,
                        'sticky': bool(errors),
                    }
                )
        except Exception as e:
            _logger.warning('Notification non envoyée: %s', str(e))
