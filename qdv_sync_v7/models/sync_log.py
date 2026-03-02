# -*- coding: utf-8 -*-
from odoo import models, fields, api


class QdvSyncLog(models.Model):
    _name = 'qdv.sync.log'
    _description = 'Log Sync QDV'
    _order = 'sync_start desc'

    supplier_id = fields.Many2one('qdv.supplier', ondelete='cascade')
    log_type = fields.Selection([
        ('sql', 'SQL Server'),
        ('qdv', 'MAJ Prix QDV'),
        ('qdv_full', 'Sync Complète QDV'),
    ], default='sql')
    sync_start = fields.Datetime()
    sync_end = fields.Datetime()
    duration = fields.Float(string='Durée (sec)')
    records_processed = fields.Integer(default=0)
    records_created = fields.Integer(default=0)
    records_updated = fields.Integer(default=0)
    records_errors = fields.Integer(default=0, string='Supprimés/Erreurs')
    status = fields.Selection([('running', 'En cours'), ('success', 'OK'), ('error', 'Erreur')], default='running')
    error_message = fields.Text()
