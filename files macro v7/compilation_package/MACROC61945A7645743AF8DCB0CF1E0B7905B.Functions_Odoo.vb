Imports System
Imports System.Net
Imports System.Text
Imports System.Web.Script.Serialization
Imports System.Collections.Generic

Module Functions_Odoo
    
    ' ===== CONFIGURATION ODOO =====
    Private Const ODOO_URL As String = "http://localhost:8069"
    Private Const DATABASE As String = "Turquand_QDV"
    Private Const USERNAME As String = "ferrandiz.dimitri@gmail.com"
    Private Const PASSWORD As String = "tx13278645"
    
    Private odooSessionId As String = ""
    
    ' ===== AUTHENTIFICATION ODOO =====
    Public Function AuthenticateOdoo() As Boolean
        Try
            Dim authUrl As String = ODOO_URL & "/web/session/authenticate"
            Dim client As New WebClient()
            client.Headers.Add("Content-Type", "application/json")
            
            ' Créer le JSON d'authentification
            Dim authData As String = "{""jsonrpc"":""2.0"",""params"":{""db"":""" & DATABASE & """,""login"":""" & USERNAME & """,""password"":""" & PASSWORD & """}}"
            
            ' Envoyer la requête
            Dim response As String = client.UploadString(authUrl, authData)
            
            ' Parser la réponse
            Dim jss As New JavaScriptSerializer()
            Dim result As Dictionary(Of String, Object) = jss.Deserialize(Of Dictionary(Of String, Object))(response)
            
            If result.ContainsKey("result") Then
                Dim resultData As Dictionary(Of String, Object) = CType(result("result"), Dictionary(Of String, Object))
                If resultData.ContainsKey("session_id") Then
                    odooSessionId = resultData("session_id").ToString()
                    Return True
                End If
            End If
            
            Return False
            
        Catch ex As Exception
            MsgBox("Erreur d'authentification Odoo: " & ex.Message, MsgBoxStyle.Critical)
            Return False
        End Try
    End Function
    
    ' ===== LECTURE DEPUIS ODOO (50 champs) =====
    Public Function GetOpportunityFromOdoo(opportunityId As Integer) As GetObjectFromOdoo
        Try
            ' S'authentifier si pas encore fait
            If odooSessionId = "" Then
                If Not AuthenticateOdoo() Then
                    Dim errObj As New GetObjectFromOdoo()
                    errObj.ErrorGot = "Erreur d'authentification Odoo"
                    Return errObj
                End If
            End If
            
            ' Préparer la requête de lecture
            Dim readUrl As String = ODOO_URL & "/web/dataset/call_kw"
            Dim client As New WebClient()
            client.Headers.Add("Content-Type", "application/json")
            client.Headers.Add("Cookie", "session_id=" & odooSessionId)
            
            ' Liste des 50 champs à récupérer (Odoo → QuickDevis)
            Dim fields As String = """name"",""qdv_nom_utilisateur_windows"",""qdv_opportunityname""," & _
                                  """qdv_oppowneremail"",""qdv_oppownermobilephone"",""qdv_oppownername""," & _
                                  """qdv_oppownertitle"",""qdv_lotnumber"",""qdv_customerreferencenumber""," & _
                                  """qdv_currencyisocode"",""qdv_workstartdate"",""qdv_workenddate""," & _
                                  """qdv_orgsfid"",""qdv_orgaddressline1"",""qdv_orgaddressline2""," & _
                                  """qdv_orgagencyname"",""qdv_orgcity"",""qdv_orgentitygeoidentifier""," & _
                                  """qdv_orgoperationalunit"",""qdv_orgphonenumber"",""qdv_orgpostalcode""," & _
                                  """qdv_orgprofitcentername"",""qdv_orgregion""," & _
                                  """qdv_primarycontactaccountname"",""qdv_primarycontactstreet""," & _
                                  """qdv_primarycontactaddressline2"",""qdv_primarycontactcity""," & _
                                  """qdv_primarycontactcountry"",""qdv_primarycontactdepartment""," & _
                                  """qdv_primarycontactemail"",""qdv_primarycontactlastname""," & _
                                  """qdv_primarycontactmailingcountry"",""qdv_primarycontactmobilephone""," & _
                                  """qdv_primarycontactpostalcode"",""qdv_primarycontactsalutation""," & _
                                  """qdv_primarycontactstate"",""qdv_primarycontacttitle""," & _
                                  """qdv_secondarycontactaccountname"",""qdv_secondarycontactstreet""," & _
                                  """qdv_secondarycontactaddressline2"",""qdv_secondarycontactcity""," & _
                                  """qdv_secondarycontactcountry"",""qdv_secondarycontactdepartment""," & _
                                  """qdv_secondarycontactemail"",""qdv_secondarycontactlastname""," & _
                                  """qdv_secondarycontactmailingcountry"",""qdv_secondarycontactmobilephone""," & _
                                  """qdv_secondarycontactpostalcode"",""qdv_secondarycontactsalutation""," & _
                                  """qdv_secondarycontactstate"",""qdv_secondarycontacttitle"""
            
            ' Créer le JSON de la requête
            Dim readData As String = "{""jsonrpc"":""2.0"",""params"":{" & _
                                    """model"":""crm.lead""," & _
                                    """method"":""read""," & _
                                    """args"":[[" & opportunityId & "]]," & _
                                    """kwargs"":{""fields"":[" & fields & "]}}}"
            
            ' Envoyer la requête
            Dim response As String = client.UploadString(readUrl, readData)
            
            ' Parser la réponse
            Dim jss As New JavaScriptSerializer()
            Dim result As Dictionary(Of String, Object) = jss.Deserialize(Of Dictionary(Of String, Object))(response)
            
            Dim gotObject As New GetObjectFromOdoo()
            
            If result.ContainsKey("result") Then
                Dim resultArray As Object() = CType(result("result"), Object())
                If resultArray.Length > 0 Then
                    Dim oppData As Dictionary(Of String, Object) = CType(resultArray(0), Dictionary(Of String, Object))
                    
                    ' Mapper les champs Odoo vers l'objet QuickDevis
                    gotObject.nom_utilisateur_windows = GetStringValue(oppData, "qdv_nom_utilisateur_windows")
                    gotObject.opportunityName = GetStringValue(oppData, "qdv_opportunityname")
                    gotObject.oppOwnerEmail = GetStringValue(oppData, "qdv_oppowneremail")
                    gotObject.oppOwnerMobilePhone = GetStringValue(oppData, "qdv_oppownermobilephone")
                    gotObject.oppOwnerName = GetStringValue(oppData, "qdv_oppownername")
                    gotObject.oppOwnerTitle = GetStringValue(oppData, "qdv_oppownertitle")
                    gotObject.lotNumber = GetStringValue(oppData, "qdv_lotnumber")
                    gotObject.customerReferenceNumber = GetStringValue(oppData, "qdv_customerreferencenumber")
                    gotObject.currencyIsoCode = GetStringValue(oppData, "qdv_currencyisocode")
                    gotObject.workStartDate = GetDateValue(oppData, "qdv_workstartdate")
                    gotObject.workEndDate = GetDateValue(oppData, "qdv_workenddate")
                    
                    ' Organisation
                    gotObject.orgSfId = GetStringValue(oppData, "qdv_orgsfid")
                    gotObject.orgAddressLine1 = GetStringValue(oppData, "qdv_orgaddressline1")
                    gotObject.orgAddressLine2 = GetStringValue(oppData, "qdv_orgaddressline2")
                    gotObject.orgAgencyName = GetStringValue(oppData, "qdv_orgagencyname")
                    gotObject.orgCity = GetStringValue(oppData, "qdv_orgcity")
                    gotObject.orgEntityGeoIdentifier = GetStringValue(oppData, "qdv_orgentitygeoidentifier")
                    gotObject.orgOperationalUnit = GetStringValue(oppData, "qdv_orgoperationalunit")
                    gotObject.orgPhoneNumber = GetStringValue(oppData, "qdv_orgphonenumber")
                    gotObject.orgPostalCode = GetStringValue(oppData, "qdv_orgpostalcode")
                    gotObject.orgProfitCenterName = GetStringValue(oppData, "qdv_orgprofitcentername")
                    gotObject.orgRegion = GetStringValue(oppData, "qdv_orgregion")
                    
                    ' Contact Principal
                    gotObject.primaryContactAccountName = GetStringValue(oppData, "qdv_primarycontactaccountname")
                    gotObject.primaryContactStreet = GetStringValue(oppData, "qdv_primarycontactstreet")
                    gotObject.primaryContactAddressLine2 = GetStringValue(oppData, "qdv_primarycontactaddressline2")
                    gotObject.primaryContactCity = GetStringValue(oppData, "qdv_primarycontactcity")
                    gotObject.primaryContactCountry = GetStringValue(oppData, "qdv_primarycontactcountry")
                    gotObject.primaryContactDepartment = GetStringValue(oppData, "qdv_primarycontactdepartment")
                    gotObject.primaryContactEmail = GetStringValue(oppData, "qdv_primarycontactemail")
                    gotObject.primaryContactLastName = GetStringValue(oppData, "qdv_primarycontactlastname")
                    gotObject.primaryContactMailingCountry = GetStringValue(oppData, "qdv_primarycontactmailingcountry")
                    gotObject.primaryContactMobilePhone = GetStringValue(oppData, "qdv_primarycontactmobilephone")
                    gotObject.primaryContactPostalCode = GetStringValue(oppData, "qdv_primarycontactpostalcode")
                    gotObject.primaryContactSalutation = GetStringValue(oppData, "qdv_primarycontactsalutation")
                    gotObject.primaryContactState = GetStringValue(oppData, "qdv_primarycontactstate")
                    gotObject.primaryContactTitle = GetStringValue(oppData, "qdv_primarycontacttitle")
                    
                    ' Contact Secondaire
                    gotObject.secondaryContactAccountName = GetStringValue(oppData, "qdv_secondarycontactaccountname")
                    gotObject.secondaryContactStreet = GetStringValue(oppData, "qdv_secondarycontactstreet")
                    gotObject.secondaryContactAddressLine2 = GetStringValue(oppData, "qdv_secondarycontactaddressline2")
                    gotObject.secondaryContactCity = GetStringValue(oppData, "qdv_secondarycontactcity")
                    gotObject.secondaryContactCountry = GetStringValue(oppData, "qdv_secondarycontactcountry")
                    gotObject.secondaryContactDepartment = GetStringValue(oppData, "qdv_secondarycontactdepartment")
                    gotObject.secondaryContactEmail = GetStringValue(oppData, "qdv_secondarycontactemail")
                    gotObject.secondaryContactLastName = GetStringValue(oppData, "qdv_secondarycontactlastname")
                    gotObject.secondaryContactMailingCountry = GetStringValue(oppData, "qdv_secondarycontactmailingcountry")
                    gotObject.secondaryContactMobilePhone = GetStringValue(oppData, "qdv_secondarycontactmobilephone")
                    gotObject.secondaryContactPostalCode = GetStringValue(oppData, "qdv_secondarycontactpostalcode")
                    gotObject.secondaryContactSalutation = GetStringValue(oppData, "qdv_secondarycontactsalutation")
                    gotObject.secondaryContactState = GetStringValue(oppData, "qdv_secondarycontactstate")
                    gotObject.secondaryContactTitle = GetStringValue(oppData, "qdv_secondarycontacttitle")
                    
                    Return gotObject
                End If
            End If
            
            gotObject.ErrorGot = "Opportunité introuvable"
            Return gotObject
            
        Catch ex As Exception
            Dim errObj As New GetObjectFromOdoo()
            errObj.ErrorGot = "Erreur lecture Odoo: " & ex.Message
            Return errObj
        End Try
    End Function
    
    ' ===== ÉCRITURE VERS ODOO (58 champs) =====
    Public Function SendQuoteToOdoo(opportunityId As Integer, quoteData As SendObjectToOdoo) As AnswerFromOdoo
        Try
            ' S'authentifier si pas encore fait
            If odooSessionId = "" Then
                If Not AuthenticateOdoo() Then
                    Dim errAnswer As New AnswerFromOdoo()
                    errAnswer.ErrorGot = "Erreur d'authentification Odoo"
                    errAnswer.status = "error"
                    Return errAnswer
                End If
            End If
            
            ' Préparer la requête d'écriture
            Dim writeUrl As String = ODOO_URL & "/web/dataset/call_kw"
            Dim client As New WebClient()
            client.Headers.Add("Content-Type", "application/json")
            client.Headers.Add("Cookie", "session_id=" & odooSessionId)
            
            ' Préparer les valeurs (58 champs QuickDevis → Odoo)
            Dim values As New Dictionary(Of String, String)
            
            ' Informations Fichier
            values.Add("qdv_sys_filepath", quoteData.sys_filepath)
            values.Add("qdv_sys_filename", quoteData.sys_filename)
            values.Add("qdv_sys_version_num", quoteData.sys_version_num)
            
            ' Conditions Commerciales
            values.Add("qdv_vat", quoteData.vat)
            values.Add("qdv_expirationdate", quoteData.expirationDate)
            values.Add("qdv_billingmilestone1", quoteData.billingMilestone1)
            values.Add("qdv_billingmilestone2", quoteData.billingMilestone2)
            values.Add("qdv_billingmilestone3", quoteData.billingMilestone3)
            values.Add("qdv_paymentmethod", quoteData.paymentMethod)
            values.Add("qdv_paymentterm", quoteData.paymentTerm)
            values.Add("qdv_warranty", quoteData.warranty)
            values.Add("qdv_deliverymethod", quoteData.deliveryMethod)
            values.Add("qdv_deliveryterm", quoteData.deliveryTerm)
            
            ' Prix et Montants
            values.Add("qdv_totalexcltax", quoteData.totalExclTax)
            values.Add("qdv_totaltax", quoteData.totalTax)
            values.Add("qdv_totalincltax", quoteData.totalInclTax)
            values.Add("qdv_discount", quoteData.discount)
            values.Add("qdv_discountamount", quoteData.discountAmount)
            values.Add("qdv_margin", quoteData.margin)
            values.Add("qdv_marginrate", quoteData.marginRate)
            values.Add("qdv_purchaseprice", quoteData.purchasePrice)
            values.Add("qdv_sellingprice", quoteData.sellingPrice)
            values.Add("qdv_laborcost", quoteData.laborCost)
            values.Add("qdv_materialcost", quoteData.materialCost)
            values.Add("qdv_equipmentcost", quoteData.equipmentCost)
            values.Add("qdv_subcontractorcost", quoteData.subcontractorCost)
            values.Add("qdv_othercosts", quoteData.otherCosts)
            values.Add("qdv_transportcost", quoteData.transportCost)
            
            ' Quantités
            values.Add("qdv_totalhours", quoteData.totalHours)
            values.Add("qdv_totaldays", quoteData.totalDays)
            values.Add("qdv_laborhours", quoteData.laborHours)
            values.Add("qdv_laborquantity", quoteData.laborQuantity)
            values.Add("qdv_materialquantity", quoteData.materialQuantity)
            values.Add("qdv_equipmentquantity", quoteData.equipmentQuantity)
            values.Add("qdv_surface_m2", quoteData.surface_m2)
            values.Add("qdv_volume_m3", quoteData.volume_m3)
            values.Add("qdv_length_m", quoteData.length_m)
            values.Add("qdv_length_km", quoteData.length_km)
            values.Add("qdv_weight_kg", quoteData.weight_kg)
            values.Add("qdv_weight_t", quoteData.weight_t)
            values.Add("qdv_linearmeters", quoteData.linearMeters)
            values.Add("qdv_unitcount", quoteData.unitCount)
            values.Add("qdv_packagecount", quoteData.packageCount)
            
            ' Notes et Documents
            values.Add("qdv_technote1", quoteData.techNote1)
            values.Add("qdv_technote2", quoteData.techNote2)
            values.Add("qdv_technote3", quoteData.techNote3)
            values.Add("qdv_commercialnote1", quoteData.commercialNote1)
            values.Add("qdv_commercialnote2", quoteData.commercialNote2)
            values.Add("qdv_attachment1", quoteData.attachment1)
            values.Add("qdv_attachment2", quoteData.attachment2)
            values.Add("qdv_attachment3", quoteData.attachment3)
            values.Add("qdv_documentref1", quoteData.documentRef1)
            values.Add("qdv_documentref2", quoteData.documentRef2)
            values.Add("qdv_comment1", quoteData.comment1)
            values.Add("qdv_comment2", quoteData.comment2)
            values.Add("qdv_internalreference", quoteData.internalReference)
            values.Add("qdv_externalreference", quoteData.externalReference)
            values.Add("qdv_projectcode", quoteData.projectCode)
            
            ' Convertir en JSON
            Dim jss As New JavaScriptSerializer()
            Dim valuesJson As String = jss.Serialize(values)
            
            ' Créer le JSON de la requête
            Dim writeData As String = "{""jsonrpc"":""2.0"",""params"":{" & _
                                     """model"":""crm.lead""," & _
                                     """method"":""write""," & _
                                     """args"":[[" & opportunityId & "]," & valuesJson & "]," & _
                                     """kwargs"":{}}}"
            
            ' Envoyer la requête
            Dim response As String = client.UploadString(writeUrl, writeData)
            
            ' Parser la réponse
            Dim result As Dictionary(Of String, Object) = jss.Deserialize(Of Dictionary(Of String, Object))(response)
            
            Dim answer As New AnswerFromOdoo()
            
            If result.ContainsKey("result") AndAlso CBool(result("result")) Then
                answer.status = "success"
                answer.message = "Devis envoyé à Odoo avec succès"
                answer.opportunity_id = opportunityId.ToString()
                Return answer
            Else
                answer.status = "error"
                answer.ErrorGot = "Erreur lors de l'écriture dans Odoo"
                Return answer
            End If
            
        Catch ex As Exception
            Dim errAnswer As New AnswerFromOdoo()
            errAnswer.ErrorGot = "Erreur écriture Odoo: " & ex.Message
            errAnswer.status = "error"
            Return errAnswer
        End Try
    End Function
    
    ' ===== FONCTIONS UTILITAIRES =====
    Private Function GetStringValue(data As Dictionary(Of String, Object), key As String) As String
        If data.ContainsKey(key) AndAlso data(key) IsNot Nothing AndAlso data(key) IsNot DBNull.Value Then
            Return data(key).ToString()
        End If
        Return ""
    End Function
    
    Private Function GetDateValue(data As Dictionary(Of String, Object), key As String) As Date
        Try
            If data.ContainsKey(key) AndAlso data(key) IsNot Nothing AndAlso data(key) IsNot DBNull.Value Then
                Return Convert.ToDateTime(data(key).ToString())
            End If
        Catch
        End Try
        Return Convert.ToDateTime("01/01/1900")
    End Function
    
End Module
