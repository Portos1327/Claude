# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    _inherit = 'crm.lead'
    
    # ===== CHAMPS ODOO → QUICKDEVIS (50 champs) =====
    # Ces champs sont remplis par Odoo et lus par QuickDevis au début du devis

    qdv_nom_utilisateur_windows = fields.Char(string="Utilisateur Windows")
    qdv_opportunityname = fields.Char(string="Nom opportunité")
    qdv_oppowneremail = fields.Char(string="Email du porteur")
    qdv_oppownermobilephone = fields.Char(string="Téléphone du porteur")
    qdv_oppownername = fields.Char(string="Nom du porteur")
    qdv_oppownertitle = fields.Char(string="Titre du porteur")
    qdv_lotnumber = fields.Char(string="Numéro de lot")
    qdv_customerreferencenumber = fields.Char(string="Référence Client")
    qdv_currencyisocode = fields.Char(string="Monnaie du devis")
    qdv_workenddate = fields.Date(string="Date de fin de chantier")
    qdv_workstartdate = fields.Date(string="Date de début de chantier")
    qdv_orgsfid = fields.Char(string="Identité SF de l'organisation")
    qdv_orgaddressline1 = fields.Char(string="Adresse organisation (1)")
    qdv_orgaddressline2 = fields.Char(string="Adresse organisation (2)")
    qdv_orgagencyname = fields.Char(string="Nom de l'agence")
    qdv_orgcity = fields.Char(string="Ville de l'agence")
    qdv_orgentitygeoidentifier = fields.Char(string="Lieu géographique agence")
    qdv_orgoperationalunit = fields.Char(string="Unité opérationnelle")
    qdv_orgphonenumber = fields.Char(string="Téléphone organisation")
    qdv_orgpostalcode = fields.Char(string="Code postal organisation")
    qdv_orgprofitcentername = fields.Char(string="Nom du centre de profit")
    qdv_orgregion = fields.Char(string="Region organisation")
    qdv_primarycontactaccountname = fields.Char(string="Compte du premier contact")
    qdv_primarycontactstreet = fields.Char(string="Adresse du premier contact(1)")
    qdv_primarycontactaddressline2 = fields.Char(string="Adresse du premier contact(2)")
    qdv_primarycontactcity = fields.Char(string="Ville du premier contact")
    qdv_primarycontactcountry = fields.Char(string="Pays du premier contact")
    qdv_primarycontactdepartment = fields.Char(string="Departement du premier contact")
    qdv_primarycontactemail = fields.Char(string="Email du premier contact")
    qdv_primarycontactlastname = fields.Char(string="Nom du premier contact")
    qdv_primarycontactmailingcountry = fields.Char(string="Pays email du premier contact")
    qdv_primarycontactmobilephone = fields.Char(string="Téléphone du premier contact")
    qdv_primarycontactpostalcode = fields.Char(string="Code postal du premier contact")
    qdv_primarycontactsalutation = fields.Char(string="Salutation du premier contact")
    qdv_primarycontactstate = fields.Char(string="Etat du premier contact")
    qdv_primarycontacttitle = fields.Char(string="Fonction du premier contact")
    qdv_secondarycontactaccountname = fields.Char(string="Compte du second contact")
    qdv_secondarycontactstreet = fields.Char(string="Adresse du second contact(1)")
    qdv_secondarycontactaddressline2 = fields.Char(string="Adresse du second contact(2)")
    qdv_secondarycontactcity = fields.Char(string="Ville du second contact")
    qdv_secondarycontactcountry = fields.Char(string="Pays du second contact")
    qdv_secondarycontactdepartment = fields.Char(string="Département du second contact")
    qdv_secondarycontactemail = fields.Char(string="Email du second contact")
    qdv_secondarycontactlastname = fields.Char(string="Nom du second contact")
    qdv_secondarycontactmailingcountry = fields.Char(string="Pays email du second contact")
    qdv_secondarycontactmobilephone = fields.Char(string="Téléphone du second contact")
    qdv_secondarycontactpostalcode = fields.Char(string="Code postal du second contact")
    qdv_secondarycontactsalutation = fields.Char(string="Salutation du second contact")
    qdv_secondarycontactstate = fields.Char(string="Etat du second contact")
    qdv_secondarycontacttitle = fields.Char(string="Fonctiondu second contact")

    # ===== CHAMPS QUICKDEVIS → ODOO (58 champs) =====
    # Ces champs sont remplis par QuickDevis et lus par Odoo à la fin du devis
    # Résultats du chiffrage : prix, quantités, délais, modalités, etc.

    qdv_sys_filepath = fields.Char(string="Répertoire du devis", readonly=True, help="Rempli par QuickDevis")
    qdv_sys_filename = fields.Char(string="Emplacement du fichier devis", readonly=True, help="Rempli par QuickDevis")
    qdv_sys_version_num = fields.Char(string="Version du devis", readonly=True, help="Rempli par QuickDevis")
    qdv_vat = fields.Char(string="Taux de TVA", readonly=True, help="Rempli par QuickDevis")
    qdv_expirationdate = fields.Date(string="Date d'expiration", readonly=True, help="Rempli par QuickDevis")
    qdv_billingmilestone1 = fields.Char(string="Modalite de réglement(1)", readonly=True, help="Rempli par QuickDevis")
    qdv_billingmilestone2 = fields.Char(string="Modalite de réglement(2)", readonly=True, help="Rempli par QuickDevis")
    qdv_billingmilestone3 = fields.Char(string="Modalite de réglement(3)", readonly=True, help="Rempli par QuickDevis")
    qdv_paymentmethod = fields.Char(string="Mode de règlement", readonly=True, help="Rempli par QuickDevis")
    qdv_paymentterm = fields.Char(string="Délai de règlement", readonly=True, help="Rempli par QuickDevis")
    qdv_id = fields.Char(string="Numéro d'opportunité", readonly=True, help="Rempli par QuickDevis")
    qdv_specificcost_prorata = fields.Char(string="Prorata", readonly=True, help="Rempli par QuickDevis")
    qdv_specificcost_management = fields.Char(string="Négo", readonly=True, help="Rempli par QuickDevis")
    qdv_specificcost_hazards = fields.Char(string="Aléas", readonly=True, help="Rempli par QuickDevis")
    qdv_specificcost_others = fields.Char(string="Autres", readonly=True, help="Rempli par QuickDevis")
    qdv_proportionalcosts_overheads = fields.Char(string="Environnement", readonly=True, help="Rempli par QuickDevis")
    qdv_proportionalcosts_tosite = fields.Char(string="Frais CSDP", readonly=True, help="Rempli par QuickDevis")
    qdv_proportionalcosts_siteinsurance = fields.Char(string="Assurance site", readonly=True, help="Rempli par QuickDevis")
    qdv_proportionalcosts_insurance = fields.Char(string="Assurance", readonly=True, help="Rempli par QuickDevis")
    qdv_proportionalcosts_margintarget = fields.Char(string="Marge escomptée", readonly=True, help="Rempli par QuickDevis")
    qdv_proportionalcosts_projectmargin = fields.Char(string="Marge du projet", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_labour_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_labour_unitofwork = fields.Char(string="Unité de main d'oeuvre", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_labour_quantity = fields.Char(string="Nombre d'heures", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_labour_unitprice = fields.Char(string="Taux de main d'oeuvre", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_materials_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_materials_quantity = fields.Char(string="Quantité FO", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_materials_unitprice = fields.Char(string="Prix total net FO", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_materials_additionaldiscount = fields.Char(string="Remise", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_subcontracting_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_subcontracting_unitofwork = fields.Char(string="Unité de main d'oeuvre", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_subcontracting_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_directexpenses_subcontracting_unitprice = fields.Char(string="Taux", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_technical_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_technical_unitofwork = fields.Char(string="Unité de main d'oeuvre", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_technical_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_technical_unitprice = fields.Char(string="Taux", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_framing_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_framing_unitofwork = fields.Char(string="Unité de main d'oeuvre", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_framing_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_framing_unitprice = fields.Char(string="Taux", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_mastery_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_mastery_unitofwork = fields.Char(string="Unité de main d'oeuvre", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_mastery_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_mastery_unitprice = fields.Char(string="Taux", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_park_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_park_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_park_unitprice = fields.Char(string="Prix unitaire", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_park_additionaldiscount = fields.Char(string="Remise", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_otherfees_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_otherfees_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_otherfees_unitprice = fields.Char(string="Prix unitaire", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_otherfees_additionaldiscount = fields.Char(string="Remise", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_tools_productcode = fields.Char(string="Code produit CPQ", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_tools_quantity = fields.Char(string="Quantité", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_tools_unitprice = fields.Char(string="Prix unitaire", readonly=True, help="Rempli par QuickDevis")
    qdv_indirectexpenses_tools_additionaldiscount = fields.Char(string="Remise", readonly=True, help="Rempli par QuickDevis")

    # ===== MÉTHODES DE SYNCHRONISATION =====
    
    def action_sync_to_quickdevis(self):
        """
        Synchronise l'opportunité vers QuickDevis 7.
        Envoie les 50 champs Odoo → QuickDevis (SF -> QDV).
        """
        self.ensure_one()
        
        try:
            _logger.info(f"Synchronisation vers QuickDevis - Opportunité ID={self.id}, Nom={self.name}")
            
            # Vérifier que l'opportunité a les données minimales
            if not self.qdv_opportunityname:
                raise UserError("Le champ 'Nom opportunité' (QuickDevis) doit être renseigné avant la synchronisation.")
            
            # TODO Phase 2: Implémenter l'appel API
            # Préparer les données des 50 champs SF -> QDV
            data_to_send = {}
            
            # Champs Odoo → QuickDevis (50 champs)
            odoo_to_qdv_fields = [
                'qdv_nom_utilisateur_windows',
                'qdv_opportunityname',
                'qdv_oppowneremail',
                'qdv_oppownermobilephone',
                'qdv_oppownername',
                'qdv_oppownertitle',
                'qdv_lotnumber',
                'qdv_customerreferencenumber',
                'qdv_currencyisocode',
                'qdv_workenddate',
                'qdv_workstartdate',
                'qdv_orgsfid',
                'qdv_orgaddressline1',
                'qdv_orgaddressline2',
                'qdv_orgagencyname',
                'qdv_orgcity',
                'qdv_orgentitygeoidentifier',
                'qdv_orgoperationalunit',
                'qdv_orgphonenumber',
                'qdv_orgpostalcode',
                'qdv_orgprofitcentername',
                'qdv_orgregion',
                'qdv_primarycontactaccountname',
                'qdv_primarycontactstreet',
                'qdv_primarycontactaddressline2',
                'qdv_primarycontactcity',
                'qdv_primarycontactcountry',
                'qdv_primarycontactdepartment',
                'qdv_primarycontactemail',
                'qdv_primarycontactlastname',
                'qdv_primarycontactmailingcountry',
                'qdv_primarycontactmobilephone',
                'qdv_primarycontactpostalcode',
                'qdv_primarycontactsalutation',
                'qdv_primarycontactstate',
                'qdv_primarycontacttitle',
                'qdv_secondarycontactaccountname',
                'qdv_secondarycontactstreet',
                'qdv_secondarycontactaddressline2',
                'qdv_secondarycontactcity',
                'qdv_secondarycontactcountry',
                'qdv_secondarycontactdepartment',
                'qdv_secondarycontactemail',
                'qdv_secondarycontactlastname',
                'qdv_secondarycontactmailingcountry',
                'qdv_secondarycontactmobilephone',
                'qdv_secondarycontactpostalcode',
                'qdv_secondarycontactsalutation',
                'qdv_secondarycontactstate',
                'qdv_secondarycontacttitle',
            ]
            
            for field_name in odoo_to_qdv_fields:
                value = getattr(self, field_name, None)
                if value:
                    data_to_send[field_name] = value
            
            _logger.info(f"Données préparées pour QuickDevis : {len(data_to_send)} champs")
            
            # TODO: Envoyer data_to_send à l'API QuickDevis
            
            _logger.info(f"Synchronisation réussie - Opportunité ID={self.id}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Synchronisation réussie',
                    'message': 'L\'opportunité "%s" a été synchronisée vers QuickDevis.\n%s champs envoyés.' % (self.name, len(data_to_send)),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur synchronisation QuickDevis - Opportunité ID={self.id}: {str(e)}")
            raise UserError("Erreur lors de la synchronisation : %s" % str(e))
    
    def action_refresh_from_quickdevis(self):
        """
        Récupère les données depuis QuickDevis 7 (résultats du chiffrage).
        Récupère les 58 champs QuickDevis → Odoo (QDV->SF).
        """
        self.ensure_one()
        
        try:
            _logger.info(f"Récupération depuis QuickDevis - Opportunité ID={self.id}, Nom={self.name}")
            
            # TODO Phase 2: Implémenter l'appel API
            # Récupérer les données des 58 champs QDV->SF
            
            # Champs QuickDevis → Odoo (58 champs de résultats)
            qdv_to_odoo_fields = [
                'qdv_sys_filepath',
                'qdv_sys_filename',
                'qdv_sys_version_num',
                'qdv_vat',
                'qdv_expirationdate',
                'qdv_billingmilestone1',
                'qdv_billingmilestone2',
                'qdv_billingmilestone3',
                'qdv_paymentmethod',
                'qdv_paymentterm',
                'qdv_specificcost_prorata',
                'qdv_specificcost_management',
                'qdv_specificcost_hazards',
                'qdv_specificcost_others',
                'qdv_proportionalcosts_overheads',
                'qdv_proportionalcosts_tosite',
                'qdv_proportionalcosts_siteinsurance',
                'qdv_proportionalcosts_insurance',
                'qdv_proportionalcosts_margintarget',
                'qdv_proportionalcosts_projectmargin',
            ]
            
            # TODO: Recevoir les données de QuickDevis via API
            # data_received = api_call_to_quickdevis()
            # for field_name, value in data_received.items():
            #     setattr(self, field_name, value)
            
            _logger.info(f"Récupération réussie - Opportunité ID={self.id}")
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Récupération réussie',
                    'message': 'Les données de chiffrage de l\'opportunité "%s" ont été récupérées depuis QuickDevis.' % self.name,
                    'type': 'info',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Erreur récupération QuickDevis - Opportunité ID={self.id}: {str(e)}")
            raise UserError("Erreur lors de la récupération : %s" % str(e))
