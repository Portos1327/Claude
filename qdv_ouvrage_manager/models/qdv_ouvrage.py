# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import os
import sqlite3
from datetime import datetime

_logger = logging.getLogger(__name__)


class QdvOuvrage(models.Model):
    """Ouvrage QDV7 - correspond à la table Groups dans le fichier .grp"""
    _name = 'qdv.ouvrage'
    _description = 'Ouvrage QDV7'
    _order = 'famille_code, reference'
    _rec_name = 'description'

    # === Référence à la base ===
    base_id = fields.Many2one(
        'qdv.ouvrage.base',
        string='Base d\'ouvrage',
        required=True,
        ondelete='cascade',
        index=True
    )

    # === Champs QDV7 natifs (table Groups) ===
    qdv_row_id = fields.Integer(
        string='ID QDV (RowID)',
        help='RowID d\'origine dans la table Groups du fichier .grp',
        readonly=True,
        index=True
    )
    description = fields.Char(
        string='Description',
        required=True,
        help='Libellé de l\'ouvrage (ex: Fourniture, pose et raccordement d\'un câble R2V 5G10)'
    )
    reference = fields.Char(
        string='Référence',
        help='Code référence unique de l\'ouvrage dans QDV7 (ex: R2V5G10)'
    )
    famille_code = fields.Char(
        string='Code famille',
        help='Code de la famille dans l\'arborescence QDV7 (ex: Ab11)'
    )
    famille_id = fields.Many2one(
        'qdv.ouvrage.famille',
        string='Famille',
        compute='_compute_famille_id',
        store=True,
        help='Famille liée (calculée depuis le code famille)'
    )
    famille_libelle = fields.Char(
        string='Libellé famille',
        related='famille_id.name',
        readonly=True
    )
    manufacturer = fields.Char(
        string='Fabricant',
        help='Fabricant principal de l\'ouvrage'
    )
    user_defined_field = fields.Char(
        string='Champ utilisateur',
        help='Champ libre QDV7'
    )
    unit = fields.Char(
        string='Unité',
        default='U',
        help='Unité de l\'ouvrage (U, ML, M, etc.)'
    )
    forced_selling_price = fields.Float(
        string='PV forcé (€)',
        digits=(16, 4),
        help='Prix de vente forcé par unité dans QDV7'
    )
    take_forced_price = fields.Boolean(
        string='Utiliser PV forcé',
        help='Si coché, QDV7 utilisera le prix de vente forcé'
    )
    lock_the_group = fields.Boolean(
        string='Ouvrage verrouillé',
        help='Ouvrage verrouillé dans QDV7 (non modifiable)'
    )
    article_date = fields.Float(
        string='Date article (QDV)',
        help='Date interne QDV7 (format OLE Automation Date)'
    )
    alter_date = fields.Float(
        string='Date modification (QDV)',
        help='Date de modification interne QDV7'
    )
    last_user_information = fields.Char(
        string='Dernier utilisateur (QDV)',
        readonly=True
    )

    # === Champs Odoo ===
    is_modified = fields.Boolean(
        string='Modifié dans Odoo',
        default=False,
        help='Indique que cet ouvrage a été modifié dans Odoo depuis le dernier import/export'
    )
    odoo_modify_date = fields.Datetime(
        string='Date modif. Odoo',
        readonly=True,
        help='Date de la dernière modification dans Odoo'
    )
    odoo_modify_uid = fields.Many2one(
        'res.users',
        string='Modifié par',
        readonly=True
    )
    notes_odoo = fields.Text(
        string='Notes Odoo',
        help='Notes internes Odoo (non synchronisées vers QDV7)'
    )
    active = fields.Boolean(default=True)

    # === Contraintes ===
    @api.constrains('reference', 'base_id')
    def _check_reference_unique(self):
        for rec in self:
            if rec.reference:
                domain = [
                    ('base_id', '=', rec.base_id.id),
                    ('reference', '=', rec.reference),
                    ('id', '!=', rec.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(
                        _('La référence "%s" existe déjà dans cette base d\'ouvrage.') % rec.reference
                    )

    @api.depends('famille_code', 'base_id')
    def _compute_famille_id(self):
        for rec in self:
            if rec.famille_code and rec.base_id:
                famille = self.env['qdv.ouvrage.famille'].search([
                    ('base_id', '=', rec.base_id.id),
                    ('code', '=', rec.famille_code)
                ], limit=1)
                rec.famille_id = famille or False
            else:
                rec.famille_id = False

    def write(self, vals):
        """Override write pour tracer les modifications"""
        # Champs qui déclenchent le marquage 'modifié'
        tracked_fields = {
            'description', 'reference', 'famille_code',
            'manufacturer', 'user_defined_field', 'unit',
            'forced_selling_price', 'take_forced_price', 'lock_the_group'
        }
        if tracked_fields & set(vals.keys()):
            vals['is_modified'] = True
            vals['odoo_modify_date'] = fields.Datetime.now()
            vals['odoo_modify_uid'] = self.env.uid
            # Mettre à jour l'état de la base
            for rec in self:
                if rec.base_id.state == 'imported':
                    rec.base_id.state = 'modified'
        return super().write(vals)

    def action_mark_unmodified(self):
        """Réinitialise le marqueur de modification"""
        self.write({'is_modified': False, 'odoo_modify_date': False, 'odoo_modify_uid': False})

    def _compute_display_name(self):
        for rec in self:
            ref = f'[{rec.reference}] ' if rec.reference else ''
            rec.display_name = f'{ref}{rec.description}'

    _sql_constraints = [
        ('unique_qdv_row_id_base', 'UNIQUE(base_id, qdv_row_id)',
         'Le RowID QDV doit être unique par base d\'ouvrage.'),
    ]

    # === Relations minutes ===
    minute_ids = fields.One2many(
        'qdv.ouvrage.minute',
        'ouvrage_id',
        string='Articles / Minutes',
    )
    minute_count = fields.Integer(
        string='Nb articles',
        compute='_compute_minute_count',
        store=True,
    )
    minute_modified_count = fields.Integer(
        string='Articles modifiés',
        compute='_compute_minute_count',
        store=True,
    )
    has_blob = fields.Boolean(
        string='Contient des minutes',
        default=False,
        readonly=True,
    )

    @api.depends('minute_ids', 'minute_ids.is_modified', 'minute_ids.is_new')
    def _compute_minute_count(self):
        for rec in self:
            rec.minute_count = len(rec.minute_ids)
            rec.minute_modified_count = len(
                rec.minute_ids.filtered(lambda m: m.is_modified or m.is_new)
            )

    def action_view_minutes(self):
        """Ouvre la vue des minutes de l'ouvrage"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Articles — {self.description}',
            'res_model': 'qdv.ouvrage.minute',
            'view_mode': 'list,form',
            'domain': [('ouvrage_id', '=', self.id)],
            'context': {
                'default_ouvrage_id': self.id,
                'default_base_id': self.base_id.id,
            },
        }


    def action_picker_articles(self):
        """Ouvre le wizard de recherche/sélection d'articles depuis les catalogues"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Ajouter des articles — {self.description}',
            'res_model': 'qdv.picker.article.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ouvrage_id': self.id,
            },
        }

    def action_load_minutes(self):
        """
        Charge/recharge les minutes depuis le BLOB SetImage du fichier .grp.
        Lit directement le fichier .grp sur le serveur.
        """
        self.ensure_one()
        fpath = self.base_id.file_path
        if not fpath or not os.path.exists(os.path.normpath(fpath)):
            raise UserError(_(
                'Impossible d\'accéder au fichier .grp :\n%s\n\n'
                'Vérifiez que le fichier est accessible depuis le serveur Odoo.'
            ) % (fpath or 'non configuré'))

        from odoo.addons.qdv_ouvrage_manager.models.qdv_ouvrage_minute import parse_minutes_from_blob

        conn = sqlite3.connect(os.path.normpath(fpath))
        cur = conn.cursor()
        cur.execute(
            'SELECT SetImage FROM Groups WHERE RowID = ?',
            (self.qdv_row_id,)
        )
        row = cur.fetchone()
        conn.close()

        if not row or not row[0]:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Aucune minute'),
                    'message': _('Cet ouvrage ne contient pas de minutes embarquées (SetImage vide).'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

        minutes_data = parse_minutes_from_blob(row[0])

        # Supprimer les minutes existantes non modifiées
        self.minute_ids.filtered(lambda m: not m.is_modified and not m.is_new).unlink()

        # Créer les nouvelles minutes
        vals_list = []
        for i, m in enumerate(minutes_data, 1):
            # Ne pas écraser si une minute modifiée existe déjà sur cette référence
            existing_modified = self.minute_ids.filtered(
                lambda x: x.reference == m.get('reference') and (x.is_modified or x.is_new)
            )
            if existing_modified:
                continue
            vals_list.append({
                'ouvrage_id': self.id,
                'sequence': i * 10,
                'quantite': m.get('quantite', 1.0),
                'description': m.get('description', ''),
                'reference': m.get('reference', ''),
                'famille': m.get('famille', ''),
                'fabricant': m.get('fabricant', ''),
                'champ_utilisateur': m.get('champ_utilisateur', ''),
                'chemin_base': m.get('chemin_base', ''),
                'base_source': m.get('base_source', ''),
                'profondeur': m.get('profondeur', ''),
                'id_ouvrage_qdv': m.get('id_ouvrage', ''),
                'toujours_importer': m.get('toujours_importer', '').upper() == 'Y',
                'gras': m.get('gras', '').upper() == 'Y',
                'italique': m.get('italique', '').upper() == 'Y',
                'souligne': m.get('souligne', '').upper() == 'Y',
                'couleur': m.get('couleur', ''),
                'is_modified': False,
                'is_new': False,
            })

        if vals_list:
            self.env['qdv.ouvrage.minute'].with_context(
                skip_modification_tracking=True
            ).create(vals_list)

        self.has_blob = True
        count = len(self.minute_ids)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('✅ Minutes chargées'),
                'message': _('%d article(s) chargé(s) pour "%s"') % (count, self.description),
                'type': 'success',
                'sticky': False,
            }
        }
