# -*- coding: utf-8 -*-
import zipfile
import io
import logging
from xml.etree import ElementTree as ET
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

NS = {'x': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}


def col_index_from_ref(ref):
    """Convertit une référence de colonne Excel (A→0, B→1, AA→26...)"""
    letters = ''.join(filter(str.isalpha, ref))
    idx = 0
    for ch in letters:
        idx = idx * 26 + (ord(ch.upper()) - ord('A') + 1)
    return idx - 1


def parse_shared_strings(z2):
    shared = []
    if 'xl/sharedStrings.xml' in z2.namelist():
        root = ET.fromstring(z2.read('xl/sharedStrings.xml'))
        for si in root.findall('x:si', NS):
            t = si.find('x:t', NS)
            if t is not None:
                shared.append(t.text or '')
            else:
                texts = [
                    r.find('x:t', NS).text or ''
                    for r in si.findall('x:r', NS)
                    if r.find('x:t', NS) is not None
                ]
                shared.append(''.join(texts))
    return shared


def get_cell_value(c, shared):
    t = c.get('t', '')
    v_elem = c.find('x:v', NS)
    v = v_elem.text if v_elem is not None else None
    if t == 's' and v is not None:
        idx = int(v)
        return shared[idx] if idx < len(shared) else ''
    return v or ''


# Mapping FR / EN des en-têtes QDV7
HEADER_MAP = {
    'Quantité': 'quantite',         'Quantity': 'quantite',
    'Description': 'description',
    'Référence': 'reference',       'Reference': 'reference',
    'Famille': 'famille',           'Family': 'famille',
    'Fabricant': 'fabricant',       'Manufacturer': 'fabricant',
    'Champ utilisateur': 'champ_utilisateur',
    'User-defined field': 'champ_utilisateur',
    'Chemin de la base :': 'chemin_base',
    'Base source': 'base_source',   'Source database': 'base_source',
    "Profondeur d'ouvrage": 'profondeur', '*Set depth': 'profondeur',
    "ID d'ouvrage": 'id_ouvrage',   '*Set ID': 'id_ouvrage',
    'Toujours importer (Y/N)': 'toujours_importer',
    'Always Import\n(Y/N)': 'toujours_importer',
    'Gras (Y/N)': 'gras',           'Bold\n (Y/N)': 'gras',
    'Italique (Y/N)': 'italique',   'Italic\n(Y/N)': 'italique',
    'Soulignement (Y/N)': 'souligne', 'Underline\n(Y/N)': 'souligne',
    'Couleur': 'couleur',           'Color': 'couleur',
}


def parse_minutes_from_blob(blob):
    """
    Extrait les lignes minutes (articles) d'un ouvrage QDV7.
    Le BLOB SetImage = ZIP → MyName → XLSX (feuille 'Articles' = sheet1).
    Retourne une liste de dicts normalisés.
    """
    if not blob:
        return []
    try:
        z1 = zipfile.ZipFile(io.BytesIO(bytes(blob)))
        myname_data = z1.read('MyName')
        z2 = zipfile.ZipFile(io.BytesIO(myname_data))
    except Exception as e:
        _logger.warning('parse_minutes_from_blob: impossible d\'ouvrir le BLOB: %s', e)
        return []

    shared = parse_shared_strings(z2)

    if 'xl/worksheets/sheet1.xml' not in z2.namelist():
        return []

    try:
        root1 = ET.fromstring(z2.read('xl/worksheets/sheet1.xml'))
    except Exception as e:
        _logger.warning('parse_minutes_from_blob: erreur XML: %s', e)
        return []

    sheetdata = root1.find('.//x:sheetData', NS)
    if sheetdata is None:
        return []

    all_rows = sheetdata.findall('x:row', NS)
    if not all_rows:
        return []

    # Ligne 1 = en-têtes (position ordinale implicite sans attribut 'r')
    headers = {}
    pos = 0
    for c in all_rows[0].findall('x:c', NS):
        r = c.get('r')
        if r:
            pos = col_index_from_ref(r)
        headers[pos] = get_cell_value(c, shared)
        pos += 1

    # Mapping position → clé normalisée
    col_map = {p: HEADER_MAP[name] for p, name in headers.items() if name in HEADER_MAP}

    # Lignes de données (skip ligne 1 en-têtes + ligne 2 cachée)
    minutes = []
    for row_elem in all_rows[2:]:
        if row_elem.get('hidden', '0') == '1':
            continue

        cells = {}
        pos = 0
        for c in row_elem.findall('x:c', NS):
            r = c.get('r')
            if r:
                pos = col_index_from_ref(r)
            cells[pos] = get_cell_value(c, shared)
            pos += 1

        m = {v: '' for v in HEADER_MAP.values()}
        for col_pos, key in col_map.items():
            m[key] = cells.get(col_pos, '')

        if not m.get('description') and not m.get('reference'):
            continue

        try:
            m['quantite'] = float(m['quantite']) if m['quantite'] else 1.0
        except (ValueError, TypeError):
            m['quantite'] = 1.0

        minutes.append(m)

    return minutes


class QdvOuvrageMinute(models.Model):
    """
    Une ligne de minute (article ou temps de pose) dans un ouvrage QDV7.
    Correspond à une ligne de la feuille 'Articles' dans le XLSX embarqué.
    """
    _name = 'qdv.ouvrage.minute'
    _description = 'Minute d\'ouvrage QDV7'
    _rec_name = 'description'
    _order = 'ouvrage_id, sequence'

    ouvrage_id = fields.Many2one(
        'qdv.ouvrage', string='Ouvrage',
        required=True, ondelete='cascade', index=True,
    )
    base_id = fields.Many2one(
        'qdv.ouvrage.base', string='Base',
        related='ouvrage_id.base_id', store=True, readonly=True,
    )
    sequence = fields.Integer(string='N°', default=10)

    # ── Données QDV7 ──────────────────────────────────────────────────────
    quantite = fields.Float(string='Qté', digits=(12, 3), default=1.0)
    description = fields.Char(string='Description', required=True)
    reference = fields.Char(string='Référence')
    famille = fields.Char(string='Famille')
    fabricant = fields.Char(string='Fabricant')
    champ_utilisateur = fields.Char(string='Champ utilisateur')
    chemin_base = fields.Char(string='Chemin base', readonly=True)
    base_source = fields.Char(string='Base source QDV')
    profondeur = fields.Char(string='Profondeur')
    id_ouvrage_qdv = fields.Char(string='ID ouvrage QDV')
    toujours_importer = fields.Boolean(string='Toujours importer')
    gras = fields.Boolean(string='Gras')
    italique = fields.Boolean(string='Italique')
    souligne = fields.Boolean(string='Souligné')
    couleur = fields.Char(string='Couleur')

    # ── Type de ligne ─────────────────────────────────────────────────────
    type_ligne = fields.Selection([
        ('materiel', '🔩 Matériel'),
        ('main_oeuvre', '👷 Main d\'œuvre'),
        ('autre', '📄 Autre'),
    ], string='Type', compute='_compute_type_ligne', store=True)

    # ── Suivi modifications ───────────────────────────────────────────────
    is_modified = fields.Boolean(string='Modifié', default=False, copy=False)
    is_new = fields.Boolean(string='Nouveau', default=False, copy=False)

    @api.depends('base_source', 'reference', 'description')
    def _compute_type_ligne(self):
        for rec in self:
            src = (rec.base_source or '').upper()
            ref = (rec.reference or '').upper()
            desc = (rec.description or '').upper()
            if 'POSE' in src or 'TEMPS' in src or ref.startswith('MO') or 'POSE' in desc:
                rec.type_ligne = 'main_oeuvre'
            elif src or rec.reference:
                rec.type_ligne = 'materiel'
            else:
                rec.type_ligne = 'autre'

    def write(self, vals):
        """Marque automatiquement comme modifié - SANS récursion sur l'ouvrage parent"""
        # CORRECTION BUG #3 : skip_modification_tracking évite la boucle
        if not self.env.context.get('skip_modification_tracking'):
            tracked = {'quantite', 'description', 'reference', 'famille',
                       'fabricant', 'champ_utilisateur', 'base_source'}
            if tracked & set(vals.keys()):
                vals['is_modified'] = True
                # Propager à l'ouvrage avec le contexte de skip
                ouvrages = self.mapped('ouvrage_id')
                if ouvrages:
                    ouvrages.with_context(skip_modification_tracking=True).write({
                        'is_modified': True,
                    })
        return super().write(vals)
