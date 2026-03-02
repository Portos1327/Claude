# -*- coding: utf-8 -*-
"""
Picker d'articles QDV.

Sources supportées (modules optionnels) :
  - qdv_tarifs_manager  →  qdv.tarif.article / qdv.tarif.base
  - qdv_sync_v7         →  qdv.supplier (lecture directe .qdb)

Tous les résultats sont normalisés dans qdv.picker.sync.result (modèle local)
pour éviter toute dépendance de vue vers des modèles externes optionnels.
"""
import logging
import os
import sqlite3
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

TARIFS_MODULE = 'qdv.tarif.article'
SYNC_MODULE   = 'qdv.supplier'


class QdvPickerArticleWizard(models.TransientModel):
    _name = 'qdv.picker.article.wizard'
    _description = "Sélection d'articles QDV depuis les bases"

    ouvrage_id = fields.Many2one('qdv.ouvrage', string='Ouvrage cible', required=True)

    state = fields.Selection([
        ('search', 'Recherche'),
        ('select', 'Sélection'),
        ('done',   'Inséré'),
    ], default='search', readonly=True)

    # ── Source ──────────────────────────────────────────────────────────
    source = fields.Selection(
        selection='_get_source_selection',
        string='Source',
    )

    @api.model
    def _get_source_selection(self):
        choices = []

        # Bases tarifs fabricants (qdv_tarifs_manager)
        if TARIFS_MODULE in self.env:
            bases = self.env['qdv.tarif.base'].search(
                [('article_count', '>', 0)], order='manufacturer_code'
            )
            for b in bases:
                label = "🏭 %s — %s" % (b.manufacturer_code, b.manufacturer_name)
                if b.file_name:
                    label += "  [%s]" % b.file_name
                choices.append(("tarif:%d" % b.id, label))

        # Bases personnalisées (qdv_sync_v7)
        if SYNC_MODULE in self.env:
            suppliers = self.env[SYNC_MODULE].search([('active', '=', True)], order='name')
            for s in suppliers:
                qdb = s.qdv_detected_file or '?'
                choices.append(("sync:%d" % s.id, "📋 %s  [%s]" % (s.name, qdb)))

        if not choices:
            choices.append(('none', '⚠️ Aucune base disponible (installez qdv_tarifs_manager ou qdv_sync_v7)'))

        return choices

    # ── Critères ────────────────────────────────────────────────────────
    recherche_texte = fields.Char(string='Référence / désignation')
    filtre_famille  = fields.Char(string='Famille')

    # ── Résultats unifiés (modèle local — pas de dépendance externe) ────
    sync_result_ids = fields.One2many(
        'qdv.picker.sync.result', 'wizard_id',
        string='Résultats', readonly=True,
    )
    result_count = fields.Integer(compute='_compute_result_count')

    @api.depends('sync_result_ids')
    def _compute_result_count(self):
        for r in self:
            r.result_count = len(r.sync_result_ids)

    # ── Sélection ───────────────────────────────────────────────────────
    selection_ids = fields.One2many(
        'qdv.picker.selection.line', 'wizard_id',
        string='Articles à insérer',
    )
    selection_count = fields.Integer(compute='_compute_selection_count')

    @api.depends('selection_ids')
    def _compute_selection_count(self):
        for r in self:
            r.selection_count = len(r.selection_ids)

    inserted_count = fields.Integer(readonly=True)
    result_log     = fields.Text(readonly=True)

    # ── Recherche ───────────────────────────────────────────────────────
    def action_rechercher(self):
        self.ensure_one()
        if not self.source or self.source == 'none':
            raise UserError(_(
                "Sélectionnez une base QDV.\n"
                "Vérifiez que qdv_tarifs_manager ou qdv_sync_v7 est installé."
            ))

        txt = (self.recherche_texte or '').strip()
        fam = (self.filtre_famille or '').strip()
        if not txt and not fam:
            raise UserError(_("Saisissez au moins un critère (référence, désignation ou famille)."))

        # Vider les anciens résultats
        self.sync_result_ids.unlink()

        src_type, src_id = self.source.split(':', 1)
        if src_type == 'tarif':
            self._rechercher_tarif(int(src_id), txt, fam)
        else:
            self._rechercher_sync(int(src_id), txt, fam)

        if not self.sync_result_ids:
            raise UserError(_("Aucun article trouvé pour ces critères."))

        self.state = 'select'
        return self._reload()

    def _rechercher_tarif(self, base_id, txt, fam):
        """
        Recherche dans qdv.tarif.article et normalise dans qdv.picker.sync.result.
        Ainsi la vue n'a pas besoin de connaître qdv.tarif.article.
        """
        if TARIFS_MODULE not in self.env:
            raise UserError(_("Module qdv_tarifs_manager non installé."))

        domain = [('base_id', '=', base_id)]
        if txt:
            domain += ['|', ('reference', 'ilike', txt), ('designation', 'ilike', txt)]
        if fam:
            domain += ['|', '|', '|',
                       ('fam_level1', 'ilike', fam),
                       ('fam_level2', 'ilike', fam),
                       ('fam_level3', 'ilike', fam),
                       ('family_breadcrumb', 'ilike', fam)]

        articles = self.env[TARIFS_MODULE].search(domain, limit=200, order='reference')
        if not articles:
            return

        vals_list = []
        for art in articles:
            qdb = art.base_id.file_name or ''
            vals_list.append({
                'wizard_id':   self.id,
                'supplier_id': 0,           # 0 = source tarif fabricant
                'qdb_filename': qdb,
                'reference':   art.reference or '',
                'designation': art.designation or '',
                'famille':     art.fam_level1 or '',
                'fabricant':   art.manufacturer_name or '',
                'unite':       art.unit or 'U',
                'prix':        art.net_price or 0.0,
            })
        self.env['qdv.picker.sync.result'].create(vals_list)

    def _rechercher_sync(self, supplier_id, txt, fam):
        """Recherche directe dans le fichier .qdb d'un qdv.supplier."""
        if SYNC_MODULE not in self.env:
            raise UserError(_("Module qdv_sync_v7 non installé."))

        supplier = self.env[SYNC_MODULE].browse(supplier_id)
        qdb_path = supplier._find_qdv_file()
        if not qdb_path or not os.path.isfile(qdb_path):
            raise UserError(_(
                "Fichier .qdb introuvable pour \"%s\".\nDossier : %s\nPattern : %s"
            ) % (supplier.name, supplier.qdv_folder, supplier.qdv_pattern))

        where_parts, params = [], []
        if txt:
            where_parts.append('(Reference LIKE ? OR Description LIKE ?)')
            params += ['%%%s%%' % txt, '%%%s%%' % txt]
        if fam:
            where_parts.append('Family LIKE ?')
            params.append('%%%s%%' % fam)
        where_clause = ' AND '.join(where_parts)

        try:
            conn = sqlite3.connect(qdb_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ColumnsDataMT'")
            has_mt = cur.fetchone() is not None
            if has_mt:
                cur.execute("""
                    SELECT a.Reference, a.Description, a.Family,
                           a.Manufacturer, a.Unit,
                           COALESCE(mt.CostPerUnitMT, 0) as prix
                    FROM Articles a
                    LEFT JOIN ColumnsDataMT mt ON mt.IDInArticles = a.RowID
                    WHERE %s ORDER BY a.Reference LIMIT 200
                """ % where_clause, params)
            else:
                cur.execute("""
                    SELECT Reference, Description, Family,
                           Manufacturer, Unit, 0 as prix
                    FROM Articles WHERE %s ORDER BY Reference LIMIT 200
                """ % where_clause, params)
            rows = cur.fetchall()
            conn.close()
        except Exception as e:
            raise UserError(_("Erreur lecture .qdb : %s") % str(e))

        if not rows:
            return

        qdb_filename = os.path.basename(qdb_path)
        vals_list = []
        for row in rows:
            vals_list.append({
                'wizard_id':   self.id,
                'supplier_id': supplier_id,
                'qdb_filename': qdb_filename,
                'reference':   str(row['Reference']    or ''),
                'designation': str(row['Description']  or ''),
                'famille':     str(row['Family']       or ''),
                'fabricant':   str(row['Manufacturer'] or ''),
                'unite':       str(row['Unit']         or 'U'),
                'prix':        float(row['prix'] or 0),
            })
        self.env['qdv.picker.sync.result'].create(vals_list)

    # ── Ajout à la sélection ────────────────────────────────────────────

    def action_vider_selection(self):
        self.selection_ids.unlink()
        return self._reload()

    def action_retour_recherche(self):
        self.sync_result_ids.unlink()
        self.write({'state': 'search'})
        return self._reload()

    # ── Insertion ───────────────────────────────────────────────────────
    def action_inserer(self):
        self.ensure_one()
        if not self.selection_ids:
            raise UserError(_("Sélectionnez au moins un article."))

        ouvrage = self.ouvrage_id
        max_seq = max((m.sequence for m in ouvrage.minute_ids), default=0)

        vals_list = []
        log_lines = ["✅ %d article(s) inséré(s) dans \"%s\"" % (
            len(self.selection_ids), ouvrage.description), ""]

        for line in self.selection_ids:
            max_seq += 10
            vals_list.append({
                'ouvrage_id':  ouvrage.id,
                'sequence':    max_seq,
                'quantite':    line.quantite,
                'description': line.designation,
                'reference':   line.reference,
                'famille':     line.famille,
                'fabricant':   line.fabricant,
                'base_source': line.base_source,  # ← NOM EXACT DU .qdb
                'is_new':      True,
                'is_modified': False,
            })
            log_lines.append("  • %.3g × [%s] %s\n    📁 %s" % (
                line.quantite, line.reference, line.designation, line.base_source))

        self.env['qdv.ouvrage.minute'].create(vals_list)
        ouvrage.write({'is_modified': True})

        self.write({
            'state':          'done',
            'inserted_count': len(vals_list),
            'result_log':     '\n'.join(log_lines),
        })
        return self._reload()

    def _reload(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class QdvPickerSyncResult(models.TransientModel):
    """
    Résultats normalisés de recherche — modèle local uniquement.
    Reçoit les articles depuis qdv.tarif.article (tarifs fabricants)
    ET depuis les .qdb de qdv.supplier (bases personnalisées).
    Le bouton action_ajouter_sync est défini ici car les boutons dans une
    sous-liste One2many s'exécutent sur le modèle de la ligne, pas sur le wizard.
    """
    _name = 'qdv.picker.sync.result'
    _description = 'Résultat recherche article QDV'
    _order = 'famille, reference'

    wizard_id    = fields.Many2one('qdv.picker.article.wizard', ondelete='cascade')
    supplier_id  = fields.Integer(help='ID qdv.supplier, 0 si source tarif fabricant')
    qdb_filename = fields.Char(string='Base .qdb')

    reference   = fields.Char(string='Référence')
    designation = fields.Char(string='Désignation')
    famille     = fields.Char(string='Famille')
    fabricant   = fields.Char(string='Fabricant')
    unite       = fields.Char(string='Unité')
    prix        = fields.Float(string='Prix', digits=(12, 4))

    def action_ajouter_sync(self):
        """
        Ajoute cette ligne à la sélection du wizard parent.
        Méthode sur ce modèle (pas sur le wizard) car les boutons d'une
        sous-liste One2many s'exécutent sur le modèle de la ligne.
        """
        self.ensure_one()
        wizard = self.wizard_id
        if not wizard:
            return

        existing = wizard.selection_ids.filtered(
            lambda l: l.reference == self.reference
                      and l.base_source == self.qdb_filename
        )
        if existing:
            existing[0].quantite += 1
        else:
            if self.supplier_id and 'qdv.supplier' in self.env:
                supplier = self.env['qdv.supplier'].browse(self.supplier_id)
                source_label = supplier.name if supplier.exists() else self.qdb_filename
            else:
                source_label = self.qdb_filename

            self.env['qdv.picker.selection.line'].create({
                'wizard_id':    wizard.id,
                'reference':    self.reference or '',
                'designation':  self.designation or '',
                'famille':      self.famille or '',
                'fabricant':    self.fabricant or '',
                'unite':        self.unite or 'U',
                'prix_net':     self.prix or 0.0,
                'quantite':     1.0,
                'base_source':  self.qdb_filename or '',
                'source_label': source_label or '',
            })

        return wizard._reload()


class QdvPickerSelectionLine(models.TransientModel):
    """Ligne de sélection — article prêt à être inséré dans l'ouvrage."""
    _name = 'qdv.picker.selection.line'
    _description = 'Article sélectionné pour insertion'
    _order = 'sequence'

    wizard_id  = fields.Many2one('qdv.picker.article.wizard', ondelete='cascade')
    sequence   = fields.Integer(default=10)

    quantite    = fields.Float(string='Qté', digits=(12, 3), default=1.0)
    designation = fields.Char(string='Description', required=True)
    reference   = fields.Char(string='Référence')
    famille     = fields.Char(string='Famille')
    fabricant   = fields.Char(string='Fabricant')
    unite       = fields.Char(string='Unité')
    prix_net    = fields.Float(string='Prix net', digits=(12, 4), readonly=True)

    # Champ crucial — nom exact du .qdb que QDV7 utilisera
    base_source  = fields.Char(string='Base source (.qdb)', readonly=True)
    source_label = fields.Char(string='Source', readonly=True)
