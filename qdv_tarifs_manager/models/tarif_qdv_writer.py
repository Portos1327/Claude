# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Écriture vers QDV (Rebates.qdbr et .qdb)

Logique exacte observée dans QDV :
  1. Dérogation → crée une ligne dans Rebates (RebateCode = code dérog, Rebate = taux)
                  + change ColumnsDataMT.RebateCode de l'article dans le .qdb
  2. Remise négociée → MAJ DerogationRebate + UseDerogation dans Rebates

Fichiers SQLite écrits :
  - Rebates.qdbr : table Rebates (remises + dérogations)
  - *.qdb        : table ColumnsDataMT (code remise par article)

IMPORTANT : QDV doit être fermé lors de l'écriture (fichiers SQLite non verrouillés)
"""
import sqlite3
import os
import shutil
import datetime
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QdvWriter:
    """
    Classe utilitaire (non-Odoo) pour écrire dans les SQLite QDV.
    Utilisée par les méthodes des modèles Odoo.
    """

    def __init__(self, rebates_path):
        self.rebates_path = rebates_path
        if not os.path.isfile(rebates_path):
            raise FileNotFoundError("Rebates.qdbr introuvable : %s" % rebates_path)

    # =========================================================================
    # BACKUP AUTOMATIQUE
    # =========================================================================
    def _backup(self, filepath):
        """Crée une sauvegarde horodatée avant toute modification"""
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup = filepath + '.bak_%s' % ts
        shutil.copy2(filepath, backup)
        _logger.info('QDV Writer — backup créé: %s', backup)
        return backup

    # =========================================================================
    # REBATES.QDBR — Remises et dérogations
    # =========================================================================
    def ensure_rebate_row(self, manufacturer_code, rebate_code, rebate_value,
                          derogation_value=None, use_derogation=False,
                          label='', comment=''):
        """
        Crée ou met à jour une ligne dans la table Rebates de Rebates.qdbr.

        Structure observée dans Rebates.qdbr:
          ManufacturerCode, RebateCode, Rebate, DerogationRebate, UseDerogation,
          RebateLabel, RebateComment, ...
        """
        self._backup(self.rebates_path)
        conn = sqlite3.connect(self.rebates_path)
        cur = conn.cursor()

        # Vérifier les colonnes disponibles
        cur.execute("PRAGMA table_info(Rebates)")
        cols = {row[1] for row in cur.fetchall()}
        _logger.info('QDV Writer — colonnes Rebates: %s', cols)

        # Vérifier si la ligne existe
        cur.execute(
            "SELECT RowID FROM Rebates WHERE ManufacturerCode=? AND RebateCode=?",
            (manufacturer_code, rebate_code)
        )
        existing = cur.fetchone()

        # Préparer les valeurs
        dv = derogation_value if derogation_value is not None else 0.0
        ud = 1 if use_derogation else 0

        if existing:
            # UPDATE
            set_parts = ["Rebate=?", "RebateLabel=?", "RebateComment=?"]
            vals = [rebate_value, label, comment]
            if 'DerogationRebate' in cols:
                set_parts.append("DerogationRebate=?")
                vals.append(dv)
            if 'UseDerogation' in cols:
                set_parts.append("UseDerogation=?")
                vals.append(ud)
            vals.extend([manufacturer_code, rebate_code])
            sql = "UPDATE Rebates SET %s WHERE ManufacturerCode=? AND RebateCode=?" % ', '.join(set_parts)
            cur.execute(sql, vals)
            _logger.info('QDV Writer — UPDATE Rebates %s/%s → remise=%.2f, derog=%.2f, useDerog=%d',
                         manufacturer_code, rebate_code, rebate_value, dv, ud)
        else:
            # INSERT
            insert_cols = ['ManufacturerCode', 'RebateCode', 'Rebate', 'RebateLabel', 'RebateComment']
            insert_vals = [manufacturer_code, rebate_code, rebate_value, label, comment]
            if 'DerogationRebate' in cols:
                insert_cols.append('DerogationRebate')
                insert_vals.append(dv)
            if 'UseDerogation' in cols:
                insert_cols.append('UseDerogation')
                insert_vals.append(ud)
            placeholders = ','.join(['?'] * len(insert_vals))
            sql = "INSERT INTO Rebates (%s) VALUES (%s)" % (','.join(insert_cols), placeholders)
            cur.execute(sql, insert_vals)
            _logger.info('QDV Writer — INSERT Rebates %s/%s → remise=%.2f',
                         manufacturer_code, rebate_code, rebate_value)

        conn.commit()
        conn.close()

    def remove_rebate_row(self, manufacturer_code, rebate_code):
        """Supprime une ligne de Rebates (quand on retire une dérogation)"""
        self._backup(self.rebates_path)
        conn = sqlite3.connect(self.rebates_path)
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM Rebates WHERE ManufacturerCode=? AND RebateCode=?",
            (manufacturer_code, rebate_code)
        )
        deleted = cur.rowcount
        conn.commit()
        conn.close()
        _logger.info('QDV Writer — DELETE Rebates %s/%s (%d lignes)', manufacturer_code, rebate_code, deleted)
        return deleted

    def update_negotiated_rebate(self, manufacturer_code, rebate_code, negotiated_value, use_negotiated):
        """
        Met à jour la remise dérogée (DerogationRebate + UseDerogation) dans Rebates.qdbr.
        Utilisé quand on change une remise négociée depuis Odoo.
        """
        self._backup(self.rebates_path)
        conn = sqlite3.connect(self.rebates_path)
        cur = conn.cursor()

        cur.execute("PRAGMA table_info(Rebates)")
        cols = {row[1] for row in cur.fetchall()}

        set_parts = []
        vals = []
        if 'DerogationRebate' in cols:
            set_parts.append("DerogationRebate=?")
            vals.append(negotiated_value)
        if 'UseDerogation' in cols:
            set_parts.append("UseDerogation=?")
            vals.append(1 if use_negotiated else 0)

        if set_parts:
            vals.extend([manufacturer_code, rebate_code])
            sql = "UPDATE Rebates SET %s WHERE ManufacturerCode=? AND RebateCode=?" % ', '.join(set_parts)
            cur.execute(sql, vals)
            updated = cur.rowcount
            conn.commit()
            _logger.info('QDV Writer — UPDATE négociée %s/%s → %.2f%% (use=%d), %d lignes',
                         manufacturer_code, rebate_code, negotiated_value, use_negotiated, updated)
        else:
            updated = 0
            _logger.warning('QDV Writer — colonnes DerogationRebate/UseDerogation absentes dans Rebates')

        conn.close()
        return updated

    # =========================================================================
    # .QDB — Code remise par article dans ColumnsDataMT
    # =========================================================================
    def update_article_rebate_code(self, qdb_path, reference, new_rebate_code,
                                   new_rebate_value=None, user_defined_field=None):
        """
        Change le RebateCode (et optionnellement Rebate + UserDefinedField) dans ColumnsDataMT et Articles.
        Jointure: Articles.Reference → Articles.RowID → ColumnsDataMT.IDInArticles
        user_defined_field: si fourni, mis à jour dans Articles.UserDefinedField (libellé dérogation)
        """
        if not os.path.isfile(qdb_path):
            raise FileNotFoundError("Base QDV introuvable : %s" % qdb_path)

        self._backup(qdb_path)
        conn = sqlite3.connect(qdb_path)
        cur = conn.cursor()

        # Trouver RowID de l'article
        cur.execute("SELECT RowID FROM Articles WHERE Reference=?", (reference,))
        article_row = cur.fetchone()
        if not article_row:
            conn.close()
            raise ValueError("Référence '%s' introuvable dans Articles" % reference)

        article_id = article_row[0]

        # MAJ ColumnsDataMT (RebateCode + optionnellement Rebate)
        if new_rebate_value is not None:
            cur.execute(
                "UPDATE ColumnsDataMT SET RebateCode=?, Rebate=? WHERE IDInArticles=?",
                (new_rebate_code, new_rebate_value, article_id)
            )
        else:
            cur.execute(
                "UPDATE ColumnsDataMT SET RebateCode=? WHERE IDInArticles=?",
                (new_rebate_code, article_id)
            )

        # MAJ Articles.UserDefinedField si fourni (libellé dérogation)
        if user_defined_field is not None:
            cur.execute(
                "UPDATE Articles SET UserDefinedField=? WHERE RowID=?",
                (user_defined_field[:255] if user_defined_field else '', article_id)
            )

        updated = cur.rowcount
        conn.commit()
        conn.close()
        _logger.info('QDV Writer — UPDATE ref=%s → RebateCode=%s, UserDefined=%s, %d lignes',
                     reference, new_rebate_code, user_defined_field or '', updated)
        return updated


# =============================================================================
# MIXIN ODOO — ajouté aux modèles Odoo pour exposer les actions d'export
# =============================================================================

class QdvTarifDerogationExport(models.Model):
    _inherit = 'qdv.tarif.derogation'

    # Statut export QDV
    qdv_exported = fields.Boolean(
        string='Exporté vers QDV',
        default=False,
        help='Indique si cette dérogation a été écrite dans les fichiers QDV'
    )
    qdv_export_date = fields.Datetime(
        string='Date export QDV',
        readonly=True
    )
    qdv_export_error = fields.Char(
        string='Erreur export QDV',
        readonly=True
    )

    # =========================================================================
    # EXPORT DÉROGATION → QDV
    # =========================================================================
    def action_export_to_qdv(self):
        """
        Exporte la/les dérogation(s) sélectionnée(s) vers QDV.
        Fonctionne en sélection multiple depuis la liste.
        """
        errors = []
        success_count = 0

        for rec in self:
            try:
                config = self.env['qdv.tarif.config'].search([], limit=1)
                if not config or not config.rebates_ok:
                    raise UserError(_("Rebates.qdbr introuvable. Vérifiez la configuration."))

                writer = QdvWriter(config.rebates_file)

                # 1. Écrire dans Rebates.qdbr
                writer.ensure_rebate_row(
                    manufacturer_code=rec.manufacturer_code,
                    rebate_code=rec.derogation_code,
                    rebate_value=rec.effective_rebate,
                    derogation_value=0.0,
                    use_derogation=False,
                    label=rec.derogation_label or rec.derogation_code,
                    comment=rec.comment or '',
                )

                # 2. Modifier le RebateCode + UserDefinedField de l'article dans le .qdb
                if rec.article_id and rec.base_id and rec.base_id.file_path:
                    writer.update_article_rebate_code(
                        qdb_path=rec.base_id.file_path,
                        reference=rec.reference,
                        new_rebate_code=rec.derogation_code,
                        new_rebate_value=rec.effective_rebate,
                        user_defined_field=rec.derogation_label or rec.derogation_code,
                    )
                    # MAJ rebate_code dans Odoo pour refléter le nouveau code remise QDV
                    rec.article_id.write({'rebate_code': rec.derogation_code})

                rec.write({
                    'qdv_exported': True,
                    'qdv_export_date': fields.Datetime.now(),
                    'qdv_export_error': False,
                })
                success_count += 1

            except Exception as e:
                err = str(e)[:300]
                rec.write({'qdv_export_error': err, 'qdv_exported': False})
                errors.append("%s/%s : %s" % (rec.manufacturer_code, rec.derogation_code, err))
                _logger.error('Erreur export dérogation %s: %s', rec.derogation_code, err)

        if errors:
            raise UserError(_("Erreur(s) lors de l'export vers QDV:\n%s") % '\n'.join(errors))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Export QDV réussi'),
                'message': _('%d dérogation(s) écrite(s) dans les fichiers QDV.') % success_count,
                'type': 'success', 'sticky': False,
            }
        }

    def action_remove_from_qdv(self):
        """
        Retire la/les dérogation(s) de QDV et remet le code remise famille d'origine.
        Fonctionne en sélection multiple.
        """
        errors = []
        success = 0
        try:
            config = self.env['qdv.tarif.config'].search([], limit=1)
            if not config or not config.rebates_ok:
                raise UserError(_("Rebates.qdbr introuvable."))
            writer = QdvWriter(config.rebates_file)
        except Exception as e:
            raise UserError(_("Impossible d'initialiser QdvWriter: %s") % str(e))

        for rec in self:
            try:
                # 1. Supprimer la ligne dérogation de Rebates.qdbr
                writer.remove_rebate_row(rec.manufacturer_code, rec.derogation_code)

                # 2. Remettre le code remise QDV d'origine dans ColumnsDataMT
                # + vider UserDefinedField (dérogation levée)
                if rec.article_id and rec.base_id and rec.base_id.file_path:
                    original_rebate_code = rec.article_id.rebate_code or rec.article_id.family_code or ''
                    writer.update_article_rebate_code(
                        qdb_path=rec.base_id.file_path,
                        reference=rec.reference,
                        new_rebate_code=original_rebate_code,
                        new_rebate_value=None,
                        user_defined_field='',  # Vider le champ utilisateur
                    )
                    # Restaurer rebate_code dans Odoo
                    rec.article_id.write({'rebate_code': original_rebate_code})

                rec.write({
                    'qdv_exported': False,
                    'qdv_export_date': False,
                    'qdv_export_error': False,
                })
                success += 1

            except Exception as e:
                err = str(e)[:300]
                rec.write({'qdv_export_error': err})
                errors.append("%s/%s : %s" % (rec.manufacturer_code, rec.derogation_code, err))

        if errors:
            raise UserError(_("Erreur(s) retrait QDV:\n%s") % '\n'.join(errors))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dérogations retirées de QDV'),
                'message': _('%d dérogation(s) supprimées de Rebates.qdbr, codes remises familles restaurés.') % success,
                'type': 'warning', 'sticky': False,
            }
        }

    def action_delete_and_revert_qdv(self):
        """
        Supprime toutes les dérogations sélectionnées dans Odoo ET dans QDV.
        Remet les codes remises QDV d'origine dans les .qdb.
        """
        # D'abord retirer de QDV (Rebates.qdbr + ColumnsDataMT)
        self.action_remove_from_qdv()
        count = len(self)

        # Délier les articles qui pointaient vers ces dérogations
        articles = self.env['qdv.tarif.article'].search([
            ('derogation_id', 'in', self.ids)
        ])
        if articles:
            articles.write({'derogation_id': False})

        # Supprimer les enregistrements Odoo
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Dérogations supprimées'),
                'message': _('%d dérogation(s) supprimées d\'Odoo et de QDV.') % count,
                'type': 'danger', 'sticky': True,
            }
        }


class QdvTarifRebateExport(models.Model):
    _inherit = 'qdv.tarif.rebate'

    qdv_exported = fields.Boolean(string='Exporté vers QDV', default=False)
    qdv_export_date = fields.Datetime(string='Date export QDV', readonly=True)
    qdv_export_error = fields.Char(string='Erreur export QDV', readonly=True)

    # =========================================================================
    # EXPORT REMISE NÉGOCIÉE → QDV
    # =========================================================================
    def action_export_negotiated_to_qdv(self):
        """
        Pousse la remise négociée (DerogationRebate + UseDerogation) dans Rebates.qdbr.
        Seule la colonne DerogationRebate est modifiée — le taux catalogue Rebate est préservé.
        """
        errors = []
        success = 0

        for rec in self:
            try:
                config = self.env['qdv.tarif.config'].search([], limit=1)
                if not config or not config.rebates_ok:
                    raise UserError(_("Rebates.qdbr introuvable."))

                writer = QdvWriter(config.rebates_file)
                writer.update_negotiated_rebate(
                    manufacturer_code=rec.manufacturer_code,
                    rebate_code=rec.rebate_code,
                    negotiated_value=rec.negotiated_value if rec.use_negotiated else 0.0,
                    use_negotiated=rec.use_negotiated,
                )

                rec.write({
                    'qdv_exported': True,
                    'qdv_export_date': fields.Datetime.now(),
                    'qdv_export_error': False,
                })
                success += 1

            except Exception as e:
                err = str(e)[:300]
                rec.write({'qdv_export_error': err, 'qdv_exported': False})
                errors.append("%s/%s : %s" % (rec.manufacturer_code, rec.rebate_code, err))

        if errors:
            raise UserError(_("Erreur(s) export remises:\n%s") % '\n'.join(errors))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Remises exportées vers QDV'),
                'message': _('%d remise(s) négociée(s) écrite(s) dans Rebates.qdbr.') % success,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_export_all_negotiated(self):
        """Export en masse : toutes les remises négociées du même fabricant"""
        self.ensure_one()
        all_negotiated = self.env['qdv.tarif.rebate'].search([
            ('base_id', '=', self.base_id.id),
            ('use_negotiated', '=', True),
            ('negotiated_value', '>', 0),
        ])
        return all_negotiated.action_export_negotiated_to_qdv()
