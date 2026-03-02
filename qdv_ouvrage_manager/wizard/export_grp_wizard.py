# -*- coding: utf-8 -*-
import base64
import json
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class QdvExportGrpWizard(models.TransientModel):
    """Wizard d'export JSON des modifications vers QDV7"""
    _name = 'qdv.export.grp.wizard'
    _description = 'Export modifications vers QDV7'

    base_id = fields.Many2one(
        'qdv.ouvrage.base',
        string='Base d\'ouvrage',
        required=True
    )
    export_mode = fields.Selection([
        ('modified', 'Ouvrages modifiés uniquement'),
        ('all', 'Tous les ouvrages'),
    ], string='Périmètre export', default='modified', required=True)

    # Résultats
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('done', 'Terminé'),
    ], default='draft')

    result_log = fields.Text(string='Résultats', readonly=True)
    export_count = fields.Integer(string='Ouvrages exportés', readonly=True)

    # Fichier JSON généré
    json_file = fields.Binary(string='Fichier JSON', readonly=True)
    json_filename = fields.Char(string='Nom du fichier', readonly=True)

    def action_export(self):
        """Génère le fichier JSON d'export pour QDV7"""
        self.ensure_one()
        base = self.base_id

        # Sélectionner les ouvrages
        if self.export_mode == 'modified':
            ouvrages = base.ouvrage_ids.filtered(lambda o: o.is_modified)
        else:
            ouvrages = base.ouvrage_ids

        if not ouvrages:
            raise UserError(_('Aucun ouvrage à exporter avec les critères sélectionnés.'))

        # Construire le JSON
        export_data = {
            'qdv_ouvrage_export': {
                'version': '1.0',
                'source': 'Odoo 18 - QDV Ouvrage Manager',
                'base_name': base.name,
                'export_date': fields.Datetime.now().isoformat(),
                'export_mode': self.export_mode,
                'file_version': base.file_version,
                'count': len(ouvrages),
            },
            'ouvrages': [],
            'familles': [],
        }

        # Ouvrages
        for ouvrage in ouvrages.sorted('qdv_row_id'):
            ouvrage_data = {
                'RowID': ouvrage.qdv_row_id,
                'Description': ouvrage.description or '',
                'Reference': ouvrage.reference or '',
                'Family': ouvrage.famille_code or '',
                'Manufacturer': ouvrage.manufacturer or '',
                'UserDefinedField': ouvrage.user_defined_field or '',
                'Unit': ouvrage.unit or 'U',
                'ForcedSellingPricePerUnit': ouvrage.forced_selling_price or 0.0,
                'TakeForcedSellingPrice': 1 if ouvrage.take_forced_price else 0,
                'LockTheGroup': 1 if ouvrage.lock_the_group else 0,
                'ArticleDate': ouvrage.article_date or 0.0,
                'AlterDate': ouvrage.alter_date or 0.0,
                'LastUserInformation': ouvrage.last_user_information or '',
                '_odoo_modified': ouvrage.is_modified,
                '_odoo_modify_date': ouvrage.odoo_modify_date.isoformat() if ouvrage.odoo_modify_date else None,
            }
            export_data['ouvrages'].append(ouvrage_data)

        # Familles (toujours exportées en totalité pour reconstruire l'arborescence)
        if self.export_mode == 'all':
            for famille in base.famille_ids.sorted('code'):
                export_data['familles'].append({
                    'RowID': famille.qdv_row_id,
                    'FamilyValue': famille.code,
                    'FamilyText': '{FR}' + famille.name,
                })

        # Sérialiser en JSON
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        json_bytes = json_str.encode('utf-8')
        json_b64 = base64.b64encode(json_bytes)

        filename = f'qdv_ouvrages_{base.name.replace(" ", "_")}_{fields.Date.today()}.json'

        log_lines = [
            f'✅ Export réussi',
            f'  📦 {len(ouvrages)} ouvrages exportés',
            f'  📁 Fichier : {filename}',
            f'\n💡 Instructions QDV7 :',
            f'  1. Ouvrez votre base d\'ouvrage dans QDV7',
            f'  2. Utilisez le macro VB.NET pour importer ce JSON',
            f'  3. Les ouvrages seront mis à jour selon le RowID',
        ]

        # Marquer comme exportés
        ouvrages.write({'is_modified': False})
        base.write({
            'state': 'exported',
            'date_export': fields.Datetime.now(),
        })

        self.write({
            'state': 'done',
            'result_log': '\n'.join(log_lines),
            'export_count': len(ouvrages),
            'json_file': json_b64,
            'json_filename': filename,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'qdv.export.grp.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
