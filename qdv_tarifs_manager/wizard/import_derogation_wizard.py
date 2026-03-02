# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Import dérogations depuis Excel fabricant

IMPORTANT - Architecture anti-InFailedSqlTransaction :
  - QdvTarifImportDerogationLine n'utilise AUCUN Many2one vers modèles permanents
  - base_id du wizard est store=False
  - Chaque create de dérogation est dans un savepoint individuel
"""
import base64
import io
import logging
import warnings
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False


class QdvTarifImportDerogationWizard(models.TransientModel):
    _name = 'qdv.tarif.import.derogation.wizard'
    _description = 'Wizard import dérogations Excel QDV'

    manufacturer_code = fields.Char(string='Code fabricant', required=True)
    # store=False : évite recompute en cascade sur transaction PostgreSQL
    base_id = fields.Many2one('qdv.tarif.base', string='Base tarif',
                               compute='_compute_base_id', store=False)
    excel_file = fields.Binary(string='Fichier Excel', attachment=False)
    excel_filename = fields.Char(string='Nom du fichier')
    derogation_label_prefix = fields.Char(string='Préfixe libellé', default='Dérogation')
    price_mode_default = fields.Selection([
        ('net_price', 'Prix net €'), ('rebate', 'Remise %'),
    ], string='Mode par défaut', default='net_price')
    valid_from = fields.Date(string='Valide du')
    valid_to = fields.Date(string='Valide au')
    export_to_qdv = fields.Boolean(string='Exporter vers QDV après création', default=False)
    update_existing = fields.Boolean(string='Mettre à jour dérogations existantes', default=True)

    header_row = fields.Integer(default=0)
    col_reference = fields.Integer(default=0)
    col_description = fields.Integer(default=1)
    col_net_price = fields.Integer(default=3)
    col_rebate = fields.Integer(default=-1)

    analyse_done = fields.Boolean(default=False)
    preview_line_ids = fields.One2many('qdv.tarif.import.derogation.line', 'wizard_id',
                                        string='Aperçu des lignes')
    total_lines = fields.Integer(compute='_compute_stats')
    matched_lines = fields.Integer(compute='_compute_stats')
    warning_message = fields.Char(compute='_compute_stats')

    @api.depends('preview_line_ids')
    def _compute_stats(self):
        for rec in self:
            rec.total_lines = len(rec.preview_line_ids)
            rec.matched_lines = len(rec.preview_line_ids.filtered('article_matched'))
            nm = rec.total_lines - rec.matched_lines
            rec.warning_message = (_('%d référence(s) non trouvées.') % nm) if nm else ''

    @api.depends('manufacturer_code')
    def _compute_base_id(self):
        for rec in self:
            rec.base_id = self.env['qdv.tarif.base'].search(
                [('manufacturer_code', '=', rec.manufacturer_code)], limit=1
            ) if rec.manufacturer_code else False

    def action_analyse(self):
        self.ensure_one()
        if not HAS_OPENPYXL:
            raise UserError(_("openpyxl non installé. Lancez: pip install openpyxl --break-system-packages"))
        if not self.excel_file:
            raise UserError(_("Veuillez uploader un fichier Excel."))
        if not self.manufacturer_code:
            raise UserError(_("Veuillez renseigner le code fabricant."))

        data = base64.b64decode(self.excel_file)
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            raise UserError(_("Le fichier Excel est vide."))

        header_idx, col_map = self._detect_columns(rows)
        ref_col = col_map.get('reference', 0)
        desc_col = col_map.get('description', 1)
        price_col = col_map.get('net_price', 3)
        rebate_col = col_map.get('rebate', -1)

        self.write({
            'header_row': header_idx,
            'col_reference': ref_col,
            'col_description': desc_col,
            'col_net_price': price_col,
            'col_rebate': rebate_col,
        })

        mfr = self.manufacturer_code
        # Charger en mémoire — uniquement données scalaires
        articles_map = {
            a.reference: (a.id, a.unit_price)
            for a in self.env['qdv.tarif.article'].search([('manufacturer_code', '=', mfr)])
        }
        derogs_map = {
            d.reference: (d.id, d.derogation_label or '')
            for d in self.env['qdv.tarif.derogation'].search([('manufacturer_code', '=', mfr)])
        }

        self.preview_line_ids.unlink()

        skip_words = {'article', 'référence', 'reference', 'réf.', 'ref.', 'ref', 'code'}
        preview_vals = []

        for i, row in enumerate(rows):
            if i <= header_idx or not row:
                continue
            if ref_col >= len(row):
                continue

            raw_ref = row[ref_col]
            reference = str(raw_ref or '').strip().strip("'\" ")
            if not reference or reference.lower() in skip_words:
                continue
            if not any(v is not None and str(v).strip() for v in row):
                continue

            description = ''
            if desc_col < len(row) and row[desc_col] is not None:
                description = str(row[desc_col]).strip().strip("'\" ")[:200]

            net_price = 0.0
            rebate_pct = 0.0
            detected_mode = self.price_mode_default

            if price_col < len(row) and row[price_col] is not None:
                net_price = self._parse_price(row[price_col])
                if net_price > 0:
                    detected_mode = 'net_price'

            if rebate_col >= 0 and rebate_col < len(row) and row[rebate_col] is not None:
                rebate_pct = self._parse_price(row[rebate_col])
                if rebate_pct > 0 and net_price == 0:
                    detected_mode = 'rebate'

            if net_price == 0 and rebate_pct == 0:
                continue

            art = articles_map.get(reference)
            derog = derogs_map.get(reference)

            computed_rebate = rebate_pct
            if detected_mode == 'net_price' and art and art[1] and net_price > 0:
                computed_rebate = round((1.0 - net_price / art[1]) * 100.0, 2)

            preview_vals.append({
                'wizard_id': self.id,
                'reference': reference,
                'description': description,
                'detected_mode': detected_mode,
                'net_price_detected': net_price,
                'rebate_detected': rebate_pct,
                'computed_rebate': computed_rebate,
                'article_matched': bool(art),
                'article_record_id': art[0] if art else 0,
                'article_unit_price': art[1] if art else 0.0,
                'existing_derogation_record_id': derog[0] if derog else 0,
                'existing_derogation_label': derog[1] if derog else '',
                'import_this': True,
            })

        if not preview_vals:
            raise UserError(_(
                "Aucune ligne exploitable trouvée.\n"
                "Colonnes (base 0) : Réf=%d, Desc=%d, Prix=%d | Entête ligne %d\n"
                "Vérifiez le format du fichier."
            ) % (ref_col, desc_col, price_col, header_idx + 1))

        # Création en lot — QdvTarifImportDerogationLine est un TransientModel SANS
        # Many2one vers modèles permanents → aucun recompute externe possible
        self.env['qdv.tarif.import.derogation.line'].create(preview_vals)
        self.write({'analyse_done': True})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.tarif.import.derogation.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    @staticmethod
    def _parse_price(value):
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip().strip("'\" ")
        if not s:
            return 0.0
        s = s.replace('\xa0', '').replace(' ', '')
        if ',' in s:
            s = s.replace('.', '').replace(',', '.')
        try:
            return float(s)
        except (ValueError, TypeError):
            return 0.0

    def _detect_columns(self, rows):
        keywords = {
            'reference': ['article', 'référence', 'reference', 'réf.', 'ref.', 'ref'],
            'description': ['description', 'désignation', 'designation', 'libellé', 'libelle'],
            'net_price': ['prix unitaire', 'prix net', 'pv unitaire', 'prix unit',
                          'unitaire ht', 'prix ht', 'conseillé'],
            'rebate': ['remise', 'rebate', 'discount'],
        }
        best_score = 0
        best_idx = 1
        best_map = {}
        for row_idx, row in enumerate(rows[:25]):
            if not row:
                continue
            row_str = [str(v or '').lower().strip() for v in row]
            col_map = {}
            score = 0
            for field, kws in keywords.items():
                for ci, cell in enumerate(row_str):
                    if any(kw in cell for kw in kws):
                        col_map[field] = ci
                        score += 1
                        break
            if score > best_score:
                best_score = score
                best_idx = row_idx
                best_map = dict(col_map)
                if score >= 3:
                    break
        if 'reference' not in best_map:
            best_map['reference'] = 0
        if 'description' not in best_map:
            best_map['description'] = best_map.get('reference', 0) + 4
        if 'net_price' not in best_map:
            best_map['net_price'] = best_map.get('reference', 0) + 3
        _logger.info('QDV Import — entête L%d colonnes %s', best_idx + 1, best_map)
        return best_idx, best_map

    def action_import(self):
        self.ensure_one()
        lines = self.preview_line_ids.filtered('import_this')
        if not lines:
            raise UserError(_("Aucune ligne sélectionnée."))

        created = updated = exported = 0
        errors = []

        writer = None
        base_path = None
        if self.export_to_qdv:
            try:
                from odoo.addons.qdv_tarifs_manager.models.tarif_qdv_writer import QdvWriter
                config = self.env['qdv.tarif.config'].search([], limit=1)
                if config and config.rebates_ok:
                    writer = QdvWriter(config.rebates_file)
                base = self.env['qdv.tarif.base'].search(
                    [('manufacturer_code', '=', self.manufacturer_code)], limit=1)
                base_path = base.file_path if base else None
            except Exception as e:
                _logger.warning('QdvWriter non disponible: %s', e)

        for line in lines:
            derog = None
            article = None
            try:
                # Savepoint individuel : si une ligne échoue, les autres continuent
                with self.env.cr.savepoint():
                    article = self.env['qdv.tarif.article'].browse(line.article_record_id) \
                        if line.article_record_id else self.env['qdv.tarif.article']
                    existing = self.env['qdv.tarif.derogation'].browse(line.existing_derogation_record_id) \
                        if line.existing_derogation_record_id else self.env['qdv.tarif.derogation']

                    mode = line.detected_mode or 'net_price'
                    net_price = line.net_price_detected if mode == 'net_price' else 0.0
                    rebate = line.computed_rebate if mode == 'net_price' else line.rebate_detected
                    derog_code = line.reference
                    label = '%s — %s' % (self.derogation_label_prefix or 'Dérogation',
                                          line.description or line.reference)

                    vals = {
                        'manufacturer_code': self.manufacturer_code,
                        'reference': line.reference,
                        'derogation_code': derog_code,
                        'derogation_label': label[:120],
                        'price_mode': mode,
                        'rebate_value': rebate,
                        'net_price_override': net_price,
                        'valid_from': self.valid_from,
                        'valid_to': self.valid_to,
                        'comment': 'Import Excel: %s' % (self.excel_filename or ''),
                        'active': True,
                    }

                    if existing.exists() and self.update_existing:
                        existing.write(vals)
                        derog = existing
                        updated += 1
                    else:
                        derog = self.env['qdv.tarif.derogation'].create(vals)
                        created += 1

                    if article.exists():
                        article.write({
                            'derogation_id': derog.id,
                            'rebate_code': derog_code,
                            'rebate_value': derog.effective_rebate,
                        })

            except Exception as e:
                errors.append('%s: %s' % (line.reference, str(e)[:150]))
                _logger.error('Import dérogation %s: %s', line.reference, e)
                continue

            # Export QDV hors savepoint (fichier externe)
            if writer and derog:
                try:
                    writer.ensure_rebate_row(
                        manufacturer_code=self.manufacturer_code,
                        rebate_code=derog_code,
                        rebate_value=derog.effective_rebate,
                        label=label[:80],
                        comment='Import Excel Odoo',
                    )
                    if article and article.exists() and base_path:
                        writer.update_article_rebate_code(
                            qdb_path=base_path,
                            reference=line.reference,
                            new_rebate_code=derog_code,
                            new_rebate_value=derog.effective_rebate,
                            user_defined_field=label[:255],
                        )
                        article.write({'rebate_code': derog_code})
                    derog.write({'qdv_exported': True, 'qdv_export_date': fields.Datetime.now()})
                    exported += 1
                except Exception as e:
                    _logger.warning('Export QDV %s: %s', line.reference, e)
                    try:
                        derog.write({'qdv_export_error': str(e)[:200]})
                    except Exception:
                        pass

        parts = []
        if created:
            parts.append(_('%d créée(s)') % created)
        if updated:
            parts.append(_('%d mise(s) à jour') % updated)
        if exported:
            parts.append(_('%d exportée(s) vers QDV') % exported)
        if errors:
            parts.append(_('%d erreur(s): %s') % (len(errors), '; '.join(errors[:3])))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Import dérogations terminé'),
                'message': ' | '.join(parts) if parts else _('Aucune modification'),
                'type': 'success' if not errors else 'warning',
                'sticky': True,
            }
        }


class QdvTarifImportDerogationLine(models.TransientModel):
    """
    IMPORTANT: Aucun Many2one vers qdv.tarif.derogation ou qdv.tarif.article.
    Uniquement des Integer (IDs bruts) pour éviter les recomputes en cascade
    qui corrompent la transaction PostgreSQL (InFailedSqlTransaction).
    """
    _name = 'qdv.tarif.import.derogation.line'
    _description = 'Ligne aperçu import dérogation'

    wizard_id = fields.Many2one('qdv.tarif.import.derogation.wizard', ondelete='cascade')

    reference = fields.Char(string='Référence', readonly=True)
    description = fields.Char(string='Description', readonly=True)
    detected_mode = fields.Selection([
        ('net_price', 'Prix net €'), ('rebate', 'Remise %'),
    ], string='Mode', readonly=True)
    net_price_detected = fields.Float(string='Prix net (€)', readonly=True, digits=(12, 4))
    rebate_detected = fields.Float(string='Remise (%)', readonly=True, digits=(5, 2))
    computed_rebate = fields.Float(string='Remise calculée (%)', readonly=True, digits=(5, 2))

    # IDs bruts — JAMAIS de Many2one vers modèles permanents ici
    article_matched = fields.Boolean(string='✓', readonly=True)
    article_record_id = fields.Integer(string='ID Article', readonly=True, default=0)
    article_unit_price = fields.Float(string='Prix tarif (€)', readonly=True, digits=(12, 4))
    existing_derogation_record_id = fields.Integer(string='ID Dérog.', readonly=True, default=0)
    existing_derogation_label = fields.Char(string='Dérog. existante', readonly=True)

    import_this = fields.Boolean(string='Importer', default=True)
