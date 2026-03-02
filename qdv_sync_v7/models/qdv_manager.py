# -*- coding: utf-8 -*-
"""
QDV Manager - Sync complète avec création articles corrigée
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class QdvSupplierManager(models.Model):
    _inherit = 'qdv.supplier'

    auto_create_articles = fields.Boolean(string='Créer nouveaux articles', default=True)
    auto_delete_obsolete = fields.Boolean(string='Supprimer obsolètes', default=False)
    default_family = fields.Char(string='Famille par défaut', default='NOUVEAUX')
    auto_material_kind = fields.Boolean(string='Auto MaterialKindID', default=True,
        help='Détermine automatiquement le MaterialKindID depuis la famille QDV')
    
    # Champ pour le prix par défaut
    price_field = fields.Char(string='Champ prix Odoo', default='price_net',
        help='Nom du champ contenant le prix (ex: price_net, prix_net, price_per_ml)')
    
    qdv_article_count = fields.Integer(string='Articles QDV', readonly=True)
    last_qdv_read = fields.Datetime(readonly=True)

    def action_import_families_from_qdv(self):
        """Importe les familles depuis la base QDV avec arborescence"""
        self.ensure_one()
        qdv_path = self._find_qdv_file()
        if not qdv_path:
            raise UserError(_("Base QDV non trouvée!"))
        
        try:
            import sqlite3
            conn = sqlite3.connect(qdv_path)
            cur = conn.cursor()
            cur.execute("SELECT FamilyValue, FamilyText FROM TreeTable ORDER BY FamilyValue")
            families = cur.fetchall()
            conn.close()
            
            self.family_ids.unlink()
            created = 0
            family_map = {}
            
            for code, name in families:
                if not code:
                    continue
                code = str(code).strip()
                name = str(name).strip() if name else code
                
                parent_id = False
                if len(code) > 1:
                    for i in range(len(code) - 1, 0, -1):
                        parent_code = code[:i]
                        if parent_code in family_map:
                            parent_id = family_map[parent_code].id
                            break
                
                family = self.env['qdv.family'].create({
                    'supplier_id': self.id, 'code': code, 'name': name, 'parent_id': parent_id,
                })
                family_map[code] = family
                created += 1
            
            self.write({'last_qdv_read': fields.Datetime.now()})
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': 'Import terminé!', 'message': '%d familles' % created, 'type': 'success', 'sticky': False}}
        except Exception as e:
            raise UserError(str(e))

    def action_full_sync_qdv(self):
        """Sync complète: Odoo vers QDV"""
        self.ensure_one()
        qdv_path = self._find_qdv_file()
        if not qdv_path:
            raise UserError(_("Base QDV non trouvée!"))
        
        import time
        start_time = time.time()
        
        log = self.env['qdv.sync.log'].create({
            'supplier_id': self.id, 'sync_start': fields.Datetime.now(),
            'status': 'running', 'log_type': 'qdv_full'
        })
        
        try:
            result = self._full_sync_direct(qdv_path)
            duration = time.time() - start_time
            msg = "MAJ: %d, Créés: %d" % (result['updated'], result['created'])
            if result.get('reconciled', 0):
                msg += ", Réconciliés: %d" % result['reconciled']
            msg += ", Obsolètes: %d" % result['obsolete']
            
            log.write({
                'sync_end': fields.Datetime.now(), 'duration': duration,
                'records_processed': result['total_odoo'], 'records_created': result['created'],
                'records_updated': result['updated'], 'records_errors': result['obsolete'],
                'status': 'success', 'error_message': msg,
            })
            self.write({
                'last_qdv_update': fields.Datetime.now(),
                'last_qdv_count': result['updated'] + result['created'],
                'last_qdv_obsolete': result['obsolete'],
            })
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                'params': {'title': 'Sync complète!', 'message': msg, 'type': 'success', 'sticky': False}}
        except Exception as e:
            log.write({'sync_end': fields.Datetime.now(), 'status': 'error', 'error_message': str(e)})
            raise UserError(str(e))

    def _full_sync_direct(self, qdv_path):
        """Sync complète Odoo vers QDV avec réconciliation et MaterialKindID"""
        import sqlite3
        
        _logger.info("=== SYNC COMPLÈTE QDV ===")
        
        # Charger les mappings
        map_art, map_mt = {}, {}
        ref_field, manufacturer_field = None, None
        
        for m in self.field_mapping_ids:
            if not m.active or m.sync_direction in ('qdv_to_odoo', 'none', False, None, ''):
                continue
            if m.is_key:
                ref_field = m.odoo_field
            if 'manufacturer' in (m.odoo_field or '').lower() or 'fabricant' in (m.odoo_field or '').lower():
                manufacturer_field = m.odoo_field
            if m.qdv_table == 'articles':
                map_art[m.qdv_column] = m
            elif m.qdv_table == 'columns_data_mt':
                map_mt[m.qdv_column] = m
        
        if not ref_field:
            ref_field = 'reference'
        
        _logger.info("  Mapping Articles: %s", list(map_art.keys()))
        _logger.info("  Mapping MT: %s", list(map_mt.keys()))
        
        # Charger les données Odoo
        records = self._get_source_data()
        _logger.info("  %d enregistrements Odoo", len(records))
        
        odoo_data, odoo_by_stripped = {}, {}
        for rec in records:
            data = self._extract_record_data(rec)
            ref = str(data.get(ref_field, '') or '')
            if ref:
                odoo_data[ref] = data
                stripped = ref.lstrip('0')
                if stripped:
                    odoo_by_stripped.setdefault(stripped, []).append((ref, data))
        
        user_field = self._format_template({})
        family_mapping = self._build_family_mapping()
        
        # QDV - récupérer aussi MaterialKindID par famille
        conn_qdv = sqlite3.connect(qdv_path)
        cur_qdv = conn_qdv.cursor()
        
        # Mapping famille → MaterialKindID depuis les articles existants
        family_to_material_kind = {}
        try:
            cur_qdv.execute("""
                SELECT DISTINCT a.Family, m.MaterialKindID 
                FROM Articles a JOIN ColumnsDataMT m ON m.IDInArticles = a.RowID
                WHERE a.Family IS NOT NULL AND m.MaterialKindID IS NOT NULL AND m.MaterialKindID != ''
            """)
            for fam, mk in cur_qdv.fetchall():
                if fam and mk:
                    family_to_material_kind[fam.upper().strip()] = mk
        except:
            pass
        _logger.info("  Mapping famille→MaterialKindID: %d familles", len(family_to_material_kind))
        
        # Articles QDV
        cur_qdv.execute("SELECT RowID, Reference, Manufacturer FROM Articles")
        qdv_articles, qdv_by_stripped = {}, {}
        for row_id, ref, mfr in cur_qdv.fetchall():
            if ref:
                ref = str(ref)
                qdv_articles[ref] = {'row_id': row_id, 'manufacturer': str(mfr or '').upper().strip()}
                stripped = ref.lstrip('0')
                if stripped:
                    qdv_by_stripped.setdefault(stripped, []).append((ref, row_id, str(mfr or '').upper().strip()))
        
        refs_odoo, refs_qdv = set(odoo_data.keys()), set(qdv_articles.keys())
        to_update = refs_odoo & refs_qdv
        to_create = refs_odoo - refs_qdv
        potential_obsolete = refs_qdv - refs_odoo
        
        updated, created, reconciled = 0, 0, 0
        refs_reconciled = set()
        
        # Réconciliation références avec zéros manquants
        for qdv_ref in list(potential_obsolete):
            stripped_qdv = qdv_ref.lstrip('0')
            if not stripped_qdv or stripped_qdv not in odoo_by_stripped:
                continue
            
            qdv_info = qdv_articles[qdv_ref]
            for odoo_ref, odoo_data_item in odoo_by_stripped[stripped_qdv]:
                if odoo_ref == qdv_ref:
                    continue
                odoo_mfr = ''
                if manufacturer_field:
                    odoo_mfr = str(odoo_data_item.get(manufacturer_field, '') or '').upper().strip()
                qdv_mfr = qdv_info['manufacturer']
                
                # Match si même fabricant ou l'un des deux vide
                if (qdv_mfr == odoo_mfr) or (not qdv_mfr) or (not odoo_mfr) or (qdv_mfr in odoo_mfr) or (odoo_mfr in qdv_mfr):
                    _logger.info("  RÉCONCILIATION: QDV '%s' → '%s'", qdv_ref, odoo_ref)
                    cur_qdv.execute("UPDATE Articles SET Reference=? WHERE RowID=?", (odoo_ref, qdv_info['row_id']))
                    self._update_qdv_article(cur_qdv, qdv_info['row_id'], odoo_data_item, map_art, map_mt, 
                                           user_field, family_mapping, family_to_material_kind)
                    refs_reconciled.add(qdv_ref)
                    to_create.discard(odoo_ref)
                    reconciled += 1
                    break
        
        # MAJ existants
        for ref in to_update:
            self._update_qdv_article(cur_qdv, qdv_articles[ref]['row_id'], odoo_data[ref], 
                                   map_art, map_mt, user_field, family_mapping, family_to_material_kind)
            updated += 1
        
        # Créer nouveaux - AVEC TOUTES LES COLONNES
        if self.auto_create_articles and to_create:
            default_family_code = self._get_or_create_family(cur_qdv, self.default_family or 'NOUVEAUX')
            price_field = self.price_field or 'price_net'
            
            for ref in to_create:
                data = odoo_data[ref]
                
                # === INSERT Articles ===
                art_cols, art_vals = ['Reference'], [ref]
                family_val = ''
                
                for col, m in map_art.items():
                    if m.is_key:
                        continue
                    v = self._get_mapping_value(m, data, user_field, family_mapping, cur_qdv)
                    art_cols.append(col)
                    if col == 'Family':
                        family_val = v
                        art_vals.append(v if v else default_family_code)
                    else:
                        art_vals.append(v if v is not None else '')
                
                cur_qdv.execute("INSERT INTO Articles (" + ",".join(art_cols) + ") VALUES (" + ",".join(["?"] * len(art_vals)) + ")", art_vals)
                new_row_id = cur_qdv.lastrowid
                
                # === INSERT ColumnsDataMT - TOUJOURS avec le prix ===
                mt_cols, mt_vals = ['IDInArticles'], [new_row_id]
                has_price = False
                
                for col, m in map_mt.items():
                    v = self._get_mapping_value(m, data, user_field, family_mapping, cur_qdv)
                    mt_cols.append(col)
                    if col == 'CostPerUnitMT':
                        has_price = True
                    mt_vals.append(v if v is not None else (0 if col in ('CostPerUnitMT', 'Rebate') else ''))
                
                # Si pas de CostPerUnitMT dans le mapping, l'ajouter quand même
                if not has_price:
                    mt_cols.append('CostPerUnitMT')
                    price = data.get(price_field, data.get('price_net', data.get('prix_net', data.get('price_per_ml', 0))))
                    try:
                        mt_vals.append(float(price) if price else 0)
                    except:
                        mt_vals.append(0)
                
                # MaterialKindID automatique
                if self.auto_material_kind and 'MaterialKindID' not in mt_cols:
                    family_key = (family_val or default_family_code).upper().strip()
                    mk = family_to_material_kind.get(family_key, '')
                    if not mk:
                        # Chercher dans les filtres famille
                        for f in self.family_filter_ids:
                            if f.material_kind_id and f.qdv_family_code and f.qdv_family_code.upper() == family_key:
                                mk = f.material_kind_id
                                break
                    if mk:
                        mt_cols.append('MaterialKindID')
                        mt_vals.append(mk)
                
                cur_qdv.execute("INSERT INTO ColumnsDataMT (" + ",".join(mt_cols) + ") VALUES (" + ",".join(["?"] * len(mt_vals)) + ")", mt_vals)
                created += 1
        
        # Obsolètes
        actual_obsolete = potential_obsolete - refs_reconciled
        for ref in actual_obsolete:
            row_id = qdv_articles[ref]['row_id']
            if self.auto_delete_obsolete:
                cur_qdv.execute("DELETE FROM ColumnsDataMT WHERE IDInArticles=?", (row_id,))
                cur_qdv.execute("DELETE FROM Articles WHERE RowID=?", (row_id,))
            else:
                cur_qdv.execute("UPDATE Articles SET UserDefinedField=? WHERE RowID=?", (self.obsolete_text or 'Obsolète', row_id))
        
        conn_qdv.commit()
        conn_qdv.close()
        
        return {
            'total_odoo': len(odoo_data), 'total_qdv': len(qdv_articles),
            'updated': updated, 'created': created, 'reconciled': reconciled, 'obsolete': len(actual_obsolete)
        }

    def _update_qdv_article(self, cur_qdv, row_id, data, map_art, map_mt, user_field, family_mapping, family_to_material_kind):
        """Met à jour un article QDV existant"""
        if map_art:
            upd, vals = [], []
            for col, m in map_art.items():
                if m.is_key:
                    continue
                v = self._get_mapping_value(m, data, user_field, family_mapping, cur_qdv)
                if v is not None:
                    upd.append(col + "=?")
                    vals.append(v)
            if upd:
                vals.append(row_id)
                cur_qdv.execute("UPDATE Articles SET " + ",".join(upd) + " WHERE RowID=?", vals)
        
        if map_mt:
            upd, vals = [], []
            for col, m in map_mt.items():
                v = self._get_mapping_value(m, data, user_field, family_mapping, cur_qdv)
                upd.append(col + "=?")
                vals.append(v if v is not None else (0 if col in ('CostPerUnitMT', 'Rebate') else ''))
            if upd:
                cur_qdv.execute("UPDATE ColumnsDataMT SET " + ",".join(upd) + " WHERE IDInArticles=?", vals + [row_id])
                if cur_qdv.rowcount == 0:
                    cur_qdv.execute("INSERT INTO ColumnsDataMT (IDInArticles," + ",".join([col + "=?" for col in map_mt.keys()]).replace("=?", "") + ") VALUES (?" + ",?" * len(vals) + ")", [row_id] + vals)

    def _get_mapping_value(self, mapping, data, user_field, family_mapping, cur_qdv):
        """Retourne la valeur selon le mapping"""
        from datetime import datetime
        
        if mapping.value_source == 'static':
            return mapping.static_value or ''
        if mapping.value_source == 'template' or mapping.odoo_field in ('_template', '_user_field_template'):
            return user_field
        if mapping.odoo_field == '_date_now':
            return datetime.now().strftime("%Y-%m-%d")
        if mapping.convert_family_to_code:
            return self._get_qdv_family_code(data, family_mapping, cur_qdv)
        if mapping.odoo_field:
            return data.get(mapping.odoo_field, '')
        return ''

    def _get_or_create_family(self, cur_qdv, name):
        cur_qdv.execute("SELECT FamilyValue FROM TreeTable WHERE FamilyText=?", (name,))
        r = cur_qdv.fetchone()
        if r:
            return r[0]
        for i in range(1, 100):
            code = 'Z' + str(i)
            cur_qdv.execute("SELECT COUNT(*) FROM TreeTable WHERE FamilyValue=?", (code,))
            if cur_qdv.fetchone()[0] == 0:
                cur_qdv.execute("INSERT INTO TreeTable (FamilyValue, FamilyText) VALUES (?,?)", (code, name))
                return code
        return 'Z99'
