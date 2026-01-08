# -*- coding: utf-8 -*-

import base64
import io
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    _logger.warning("openpyxl n'est pas installé. L'export Excel ne sera pas disponible.")


class ExportQuickdevisWizard(models.TransientModel):
    _name = 'export.quickdevis.wizard'
    _description = 'Assistant d\'export vers QuickDevis 7'

    article_ids = fields.Many2many('rexel.article', string='Articles à exporter')
    
    # Options d'export
    export_all = fields.Boolean(string='Exporter tous les articles', default=False)
    include_obsolete = fields.Boolean(string='Inclure les articles obsolètes', default=False)
    
    # Filtres
    famille_ids = fields.Many2many(
        'rexel.product.family',
        'export_qdv_wizard_famille_rel',
        'wizard_id', 'famille_id',
        string='Familles',
        domain=[('parent_id', '=', False)]
    )
    
    # Résultat
    export_file = fields.Binary(string='Fichier exporté', readonly=True)
    export_filename = fields.Char(string='Nom du fichier', readonly=True)
    state = fields.Selection([
        ('draft', 'Configuration'),
        ('done', 'Terminé')
    ], default='draft')
    articles_exported = fields.Integer(string='Articles exportés', readonly=True)

    @api.model
    def default_get(self, fields_list):
        """Récupère les articles sélectionnés"""
        res = super().default_get(fields_list)
        
        if self.env.context.get('active_ids'):
            res['article_ids'] = [(6, 0, self.env.context.get('active_ids'))]
        
        return res

    def _get_all_subfamilies(self, family_ids):
        """Récupère récursivement toutes les sous-familles"""
        Family = self.env['rexel.product.family']
        all_ids = list(family_ids)
        children = Family.search([('parent_id', 'in', family_ids)])
        if children:
            all_ids.extend(self._get_all_subfamilies(children.ids))
        return all_ids

    def action_export(self):
        """Lance l'export vers QuickDevis 7 avec le nouveau format"""
        self.ensure_one()
        
        if not OPENPYXL_AVAILABLE:
            raise UserError(_("La bibliothèque openpyxl n'est pas installée."))
        
        # Déterminer les articles à exporter
        if self.export_all:
            domain = []
            if not self.include_obsolete:
                domain.append(('is_obsolete', '=', False))
            articles = self.env['rexel.article'].search(domain)
        elif self.article_ids:
            articles = self.article_ids
            if not self.include_obsolete:
                articles = articles.filtered(lambda a: not a.is_obsolete)
        elif self.famille_ids:
            all_family_ids = self._get_all_subfamilies(self.famille_ids.ids)
            domain = [('family_node_id', 'in', all_family_ids)]
            if not self.include_obsolete:
                domain.append(('is_obsolete', '=', False))
            articles = self.env['rexel.article'].search(domain)
        else:
            raise UserError(_("Veuillez sélectionner des articles ou cocher 'Exporter tous les articles'."))
        
        if not articles:
            raise UserError(_('Aucun article à exporter.'))
        
        # Créer le fichier Excel
        excel_data = self._create_quickdevis_excel(articles)
        
        # Préparer le nom du fichier
        filename = f"Export_QuickDevis7_{datetime.now().strftime('%Y-%m-%d')}.xlsx"
        
        # Sauvegarder
        self.write({
            'export_file': base64.b64encode(excel_data),
            'export_filename': filename,
            'state': 'done',
            'articles_exported': len(articles),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.quickdevis.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _create_quickdevis_excel(self, articles):
        """
        Créer le fichier Excel au format QuickDevis 7
        
        Structure:
        - Onglet "Articles Rexel" : données articles avec formule Famille en colonne X
        - Onglet "Structure" : arborescence Famille/Sous-famille pour QDV7
        """
        wb = Workbook()
        
        # ==========================================
        # ONGLET 1 : Articles Rexel
        # ==========================================
        ws_articles = wb.active
        ws_articles.title = "Articles Rexel"
        
        # Définir les colonnes pour l'onglet Articles
        # Colonnes A à W = données, X = formule Famille
        columns_articles = [
            ('A', 'Référence Fabricant', 20),
            ('B', 'Trigramme Fabricant', 15),
            ('C', 'Fabricant', 25),
            ('D', 'Référence Rexel', 20),
            ('E', 'Désignation', 50),
            ('F', 'Prix Base', 12),
            ('G', 'Prix Net', 12),
            ('H', 'Remise %', 10),
            ('I', 'Unité Mesure', 12),
            ('J', 'Conditionnement', 15),
            ('K', 'Code EAN', 15),
            ('L', 'Montant D3E', 12),
            ('M', 'Unité D3E', 10),
            ('N', 'Famille', 30),
            ('O', 'Sous-Famille', 30),
            ('P', 'Fonction', 30),
            ('Q', 'Code Famille', 15),
            ('R', 'Code Sous-Famille', 15),
            ('S', 'Code Fonction', 15),
            ('T', 'Date Tarif', 12),
            ('U', 'Date MAJ API', 12),
            ('V', 'Source', 10),
            ('W', 'Obsolète', 10),
            ('X', 'Famille QDV7', 20),  # Formule =Q&R&S
        ]
        
        # Styles
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='0066CC', end_color='0066CC', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        # Écrire les en-têtes
        for col_letter, col_name, col_width in columns_articles:
            cell = ws_articles[f'{col_letter}1']
            cell.value = col_name
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
            ws_articles.column_dimensions[col_letter].width = col_width
        
        # Figer la première ligne
        ws_articles.freeze_panes = 'A2'
        
        # Collecter les données pour l'onglet Structure
        familles_set = set()  # (code_famille, libelle_famille)
        sous_familles_set = set()  # (code_famille, code_sous_famille, libelle_sous_famille)
        
        # Écrire les données des articles
        row = 2
        for article in articles:
            # Récupérer les infos famille
            data = self._get_article_data(article)
            
            # Collecter pour l'onglet Structure
            if data['famille_code']:
                familles_set.add((data['famille_code'], data['famille_libelle']))
            if data['famille_code'] and data['sous_famille_code']:
                sous_familles_set.add((
                    data['famille_code'],
                    data['sous_famille_code'],
                    data['sous_famille_libelle']
                ))
            
            # Écrire les colonnes A à W
            ws_articles[f'A{row}'] = data['reference_fabricant']
            ws_articles[f'B{row}'] = data['trigramme_fabricant']
            ws_articles[f'C{row}'] = data['fabricant_libelle']
            ws_articles[f'D{row}'] = data['reference_rexel']
            ws_articles[f'E{row}'] = data['designation']
            ws_articles[f'F{row}'] = data['prix_base']
            ws_articles[f'G{row}'] = data['prix_net']
            ws_articles[f'H{row}'] = data['remise']
            ws_articles[f'I{row}'] = data['unite_mesure']
            ws_articles[f'J{row}'] = data['conditionnement']
            ws_articles[f'K{row}'] = data['code_ean13']
            ws_articles[f'L{row}'] = data['montant_d3e']
            ws_articles[f'M{row}'] = data['unite_d3e']
            ws_articles[f'N{row}'] = data['famille_libelle']
            ws_articles[f'O{row}'] = data['sous_famille_libelle']
            ws_articles[f'P{row}'] = data['fonction_libelle']
            ws_articles[f'Q{row}'] = data['famille_code']
            ws_articles[f'R{row}'] = data['sous_famille_code']
            ws_articles[f'S{row}'] = data['fonction_code']
            ws_articles[f'T{row}'] = data['date_tarif']
            ws_articles[f'U{row}'] = data['last_api_update']
            ws_articles[f'V{row}'] = data['import_source']
            ws_articles[f'W{row}'] = data['is_obsolete']
            
            # Colonne X : Formule =Q&R&S (Code Famille + Code Sous-Famille + Code Fonction)
            ws_articles[f'X{row}'] = f'=Q{row}&R{row}&S{row}'
            
            # Appliquer bordures
            for col_letter, _, _ in columns_articles:
                ws_articles[f'{col_letter}{row}'].border = thin_border
            
            row += 1
        
        # ==========================================
        # ONGLET 2 : Structure
        # ==========================================
        ws_structure = wb.create_sheet(title="Structure")
        
        # En-têtes de l'onglet Structure
        structure_columns = [
            ('A', 'Type', 15),
            ('B', 'Libellé', 50),
            ('C', 'Code Structure', 25),
        ]
        
        for col_letter, col_name, col_width in structure_columns:
            cell = ws_structure[f'{col_letter}1']
            cell.value = col_name
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
            cell.border = thin_border
            ws_structure.column_dimensions[col_letter].width = col_width
        
        ws_structure.freeze_panes = 'A2'
        
        # Trier les familles et sous-familles
        familles_sorted = sorted(familles_set, key=lambda x: (x[0] or '', x[1] or ''))
        sous_familles_sorted = sorted(sous_familles_set, key=lambda x: (x[0] or '', x[1] or '', x[2] or ''))
        
        # Écrire les FAMILLES d'abord
        struct_row = 2
        for code_famille, libelle_famille in familles_sorted:
            if libelle_famille:  # Ne pas écrire si vide
                ws_structure[f'A{struct_row}'] = 'Famille'
                ws_structure[f'B{struct_row}'] = libelle_famille
                ws_structure[f'C{struct_row}'] = code_famille or ''
                
                for col_letter, _, _ in structure_columns:
                    ws_structure[f'{col_letter}{struct_row}'].border = thin_border
                
                struct_row += 1
        
        # Écrire les SOUS-FAMILLES ensuite
        for code_famille, code_sous_famille, libelle_sous_famille in sous_familles_sorted:
            if libelle_sous_famille:  # Ne pas écrire si vide
                ws_structure[f'A{struct_row}'] = 'Sous-Famille'
                ws_structure[f'B{struct_row}'] = libelle_sous_famille
                # Code Structure = Code Famille + Code Sous-Famille
                ws_structure[f'C{struct_row}'] = f"{code_famille or ''}{code_sous_famille or ''}"
                
                for col_letter, _, _ in structure_columns:
                    ws_structure[f'{col_letter}{struct_row}'].border = thin_border
                
                struct_row += 1
        
        # Sauvegarder dans un buffer
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        return output.read()

    def _get_article_data(self, article):
        """Prépare les données d'un article pour l'export"""
        # Récupérer les infos famille depuis les champs texte ou la relation
        famille_name = article.famille_libelle or ''
        sous_famille_name = article.sous_famille_libelle or ''
        fonction_name = article.fonction_libelle or ''
        famille_code = article.famille_code or ''
        sous_famille_code = article.sous_famille_code or ''
        fonction_code = article.fonction_code or ''
        
        # Si family_node_id existe, utiliser les infos de la hiérarchie
        if article.family_node_id:
            famille = article.family_node_id
            if famille.level == 'fonction':
                fonction_name = famille.name
                fonction_code = famille.code or ''
                if famille.parent_id:
                    sous_famille_name = famille.parent_id.name
                    sous_famille_code = famille.parent_id.code or ''
                    if famille.parent_id.parent_id:
                        famille_name = famille.parent_id.parent_id.name
                        famille_code = famille.parent_id.parent_id.code or ''
            elif famille.level == 'sous_famille':
                sous_famille_name = famille.name
                sous_famille_code = famille.code or ''
                if famille.parent_id:
                    famille_name = famille.parent_id.name
                    famille_code = famille.parent_id.code or ''
            else:
                famille_name = famille.name
                famille_code = famille.code or ''
        
        return {
            'reference_fabricant': article.reference_fabricant or '',
            'trigramme_fabricant': article.trigramme_fabricant or '',
            'fabricant_libelle': article.fabricant_libelle or '',
            'reference_rexel': article.reference_rexel or '',
            'designation': article.designation or '',
            'prix_base': article.prix_base or 0,
            'prix_net': article.prix_net or 0,
            'remise': article.remise or 0,
            'unite_mesure': article.unite_mesure or 'U',
            'conditionnement': article.conditionnement or '',
            'code_ean13': article.code_ean13 or '',
            'montant_d3e': article.montant_d3e or 0,
            'unite_d3e': article.unite_d3e or 0,
            'famille_libelle': famille_name,
            'sous_famille_libelle': sous_famille_name,
            'fonction_libelle': fonction_name,
            'famille_code': famille_code,
            'sous_famille_code': sous_famille_code,
            'fonction_code': fonction_code,
            'date_tarif': article.date_tarif.strftime('%d/%m/%Y') if article.date_tarif else '',
            'last_api_update': article.last_api_update.strftime('%d/%m/%Y') if article.last_api_update else '',
            'import_source': article.import_source or '',
            'is_obsolete': 'Oui' if article.is_obsolete else 'Non',
        }

    def action_back(self):
        """Retour à la configuration"""
        self.write({'state': 'draft'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.quickdevis.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_download(self):
        """Télécharge le fichier exporté"""
        self.ensure_one()
        
        if not self.export_file:
            raise UserError(_('Aucun fichier à télécharger. Veuillez d\'abord lancer l\'export.'))
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/export.quickdevis.wizard/{self.id}/export_file/{self.export_filename}?download=true',
            'target': 'self',
        }
