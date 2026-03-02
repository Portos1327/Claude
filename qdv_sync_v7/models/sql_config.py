# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

try:
    import pyodbc
    PYODBC_AVAILABLE = True
except ImportError:
    PYODBC_AVAILABLE = False


class QdvSqlConfig(models.Model):
    """Configuration SQL Server (singleton)"""
    _name = 'qdv.sql.config'
    _description = 'Configuration SQL Server'

    name = fields.Char(default='Configuration SQL Server', required=True)
    sql_server = fields.Char(string='Serveur', default='localhost\\SQL_QDV', required=True)
    sql_database = fields.Char(string='Base de données', default='Odoo_QDV', required=True)
    sql_user = fields.Char(string='Utilisateur', default='odoo_sync')
    sql_password = fields.Char(string='Mot de passe', default='OdooQDV2025!')
    sql_use_windows_auth = fields.Boolean(string='Auth Windows', default=False)
    sql_driver = fields.Selection([('17', 'ODBC Driver 17'), ('18', 'ODBC Driver 18')], string='Driver', default='18', required=True)
    
    pyodbc_installed = fields.Boolean(compute='_compute_pyodbc')
    pyodbc_drivers = fields.Char(compute='_compute_pyodbc')
    connection_status = fields.Char(string='Statut', readonly=True)

    def _compute_pyodbc(self):
        for r in self:
            r.pyodbc_installed = PYODBC_AVAILABLE
            if PYODBC_AVAILABLE:
                r.pyodbc_drivers = ', '.join(pyodbc.drivers())
            else:
                r.pyodbc_drivers = 'Non installé'

    def _get_connection_string(self):
        drv = 'ODBC Driver ' + str(self.sql_driver) + ' for SQL Server'
        if self.sql_use_windows_auth:
            cs = "DRIVER={" + drv + "};SERVER=" + str(self.sql_server) + ";DATABASE=" + str(self.sql_database) + ";Trusted_Connection=yes;"
        else:
            cs = "DRIVER={" + drv + "};SERVER=" + str(self.sql_server) + ";DATABASE=" + str(self.sql_database) + ";UID=" + str(self.sql_user) + ";PWD=" + str(self.sql_password) + ";"
        if self.sql_driver == '18':
            cs = cs + "TrustServerCertificate=yes;"
        return cs

    def action_test_connection(self):
        self.ensure_one()
        if not PYODBC_AVAILABLE:
            raise UserError("pyodbc non installé!")
        try:
            conn = pyodbc.connect(self._get_connection_string(), timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT @@VERSION")
            version = str(cur.fetchone()[0])[:50]
            conn.close()
            self.connection_status = "OK - " + version
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': 'Connexion OK!', 'message': version, 'type': 'success', 'sticky': False}}
        except Exception as e:
            self.connection_status = "Erreur: " + str(e)[:100]
            raise UserError(str(e))

    def action_create_database(self):
        """Créer la base de données si elle n'existe pas"""
        self.ensure_one()
        if not PYODBC_AVAILABLE:
            raise UserError("pyodbc non installé!")
        
        try:
            # Connexion à master
            drv = 'ODBC Driver ' + str(self.sql_driver) + ' for SQL Server'
            cs = "DRIVER={" + drv + "};SERVER=" + str(self.sql_server) + ";DATABASE=master;UID=" + str(self.sql_user) + ";PWD=" + str(self.sql_password) + ";TrustServerCertificate=yes;"
            conn = pyodbc.connect(cs, timeout=10, autocommit=True)
            cur = conn.cursor()
            
            # Créer la base si elle n'existe pas
            db_name = str(self.sql_database)
            cur.execute("IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = ?) CREATE DATABASE [" + db_name + "]", (db_name,))
            conn.close()
            
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': 'Base créée!', 'message': db_name, 'type': 'success', 'sticky': False}}
        except Exception as e:
            raise UserError(str(e))

    def action_list_tables(self):
        """Liste les tables de la base de données"""
        self.ensure_one()
        if not PYODBC_AVAILABLE:
            raise UserError("pyodbc non installé!")
        try:
            conn = pyodbc.connect(self._get_connection_string(), timeout=5)
            cur = conn.cursor()
            cur.execute("SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE' ORDER BY TABLE_SCHEMA, TABLE_NAME")
            tables = []
            for row in cur.fetchall():
                tables.append(str(row[0]) + "." + str(row[1]))
            conn.close()
            
            msg = "Tables trouvées:\n" + "\n".join(tables) if tables else "Aucune table"
            
            return {'type': 'ir.actions.client', 'tag': 'display_notification',
                    'params': {'title': 'Tables dans ' + str(self.sql_database), 'message': msg, 'type': 'info', 'sticky': True}}
        except Exception as e:
            raise UserError(str(e))

    @api.model
    def get_config(self):
        """Retourne la configuration (singleton)"""
        config = self.search([], limit=1)
        return config if config else None
