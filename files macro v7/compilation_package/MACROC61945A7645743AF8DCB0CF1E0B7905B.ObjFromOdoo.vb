

Public Class GetObjectFromOdoo
    Public Property ErrorGot As String = ""
    
    ' ===== VARIABLES ODOO → QUICKDEVIS (50 champs) =====
    ' Ces variables sont remplies par Odoo et lues par QuickDevis
    
    ' Informations Utilisateur et Opportunité
    Public Property nom_utilisateur_windows As String = ""
    Public Property opportunityName As String = ""
    Public Property oppOwnerEmail As String = ""
    Public Property oppOwnerMobilePhone As String = ""
    Public Property oppOwnerName As String = ""
    Public Property oppOwnerTitle As String = ""
    Public Property lotNumber As String = ""
    Public Property customerReferenceNumber As String = ""
    Public Property currencyIsoCode As String = ""
    Public Property workStartDate As Date
    Public Property workEndDate As Date
    
    ' Organisation (11 champs)
    Public Property orgSfId As String = ""
    Public Property orgAddressLine1 As String = ""
    Public Property orgAddressLine2 As String = ""
    Public Property orgAgencyName As String = ""
    Public Property orgCity As String = ""
    Public Property orgEntityGeoIdentifier As String = ""
    Public Property orgOperationalUnit As String = ""
    Public Property orgPhoneNumber As String = ""
    Public Property orgPostalCode As String = ""
    Public Property orgProfitCenterName As String = ""
    Public Property orgRegion As String = ""
    
    ' Contact Principal (14 champs)
    Public Property primaryContactAccountName As String = ""
    Public Property primaryContactStreet As String = ""
    Public Property primaryContactAddressLine2 As String = ""
    Public Property primaryContactCity As String = ""
    Public Property primaryContactCountry As String = ""
    Public Property primaryContactDepartment As String = ""
    Public Property primaryContactEmail As String = ""
    Public Property primaryContactLastName As String = ""
    Public Property primaryContactMailingCountry As String = ""
    Public Property primaryContactMobilePhone As String = ""
    Public Property primaryContactPostalCode As String = ""
    Public Property primaryContactSalutation As String = ""
    Public Property primaryContactState As String = ""
    Public Property primaryContactTitle As String = ""
    
    ' Contact Secondaire (14 champs)
    Public Property secondaryContactAccountName As String = ""
    Public Property secondaryContactStreet As String = ""
    Public Property secondaryContactAddressLine2 As String = ""
    Public Property secondaryContactCity As String = ""
    Public Property secondaryContactCountry As String = ""
    Public Property secondaryContactDepartment As String = ""
    Public Property secondaryContactEmail As String = ""
    Public Property secondaryContactLastName As String = ""
    Public Property secondaryContactMailingCountry As String = ""
    Public Property secondaryContactMobilePhone As String = ""
    Public Property secondaryContactPostalCode As String = ""
    Public Property secondaryContactSalutation As String = ""
    Public Property secondaryContactState As String = ""
    Public Property secondaryContactTitle As String = ""
    
    ' Champs optionnels pour compatibilité
    Public Property oppId As String = ""
    Public Property opportunityNumber As String = ""
End Class

Public Class SendObjectToOdoo
    ' ===== VARIABLES QUICKDEVIS → ODOO (58 champs) =====
    ' Ces variables sont remplies par QuickDevis et envoyées à Odoo
    
    ' Informations Fichier (3 champs)
    Public Property sys_filepath As String = ""
    Public Property sys_filename As String = ""
    Public Property sys_version_num As String = ""
    
    ' Conditions Commerciales (10 champs)
    Public Property vat As String = ""
    Public Property expirationDate As String = ""
    Public Property billingMilestone1 As String = ""
    Public Property billingMilestone2 As String = ""
    Public Property billingMilestone3 As String = ""
    Public Property paymentMethod As String = ""
    Public Property paymentTerm As String = ""
    Public Property warranty As String = ""
    Public Property deliveryMethod As String = ""
    Public Property deliveryTerm As String = ""
    
    ' Prix et Montants (15 champs)
    Public Property totalExclTax As String = ""
    Public Property totalTax As String = ""
    Public Property totalInclTax As String = ""
    Public Property discount As String = ""
    Public Property discountAmount As String = ""
    Public Property margin As String = ""
    Public Property marginRate As String = ""
    Public Property purchasePrice As String = ""
    Public Property sellingPrice As String = ""
    Public Property laborCost As String = ""
    Public Property materialCost As String = ""
    Public Property equipmentCost As String = ""
    Public Property subcontractorCost As String = ""
    Public Property otherCosts As String = ""
    Public Property transportCost As String = ""
    
    ' Quantités et Unités (15 champs)
    Public Property totalHours As String = ""
    Public Property totalDays As String = ""
    Public Property laborHours As String = ""
    Public Property laborQuantity As String = ""
    Public Property materialQuantity As String = ""
    Public Property equipmentQuantity As String = ""
    Public Property surface_m2 As String = ""
    Public Property volume_m3 As String = ""
    Public Property length_m As String = ""
    Public Property length_km As String = ""
    Public Property weight_kg As String = ""
    Public Property weight_t As String = ""
    Public Property linearMeters As String = ""
    Public Property unitCount As String = ""
    Public Property packageCount As String = ""
    
    ' Notes et Documents (15 champs)
    Public Property techNote1 As String = ""
    Public Property techNote2 As String = ""
    Public Property techNote3 As String = ""
    Public Property commercialNote1 As String = ""
    Public Property commercialNote2 As String = ""
    Public Property attachment1 As String = ""
    Public Property attachment2 As String = ""
    Public Property attachment3 As String = ""
    Public Property documentRef1 As String = ""
    Public Property documentRef2 As String = ""
    Public Property comment1 As String = ""
    Public Property comment2 As String = ""
    Public Property internalReference As String = ""
    Public Property externalReference As String = ""
    Public Property projectCode As String = ""
    
    ' Identifiants
    Public Property opportunityNumber As String = ""
    Public Property qdvQuoteId As String = ""
    Public Property quoteVersion As String = ""
    Public Property currencyIsoCode As String = ""
    
    ' Dates
    Public Property workStartDate As String = ""
    Public Property workEndDate As String = ""
    
    ' Anciens champs pour compatibilité
    Public Property commercialProposal As String = ""
    Public Property salesDocument As String = ""
    Public Property technicalOffer As String = ""
    Public Property slipDocument As String = ""
    Public Property totalAmount As String = ""
    Public Property profitCenter As String = ""
    Public Property project As String = ""
    Public Property masterContract As String = ""
    Public Property pricebook2Id As String = ""
    Public Property pricingMethod As String = ""
    Public Property oia As String = ""
    Public Property vosRef As String
End Class

Public Class AnswerFromOdoo
    Public Property status As String
    Public Property message As String
    Public Property opportunity_id As String
    Public Property opportunity_name As String
    Public Property ErrorGot As String
End Class

Public Class OdooConfig
    Public Property odoo_url As String = ""
    Public Property database As String = ""
    Public Property username As String = ""
    Public Property password As String = ""
    Public Property session_id As String = ""
End Class
