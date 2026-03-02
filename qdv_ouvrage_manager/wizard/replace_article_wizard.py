# -*- coding: utf-8 -*-
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QdvReplaceArticleWizard(models.TransientModel):
    """
    Wizard de remplacement en masse d'un article dans plusieurs ouvrages.

    Permet de rechercher tous les ouvrages contenant un article (par référence
    ou description) et de le remplacer par un autre article en une seule opération.

    Cas d'usage typique : un fabricant change de référence produit → mettre à jour
    tous les ouvrages qui utilisent l'ancienne référence.
    """
    _name = 'qdv.replace.article.wizard'
    _description = 'Remplacement en masse d\'article dans les ouvrages'

    # ── Périmètre de recherche ────────────────────────────────────────────
    base_id = fields.Many2one(
        'qdv.ouvrage.base',
        string='Base d\'ouvrage',
        help='Limiter la recherche à une base spécifique. Laisser vide pour toutes les bases.',
    )

    state = fields.Selection([
        ('search', 'Recherche'),
        ('preview', 'Aperçu'),
        ('done', 'Terminé'),
    ], default='search', readonly=True)

    # ── Critères de recherche de l'article à remplacer ───────────────────
    search_type = fields.Selection([
        ('reference', 'Par référence exacte'),
        ('reference_ilike', 'Par référence (contient)'),
        ('description', 'Par description (contient)'),
        ('fabricant', 'Par fabricant'),
    ], string='Chercher par', default='reference', required=True)

    search_value = fields.Char(
        string='Valeur recherchée',
        required=True,
        help='Valeur à rechercher dans les articles des ouvrages'
    )

    # ── Résultats de la recherche ─────────────────────────────────────────
    found_minute_ids = fields.Many2many(
        'qdv.ouvrage.minute',
        'qdv_replace_wizard_minute_rel',
        'wizard_id', 'minute_id',
        string='Articles trouvés',
        readonly=True,
    )
    found_count = fields.Integer(
        string='Occurrences trouvées',
        compute='_compute_found_count',
    )
    found_ouvrage_count = fields.Integer(
        string='Ouvrages concernés',
        compute='_compute_found_count',
    )

    @api.depends('found_minute_ids')
    def _compute_found_count(self):
        for rec in self:
            rec.found_count = len(rec.found_minute_ids)
            rec.found_ouvrage_count = len(rec.found_minute_ids.mapped('ouvrage_id'))

    # ── Données du nouvel article (remplacement) ──────────────────────────
    replace_mode = fields.Selection([
        ('full', 'Remplacer l\'article complet'),
        ('reference_only', 'Changer la référence uniquement'),
        ('description_only', 'Changer la description uniquement'),
        ('quantite_only', 'Changer la quantité uniquement'),
    ], string='Mode de remplacement', default='full', required=True)

    new_reference = fields.Char(string='Nouvelle référence')
    new_description = fields.Char(string='Nouvelle description')
    new_quantite = fields.Float(
        string='Nouvelle quantité',
        digits=(12, 3),
        default=1.0,
    )
    new_fabricant = fields.Char(string='Nouveau fabricant')
    new_famille = fields.Char(string='Nouvelle famille')
    new_base_source = fields.Char(string='Nouvelle base QDV source')
    new_champ_utilisateur = fields.Char(string='Nouveau champ utilisateur')

    # ── Résultat ──────────────────────────────────────────────────────────
    result_log = fields.Text(string='Résultat', readonly=True)
    replaced_count = fields.Integer(string='Articles remplacés', readonly=True)

    # ── Sélection des ouvrages à traiter ─────────────────────────────────
    select_all = fields.Boolean(
        string='Tout sélectionner / désélectionner',
        default=True,
    )

    @api.onchange('select_all')
    def _onchange_select_all(self):
        if self.found_minute_ids:
            # On ne peut pas modifier directly les Many2many en onchange
            # mais on garde le champ pour l'affichage
            pass

    def action_search(self):
        """Recherche les articles correspondant aux critères"""
        self.ensure_one()

        if not self.search_value or not self.search_value.strip():
            raise UserError(_('Saisissez une valeur de recherche.'))

        val = self.search_value.strip()

        # Construire le domaine
        domain = []
        if self.base_id:
            domain.append(('base_id', '=', self.base_id.id))

        if self.search_type == 'reference':
            domain.append(('reference', '=', val))
        elif self.search_type == 'reference_ilike':
            domain.append(('reference', 'ilike', val))
        elif self.search_type == 'description':
            domain.append(('description', 'ilike', val))
        elif self.search_type == 'fabricant':
            domain.append(('fabricant', 'ilike', val))

        minutes = self.env['qdv.ouvrage.minute'].search(domain, order='ouvrage_id, sequence')

        if not minutes:
            raise UserError(_(
                'Aucun article trouvé pour "%s".\n\n'
                'Vérifiez les critères de recherche ou chargez d\'abord\n'
                'les articles depuis les fichiers .grp.'
            ) % val)

        self.write({
            'found_minute_ids': [(6, 0, minutes.ids)],
            'state': 'preview',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_replace(self):
        """Applique le remplacement sur tous les articles trouvés"""
        self.ensure_one()

        if not self.found_minute_ids:
            raise UserError(_('Aucun article sélectionné.'))

        # Valider les données du nouvel article selon le mode
        if self.replace_mode == 'full':
            if not self.new_reference and not self.new_description:
                raise UserError(_(
                    'En mode "Remplacer l\'article complet", renseignez au minimum\n'
                    'la nouvelle référence ou la nouvelle description.'
                ))
        elif self.replace_mode == 'reference_only' and not self.new_reference:
            raise UserError(_('Saisissez la nouvelle référence.'))
        elif self.replace_mode == 'description_only' and not self.new_description:
            raise UserError(_('Saisissez la nouvelle description.'))
        elif self.replace_mode == 'quantite_only' and self.new_quantite <= 0:
            raise UserError(_('La nouvelle quantité doit être positive.'))

        # Construire les valeurs à écrire
        vals = {}

        if self.replace_mode == 'full':
            if self.new_reference:
                vals['reference'] = self.new_reference
            if self.new_description:
                vals['description'] = self.new_description
            if self.new_fabricant:
                vals['fabricant'] = self.new_fabricant
            if self.new_famille:
                vals['famille'] = self.new_famille
            if self.new_base_source:
                vals['base_source'] = self.new_base_source
            if self.new_champ_utilisateur:
                vals['champ_utilisateur'] = self.new_champ_utilisateur
            if self.new_quantite != 1.0:
                vals['quantite'] = self.new_quantite

        elif self.replace_mode == 'reference_only':
            vals['reference'] = self.new_reference

        elif self.replace_mode == 'description_only':
            vals['description'] = self.new_description

        elif self.replace_mode == 'quantite_only':
            vals['quantite'] = self.new_quantite

        if not vals:
            raise UserError(_('Aucune valeur à remplacer. Renseignez au moins un champ.'))

        # Appliquer le remplacement
        minutes = self.found_minute_ids
        ouvrages_touches = minutes.mapped('ouvrage_id')

        try:
            minutes.write(vals)
        except Exception as e:
            raise UserError(_('Erreur lors du remplacement : %s') % str(e))

        # Construire le log
        log_lines = [
            f'✅ Remplacement effectué avec succès',
            f'',
            f'🔍 Recherche : {self.search_value}',
            f'🔄 Mode : {dict(self._fields["replace_mode"].selection)[self.replace_mode]}',
            f'',
            f'📊 Résultats :',
            f'  • {len(minutes)} article(s) remplacé(s)',
            f'  • dans {len(ouvrages_touches)} ouvrage(s)',
            f'',
            f'📋 Ouvrages modifiés :',
        ]
        for o in ouvrages_touches.sorted('reference'):
            ref = f'[{o.reference}] ' if o.reference else ''
            log_lines.append(f'  • {ref}{o.description}')

        if vals.get('reference'):
            log_lines.append(f'')
            log_lines.append(f'🆕 Nouvelle référence : {vals["reference"]}')
        if vals.get('description'):
            log_lines.append(f'🆕 Nouvelle description : {vals["description"]}')

        self.write({
            'state': 'done',
            'result_log': '\n'.join(log_lines),
            'replaced_count': len(minutes),
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_back_to_search(self):
        """Retour à l'étape de recherche"""
        self.write({'state': 'search', 'found_minute_ids': [(5,)]})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
