# -*- coding: utf-8 -*-
"""
QDV Tarifs Manager - Wizard d'import des articles QDV
Lit la base .qdb SQLite et importe les articles dans qdv.tarif.article
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import os
import sqlite3
import json

_logger = logging.getLogger(__name__)


class QdvTarifImportWizard(models.TransientModel):
    _name = 'qdv.tarif.import.wizard'
    _description = "Wizard import articles QDV"

    # =========================================================================
    # BASES À IMPORTER
    # =========================================================================
    base_ids = fields.Many2many(
        'qdv.tarif.base',
        string='Bases à importer',
        help='Bases tarifs dont les articles seront importés'
    )
    single_base_id = fields.Many2one(
        'qdv.tarif.base',
        string='Base unique',
        help='Rempli quand on importe depuis la fiche d\'une base'
    )

    # =========================================================================
    # OPTIONS
    # =========================================================================
    update_existing = fields.Boolean(
        string='Mettre à jour les articles existants',
        default=True,
        help='Si coché, les articles déjà importés seront mis à jour (prix, désignation...)'
    )
    apply_rebates = fields.Boolean(
        string='Appliquer les remises',
        default=True,
        help='Calcule le prix net en appliquant les remises Rebates.qdbr'
    )
    create_odoo_products = fields.Boolean(
        string='Créer les produits Odoo automatiquement',
        default=False,
        help='Crée un product.template pour chaque article importé'
    )
    limit_rows = fields.Integer(
        string='Limite lignes (0 = tout)',
        default=0,
        help='Pour test: limite le nombre d\'articles importés par base (0 = pas de limite)'
    )

    # =========================================================================
    # RÉSULTATS
    # =========================================================================
    result_message = fields.Text(string='Résultat', readonly=True)
    import_done = fields.Boolean(default=False)

    # =========================================================================
    # SCAN ET IMPORT
    # =========================================================================
    def action_import(self):
        """Lance l'import des articles pour toutes les bases sélectionnées"""
        self.ensure_one()
        bases = self.base_ids or (self.single_base_id and self.single_base_id) or self.env['qdv.tarif.base']

        if not bases:
            raise UserError(_("Aucune base sélectionnée."))

        results = []
        total_created = 0
        total_updated = 0
        total_errors = 0

        for base in bases:
            if not base.file_path or not os.path.isfile(base.file_path):
                results.append("❌ %s (%s): Fichier .qdb introuvable" % (base.manufacturer_name, base.manufacturer_code))
                total_errors += 1
                continue

            try:
                created, updated, errors = self._import_base(base)
                total_created += created
                total_updated += updated
                total_errors += errors
                results.append("✅ %s (%s): %d créés, %d MAJ, %d erreurs" % (
                    base.manufacturer_name, base.manufacturer_code,
                    created, updated, errors
                ))
                base.write({
                    'import_state': 'imported' if errors == 0 else 'partial',
                    'last_import_date': fields.Datetime.now(),
                    'import_error': '',
                })
            except Exception as e:
                err_msg = str(e)[:500]
                results.append("❌ %s (%s): %s" % (base.manufacturer_name, base.manufacturer_code, err_msg))
                base.write({'import_state': 'error', 'import_error': err_msg})
                total_errors += 1

        summary = _("Import terminé:\n- %d articles créés\n- %d articles mis à jour\n- %d erreurs\n\n") % (
            total_created, total_updated, total_errors
        )
        self.write({
            'result_message': summary + '\n'.join(results),
            'import_done': True,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.tarif.import.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _import_base(self, base):
        """
        Importe les articles d'une base .qdb.

        Structure QDV 18 observée:
          - Articles      → Reference, Description, Family, Unit
          - ColumnsDataMT → IDInArticles (FK→Articles.RowID), CostPerUnitMT (prix tarif),
                            RebateCode (code remise famille), Rebate (taux remise)

        On fait une jointure LEFT JOIN pour récupérer le prix et le code remise.
        Fallback: si ColumnsDataMT n'existe pas, on tente les colonnes classiques.
        """
        conn = sqlite3.connect(base.file_path)
        cur = conn.cursor()

        # Tables disponibles
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cur.fetchall()]

        # Préférence de table articles
        article_table = None
        for candidate in ['Articles', 'ArticlesTable', 'BigLocalTable', 'Items', 'PriceTable']:
            if candidate in tables:
                article_table = candidate
                break
        if not article_table:
            # Prendre la plus grande table
            max_count = 0
            for t in tables:
                try:
                    cur.execute("SELECT COUNT(*) FROM \"%s\"" % t)
                    c = cur.fetchone()[0]
                    if c > max_count:
                        max_count = c
                        article_table = t
                except Exception:
                    pass
        if not article_table:
            conn.close()
            raise UserError(_("Impossible de trouver la table articles dans %s") % base.file_name)

        # Colonnes de la table articles
        cur.execute("PRAGMA table_info(\"%s\")" % article_table)
        article_cols = [row[1] for row in cur.fetchall()]

        # =====================================================================
        # CAS 1: ColumnsDataMT présente → jointure pour prix + code remise
        # (structure QDV standard observée sur ACOME, etc.)
        # =====================================================================
        use_join = 'ColumnsDataMT' in tables

        if use_join:
            cur.execute("PRAGMA table_info(ColumnsDataMT)")
            mt_cols = [row[1] for row in cur.fetchall()]
            has_cost = 'CostPerUnitMT' in mt_cols
            has_rebate_code = 'RebateCode' in mt_cols
            has_rebate_val = 'Rebate' in mt_cols

            # Colonnes à sélectionner depuis Articles
            art_select = []
            ref_col = self._find_col(article_cols, ['Reference', 'Ref', 'Code', 'ArticleCode'])
            des_col = self._find_col(article_cols, ['Description', 'Designation', 'Libelle', 'Label', 'Name'])
            fam_col = self._find_col(article_cols, ['Family', 'Famille', 'FamilyCode', 'Categorie'])
            unit_col = self._find_col(article_cols, ['Unit', 'Unite', 'UOM'])

            if not ref_col:
                conn.close()
                raise UserError(_("Colonne référence introuvable dans %s") % article_table)

            art_select.append('a."%s" AS reference' % ref_col)
            art_select.append('a."%s" AS designation' % des_col if des_col else "'' AS designation")
            art_select.append('a."%s" AS family_code' % fam_col if fam_col else "'' AS family_code")
            art_select.append('a."%s" AS unit' % unit_col if unit_col else "'U' AS unit")

            mt_select = []
            mt_select.append('mt.CostPerUnitMT AS unit_price' if has_cost else '0.0 AS unit_price')
            mt_select.append('mt.RebateCode AS rebate_code_mt' if has_rebate_code else "'' AS rebate_code_mt")
            mt_select.append('mt.Rebate AS rebate_val_mt' if has_rebate_val else '0.0 AS rebate_val_mt')

            query = """
                SELECT {art}, {mt}
                FROM "{table}" a
                LEFT JOIN ColumnsDataMT mt ON mt.IDInArticles = a.RowID
            """.format(
                art=', '.join(art_select),
                mt=', '.join(mt_select),
                table=article_table,
            )
            if self.limit_rows > 0:
                query += " LIMIT %d" % self.limit_rows

            cur.execute(query)
            col_names = [d[0] for d in cur.description]
            rows = [dict(zip(col_names, row)) for row in cur.fetchall()]

        # =====================================================================
        # CAS 2: pas de ColumnsDataMT → détection classique par noms de colonnes
        # =====================================================================
        else:
            col_map = self._detect_columns(article_cols)
            select_cols = [c for c in col_map.values() if c]
            if not select_cols:
                conn.close()
                raise UserError(_("Aucune colonne reconnue dans %s") % article_table)

            query = 'SELECT %s FROM "%s"' % (
                ', '.join('"%s"' % c for c in select_cols),
                article_table
            )
            if self.limit_rows > 0:
                query += " LIMIT %d" % self.limit_rows

            cur.execute(query)
            raw_rows = cur.fetchall()
            rows = []
            for row in raw_rows:
                d = dict(zip(select_cols, row))
                rows.append({
                    'reference': d.get(col_map.get('reference'), ''),
                    'designation': d.get(col_map.get('designation'), ''),
                    'family_code': d.get(col_map.get('family_code'), ''),
                    'unit': d.get(col_map.get('unit'), 'U'),
                    'unit_price': d.get(col_map.get('unit_price'), 0.0),
                    'rebate_code_mt': '',
                    'rebate_val_mt': 0.0,
                })

        conn.close()

        # =====================================================================
        # IMPORT DES FAMILLES depuis TreeTable (si présente)
        # =====================================================================
        self._import_families(base)

        # Charger les remises stockées (pour fallback ou enrichissement)
        rebates_map = {}
        if self.apply_rebates:
            rebates_map = {r.rebate_code: r.effective_rebate for r in base.rebate_ids}

        # Charger articles existants
        existing = {
            a.reference: a
            for a in self.env['qdv.tarif.article'].search([('base_id', '=', base.id)])
        }

        created = 0
        updated = 0
        errors = 0

        for row in rows:
            try:
                reference = str(row.get('reference') or '').strip()
                if not reference:
                    continue

                # Prix tarif (depuis ColumnsDataMT.CostPerUnitMT en priorité)
                unit_price = 0.0
                try:
                    raw = row.get('unit_price')
                    if raw is not None:
                        unit_price = float(str(raw).replace(',', '.'))
                except Exception:
                    pass

                family_code = str(row.get('family_code') or '').strip()

                # Code et taux remise
                # Priorité: RebateCode depuis ColumnsDataMT > recherche dans rebates_map
                rebate_code_mt = str(row.get('rebate_code_mt') or '').strip()
                rebate_val_mt = 0.0
                try:
                    rebate_val_mt = float(row.get('rebate_val_mt') or 0)
                except Exception:
                    pass

                rebate_code_applied = ''
                rebate_value = 0.0

                if rebate_code_mt and rebate_code_mt in rebates_map:
                    # Code remise direct depuis ColumnsDataMT → chercher taux dans rebates_map
                    rebate_code_applied = rebate_code_mt
                    rebate_value = rebates_map[rebate_code_mt]
                elif rebate_val_mt > 0:
                    # Taux remise direct depuis ColumnsDataMT
                    rebate_code_applied = rebate_code_mt
                    rebate_value = rebate_val_mt
                elif family_code and rebates_map:
                    # Fallback: recherche par famille (code exact puis wildcard)
                    if family_code in rebates_map:
                        rebate_code_applied = family_code
                        rebate_value = rebates_map[family_code]
                    else:
                        parts = family_code.split('_')
                        if len(parts) >= 2:
                            wildcard = parts[0] + '_*'
                            if wildcard in rebates_map:
                                rebate_code_applied = wildcard
                                rebate_value = rebates_map[wildcard]

                # Libellé famille depuis TreeTable si dispo (lecture lazy non bloquante)
                family_label = ''

                vals = {
                    'base_id': base.id,
                    'reference': reference,
                    'designation': str(row.get('designation') or '')[:500],
                    'unit_price': unit_price,
                    'unit': str(row.get('unit') or 'U')[:10],
                    'family_code': family_code,
                    'rebate_code': rebate_code_applied,
                    'rebate_value': rebate_value,
                    'import_date': fields.Datetime.now(),
                }

                if reference in existing:
                    if self.update_existing:
                        existing[reference].write(vals)
                        updated += 1
                else:
                    new_article = self.env['qdv.tarif.article'].create(vals)
                    existing[reference] = new_article
                    created += 1
                    if self.create_odoo_products and not new_article.product_id:
                        try:
                            new_article.action_create_product()
                        except Exception:
                            pass

            except Exception as e:
                _logger.warning("Erreur import article: %s", str(e))
                errors += 1

        return created, updated, errors

    def _find_col(self, columns, candidates):
        """Cherche la première colonne correspondant à un des candidats (insensible à la casse)"""
        col_lower = {c.lower(): c for c in columns}
        for candidate in candidates:
            if candidate.lower() in col_lower:
                return col_lower[candidate.lower()]
        return None

    def _import_families(self, base):
        """
        Importe l'arborescence des familles depuis TreeTable de la base .qdb.
        TreeTable: FamilyValue (code), FamilyText (libellé)
        """
        if not base.file_path or not os.path.isfile(base.file_path):
            return
        try:
            conn = sqlite3.connect(base.file_path)
            cur = conn.cursor()

            # Vérifier que TreeTable existe
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='TreeTable'")
            if not cur.fetchone():
                conn.close()
                return

            cur.execute("SELECT FamilyValue, FamilyText FROM TreeTable ORDER BY FamilyValue")
            rows = cur.fetchall()
            conn.close()

            if not rows:
                return

            # Familles existantes pour cette base
            existing = {
                f.family_code: f
                for f in self.env['qdv.tarif.family'].search([('base_id', '=', base.id)])
            }

            created_fam = 0
            updated_fam = 0
            for (fam_code, fam_label) in rows:
                if not fam_code:
                    continue
                fam_code = str(fam_code).strip()
                fam_label = str(fam_label or '').strip()
                vals = {
                    'base_id': base.id,
                    'family_code': fam_code,
                    'family_label': fam_label,
                }
                if fam_code in existing:
                    if existing[fam_code].family_label != fam_label:
                        existing[fam_code].write({'family_label': fam_label})
                        updated_fam += 1
                else:
                    self.env['qdv.tarif.family'].create(vals)
                    existing[fam_code] = True
                    created_fam += 1

            _logger.info('Familles %s: %d créées, %d MAJ', base.manufacturer_code, created_fam, updated_fam)

        except Exception as e:
            _logger.warning('Erreur import familles %s: %s', base.manufacturer_code, str(e))
