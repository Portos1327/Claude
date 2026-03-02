# -*- coding: utf-8 -*-
"""
QDV Sync - Rapport de prévisualisation
Affiche les données qui seront envoyées vers QDV avant la synchronisation.
Format : Champ Odoo → Colonne QDV | Valeur
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class QdvSyncPreviewLine(models.TransientModel):
    """Une ligne du rapport de prévisualisation"""
    _name = 'qdv.sync.preview.line'
    _description = 'Ligne prévisualisation QDV'
    _order = 'reference, sequence'

    preview_id = fields.Many2one('qdv.sync.preview', ondelete='cascade')
    sequence = fields.Integer(default=10)

    # Identifiant de l'article
    reference = fields.Char(string='Référence', readonly=True)

    # Mapping
    odoo_field = fields.Char(string='Champ Odoo', readonly=True)
    qdv_table = fields.Char(string='Table QDV', readonly=True)
    qdv_column = fields.Char(string='Colonne QDV', readonly=True)

    # Valeur calculée
    value = fields.Char(string='Valeur', readonly=True)

    # État
    status = fields.Selection([
        ('ok', 'OK'),
        ('warning', 'Avertissement'),
        ('error', 'Erreur'),
    ], default='ok', readonly=True)
    status_msg = fields.Char(string='Info', readonly=True)


class QdvSyncPreview(models.TransientModel):
    """Wizard de prévisualisation de la synchronisation QDV"""
    _name = 'qdv.sync.preview'
    _description = 'Prévisualisation sync QDV'

    supplier_id = fields.Many2one('qdv.supplier', string='Fournisseur', readonly=True)

    # Options d'affichage
    max_records = fields.Integer(string='Nb articles max', default=10,
        help='Nombre maximum d\'articles à afficher dans le rapport')
    show_all_fields = fields.Boolean(string='Tous les champs', default=True,
        help='Afficher tous les champs du mapping ou uniquement les champs clés')
    filter_reference = fields.Char(string='Filtrer par référence',
        help='Optionnel : saisir une référence partielle pour filtrer les articles prévisualisés')

    # Résultats
    preview_line_ids = fields.One2many('qdv.sync.preview.line', 'preview_id',
        string='Aperçu', readonly=True)

    # Stats
    total_records = fields.Integer(string='Total articles Odoo', readonly=True)
    total_mapped = fields.Integer(string='Champs mappés actifs', readonly=True)
    preview_generated = fields.Boolean(default=False)

    # Rapport HTML pour export
    report_html = fields.Html(string='Rapport', readonly=True, sanitize=False)

    def action_generate_preview(self):
        """Génère le rapport de prévisualisation"""
        self.ensure_one()
        supplier = self.supplier_id
        if not supplier:
            raise UserError(_("Aucun fournisseur sélectionné!"))

        # Récupérer les mappings actifs (direction vers QDV)
        active_mappings = supplier.field_mapping_ids.filtered(
            lambda m: m.active and m.odoo_field and
            m.sync_direction in ('odoo_to_qdv', 'bidirectional')
        )
        if not active_mappings:
            raise UserError(_("Aucun mapping actif avec direction 'Odoo → QDV'!"))

        # Récupérer les données source
        records = supplier._get_source_data()
        if not records:
            raise UserError(_("Aucun enregistrement trouvé avec les filtres actuels!"))

        # Filtrer par référence si demandé
        ref_field = supplier._get_reference_field()
        all_data = []
        for rec in records:
            data = supplier._extract_record_data(rec)
            ref = str(data.get(ref_field, '') or '').strip()
            if not ref:
                continue
            if self.filter_reference:
                if self.filter_reference.upper() not in ref.upper():
                    continue
            all_data.append((ref, data))

        total = len(all_data)
        # Limiter au nombre max demandé
        preview_data = all_data[:self.max_records]

        # Construire les données de mapping
        user_field = supplier._format_template({})
        family_mapping = supplier._build_family_mapping()

        # Supprimer les anciennes lignes
        self.preview_line_ids.unlink()

        lines_to_create = []
        from datetime import datetime

        for ref, data in preview_data:
            seq = 10
            for m in active_mappings:
                # Calculer la valeur
                value = ''
                odoo_field_display = m.odoo_field or ''
                status = 'ok'
                status_msg = ''

                try:
                    if m.value_source == 'static':
                        value = m.static_value or ''
                        odoo_field_display = '[statique]'
                    elif m.value_source == 'template' or m.odoo_field in ('_template', '_user_field_template'):
                        value = user_field
                        odoo_field_display = '[template]'
                    elif m.odoo_field == '_date_now':
                        value = datetime.now().strftime("%Y-%m-%d")
                        odoo_field_display = '[date_now]'
                    elif m.convert_family_to_code:
                        value = supplier._get_qdv_family_code(data, family_mapping, None)
                        odoo_field_display = m.odoo_field + ' → [code famille]'
                        if not value:
                            status = 'warning'
                            status_msg = 'Code famille QDV non trouvé'
                    else:
                        raw = data.get(m.odoo_field, '')
                        value = str(raw) if raw is not None else ''
                        if not value:
                            status = 'warning'
                            status_msg = 'Valeur vide'

                except Exception as e:
                    value = ''
                    status = 'error'
                    status_msg = str(e)[:100]

                lines_to_create.append({
                    'preview_id': self.id,
                    'sequence': seq,
                    'reference': ref,
                    'odoo_field': odoo_field_display,
                    'qdv_table': m.qdv_table or 'articles',
                    'qdv_column': m.qdv_column or '',
                    'value': value[:200] if value else '',
                    'status': status,
                    'status_msg': status_msg,
                })
                seq += 1

        if lines_to_create:
            self.env['qdv.sync.preview.line'].create(lines_to_create)

        # Générer le HTML du rapport
        html = self._build_report_html(preview_data, active_mappings, total)

        self.write({
            'total_records': total,
            'total_mapped': len(active_mappings),
            'preview_generated': True,
            'report_html': html,
        })

        # Recharger la vue
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.sync.preview',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _build_report_html(self, preview_data, active_mappings, total):
        """Construit le rapport HTML de prévisualisation"""
        supplier = self.supplier_id
        user_field = supplier._format_template({})
        family_mapping = supplier._build_family_mapping()
        ref_field = supplier._get_reference_field()
        from datetime import datetime

        # En-tête du rapport
        html = """
<div style="font-family: Arial, sans-serif; font-size: 13px;">
<h3 style="color: #3c3c3c; border-bottom: 2px solid #875a7b; padding-bottom: 6px;">
    📋 Prévisualisation sync QDV — {supplier}
</h3>
<div style="background: #f8f9fa; border-left: 4px solid #875a7b; padding: 8px 12px; margin-bottom: 12px; border-radius: 3px;">
    <b>Fournisseur :</b> {supplier} &nbsp;|&nbsp;
    <b>Modèle source :</b> {model} &nbsp;|&nbsp;
    <b>Total articles :</b> {total} &nbsp;|&nbsp;
    <b>Affichés :</b> {shown} &nbsp;|&nbsp;
    <b>Champs mappés :</b> {nb_map}
</div>
""".format(
            supplier=supplier.name or '',
            model=supplier._source_model_name,
            total=total,
            shown=len(preview_data),
            nb_map=len(active_mappings),
        )

        # En-tête du tableau de mapping (légende)
        html += """
<table style="width:100%; border-collapse: collapse; margin-bottom: 16px;">
<thead>
<tr style="background: #875a7b; color: white;">
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">Référence article</th>
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">Champ Odoo</th>
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">→</th>
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">Table QDV</th>
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">Colonne QDV</th>
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">Valeur envoyée</th>
    <th style="padding: 7px 10px; text-align: left; font-weight: bold;">État</th>
</tr>
</thead>
<tbody>
"""
        row_colors = ['#ffffff', '#f9f9f9']
        row_idx = 0

        for ref, data in preview_data:
            first_row = True
            nb_mappings = len(active_mappings)

            for m in active_mappings:
                # Calculer la valeur
                value = ''
                odoo_field_display = m.odoo_field or ''
                status_icon = '✅'
                status_msg = ''
                value_color = '#1a1a1a'

                try:
                    if m.value_source == 'static':
                        value = m.static_value or ''
                        odoo_field_display = '<i style="color:#666">[valeur statique]</i>'
                    elif m.value_source == 'template' or m.odoo_field in ('_template', '_user_field_template'):
                        value = user_field
                        odoo_field_display = '<i style="color:#666">[template]</i>'
                    elif m.odoo_field == '_date_now':
                        value = datetime.now().strftime("%Y-%m-%d")
                        odoo_field_display = '<i style="color:#666">[date_now]</i>'
                    elif m.convert_family_to_code:
                        value = supplier._get_qdv_family_code(data, family_mapping, None)
                        odoo_field_display = '<b>' + (m.odoo_field or '') + '</b> <i style="color:#875a7b">→ code famille</i>'
                        if not value:
                            status_icon = '⚠️'
                            status_msg = 'Code famille QDV non trouvé'
                            value_color = '#e07800'
                            value = '<i style="color:#e07800">Non trouvé</i>'
                    else:
                        raw = data.get(m.odoo_field, '')
                        value = str(raw) if raw is not None else ''
                        odoo_field_display = '<b>' + (m.odoo_field or '') + '</b>'
                        if not value:
                            status_icon = '⚠️'
                            status_msg = 'Vide'
                            value_color = '#999'
                            value = '<i style="color:#999">—</i>'

                except Exception as e:
                    value = '<i style="color:red">Erreur</i>'
                    status_icon = '❌'
                    status_msg = str(e)[:80]
                    value_color = 'red'

                bg = row_colors[row_idx % 2]
                ref_cell = ''
                if first_row:
                    ref_cell = '<td style="padding: 6px 10px; font-weight: bold; color: #333; vertical-align: top; border-bottom: 1px solid #e0e0e0; border-top: 2px solid #ccc;" rowspan="{}">{}</td>'.format(
                        nb_mappings, ref)
                    first_row = False

                is_key_style = ' font-weight:bold; ' if m.is_key else ''

                html += """<tr style="background: {bg};">
    {ref_cell}
    <td style="padding: 5px 10px; border-bottom: 1px solid #eee; color:#555; {key_style}">{odoo}</td>
    <td style="padding: 5px 10px; border-bottom: 1px solid #eee; color: #875a7b; text-align:center;">→</td>
    <td style="padding: 5px 10px; border-bottom: 1px solid #eee; color:#888; font-size:11px;">{table}</td>
    <td style="padding: 5px 10px; border-bottom: 1px solid #eee; color:#333; font-family:monospace; {key_style}">{col}</td>
    <td style="padding: 5px 10px; border-bottom: 1px solid #eee; color:{val_color}; max-width:250px; overflow:hidden;">{val}</td>
    <td style="padding: 5px 10px; border-bottom: 1px solid #eee; font-size:14px;" title="{msg}">{icon} {msg}</td>
</tr>""".format(
                    bg=bg,
                    ref_cell=ref_cell,
                    odoo=odoo_field_display,
                    table=m.qdv_table or 'articles',
                    col=m.qdv_column or '',
                    val=value if len(str(value)) < 200 else str(value)[:197] + '...',
                    val_color=value_color,
                    icon=status_icon,
                    msg=status_msg,
                    key_style=is_key_style,
                )

            row_idx += 1

        html += "</tbody></table>"

        if total > len(preview_data):
            html += """<div style="text-align:center; color:#666; font-style:italic; padding: 8px;">
... et {} autres articles non affichés (augmentez "Nb articles max" pour en voir plus)
</div>""".format(total - len(preview_data))

        html += """
<div style="margin-top: 12px; background: #e8f5e9; border-left: 4px solid #4caf50; padding: 8px 12px; border-radius: 3px; font-size: 12px;">
    ℹ️ Ce rapport est une prévisualisation. Les valeurs réelles envoyées à QDV seront identiques lors de la sync complète.
    La colonne <b>Référence</b> correspond à la clé de l'article dans QDV.
</div>
</div>
"""
        return html

    def action_export_html(self):
        """Ouvre le rapport dans une nouvelle fenêtre pour impression/export"""
        self.ensure_one()
        if not self.preview_generated:
            return self.action_generate_preview()
        # Retourner une URL pour téléchargement du rapport HTML
        return {
            'type': 'ir.actions.act_url',
            'url': '/qdv_sync/preview/report/%d' % self.id,
            'target': 'new',
        }
