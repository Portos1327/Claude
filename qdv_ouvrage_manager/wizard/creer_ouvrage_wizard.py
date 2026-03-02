# -*- coding: utf-8 -*-
"""
Wizard de création d'ouvrage de zéro.

Les lignes de composition pointent vers des articles existants dans les bases QDV
(qdv_tarifs_manager ou qdv_sync). Le champ base_source de chaque ligne doit
contenir le nom exact du fichier .qdb — QDV7 s'en sert pour récupérer les prix
lors de l'utilisation de l'ouvrage dans un devis.
"""
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QdvCreerOuvrageWizard(models.TransientModel):
    _name = 'qdv.creer.ouvrage.wizard'
    _description = "Création d'un ouvrage QDV de zéro"

    state = fields.Selection([
        ('metadonnees', 'Identification'),
        ('composition', 'Composition'),
        ('done', 'Créé'),
    ], default='metadonnees', readonly=True)

    # ── Base de destination ──────────────────────────────────────────────
    base_id = fields.Many2one('qdv.ouvrage.base', string='Base destination', required=True)

    # ── Identification ───────────────────────────────────────────────────
    reference   = fields.Char(string='Référence', required=True)
    description = fields.Char(string='Désignation', required=True)
    famille_code = fields.Char(string='Code famille')
    unit         = fields.Char(string='Unité', default='ENS')
    manufacturer = fields.Char(string='Fabricant')

    # Prix
    forced_selling_price = fields.Float(string='Prix de vente forcé', digits=(12, 4))
    take_forced_price    = fields.Boolean(string='Appliquer prix forcé', default=False)
    lock_the_group       = fields.Boolean(string='Verrouiller l\'ouvrage', default=False)

    # ── Composition ──────────────────────────────────────────────────────
    ligne_ids = fields.One2many('qdv.creer.ouvrage.ligne', 'wizard_id', string='Lignes')

    # ── Résultat ─────────────────────────────────────────────────────────
    result_log = fields.Text(readonly=True)

    # ── Navigation ──────────────────────────────────────────────────────
    def action_etape_composition(self):
        self.ensure_one()
        # Vérifier unicité référence dans la base
        existing = self.env['qdv.ouvrage'].search([
            ('base_id', '=', self.base_id.id),
            ('reference', '=', self.reference),
        ], limit=1)
        if existing:
            raise UserError(_(
                "La référence \"%s\" existe déjà dans la base \"%s\"."
            ) % (self.reference, self.base_id.name))

        self.state = 'composition'
        return self._reload()

    def action_retour_metadonnees(self):
        self.state = 'metadonnees'
        return self._reload()

    # ── Création ────────────────────────────────────────────────────────
    def action_creer_ouvrage(self):
        self.ensure_one()

        base = self.base_id
        if not base:
            raise UserError(_("Sélectionnez une base de destination."))

        # Calculer le prochain RowID disponible
        max_row = max(
            (o.row_id for o in self.env['qdv.ouvrage'].search([('base_id', '=', base.id)])),
            default=0
        )
        new_row_id = max(max_row + 1, 99001)

        # Créer l'ouvrage
        ouvrage = self.env['qdv.ouvrage'].create({
            'base_id':     base.id,
            'row_id':      new_row_id,
            'reference':   self.reference,
            'description': self.description,
            'famille':     self.famille_code or '',
            'unit':        self.unit or 'ENS',
            'manufacturer': self.manufacturer or '',
            'forced_selling_price': self.forced_selling_price,
            'take_forced_price':    self.take_forced_price,
            'lock_the_group':       self.lock_the_group,
            'is_modified': True,
            'is_new':      True,
        })

        # Créer les minutes
        log_lines = [
            "✅ Ouvrage \"%s\" créé dans \"%s\"" % (self.reference, base.name),
            "",
        ]
        seq = 10
        for ligne in self.ligne_ids:
            self.env['qdv.ouvrage.minute'].create({
                'ouvrage_id':  ouvrage.id,
                'sequence':    seq,
                'quantite':    ligne.quantite,
                'description': ligne.description or '',
                'reference':   ligne.reference or '',
                'famille':     ligne.famille or '',
                'fabricant':   ligne.fabricant or '',
                'base_source': ligne.base_source or '',   # ← NOM EXACT DU .qdb
                'is_new':      True,
            })
            ref_str = "[%s] " % ligne.reference if ligne.reference else ""
            log_lines.append("  • %.3g × %s%s  📁 %s" % (
                ligne.quantite, ref_str, ligne.description, ligne.base_source or '?'))
            seq += 10

        base.write({'state': 'modified'})

        self.write({'state': 'done', 'result_log': '\n'.join(log_lines)})
        return self._reload()

    def _reload(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class QdvCreerOuvrageLigne(models.TransientModel):
    """Ligne de composition d'un nouvel ouvrage."""
    _name = 'qdv.creer.ouvrage.ligne'
    _description = 'Ligne de composition ouvrage'
    _order = 'sequence'

    wizard_id = fields.Many2one('qdv.creer.ouvrage.wizard', ondelete='cascade')
    sequence  = fields.Integer(default=10)

    type_ligne = fields.Selection([
        ('materiel',    'Matériel'),
        ('main_oeuvre', 'Main d\'œuvre'),
        ('autre',       'Autre'),
    ], string='Type', default='materiel')

    quantite    = fields.Float(string='Qté', digits=(12, 3), default=1.0)
    description = fields.Char(string='Description')
    reference   = fields.Char(string='Référence')
    famille     = fields.Char(string='Famille')
    fabricant   = fields.Char(string='Fabricant')

    # Champ crucial — nom exact du .qdb que QDV7 utilisera pour retrouver les prix
    base_source = fields.Char(
        string='Base source (.qdb)',
        help='Nom exact du fichier .qdb (ex: LEG [2026.02.02 - 0000002].qdb).\n'
             'QDV7 s\'en sert pour récupérer les prix lors de l\'utilisation dans un devis.'
    )
