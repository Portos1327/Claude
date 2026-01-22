Imports System
Imports System.Net
Imports System.Text
Imports System.Collections.Generic
Imports System.Text.RegularExpressions

Module Functions_Odoo
    
    ' ===== CONFIGURATION ODOO =====
    Private Const ODOO_URL As String = "http://localhost:8069"
    Private Const DATABASE As String = "Turquand_QDV"
    Private Const USERNAME As String = "ferrandiz.dimitri@gmail.com"
    Private Const PASSWORD As String = "tx13278645"
    
    Private odooSessionId As String = ""
    Private cookies As String = ""
    
    ' ===== FONCTION UTILITAIRE : EXTRAIRE VALEUR JSON =====
    Private Function ExtractJsonValue(json As String, key As String) As String
        Try
            ' Chercher "key":"value" ou "key":value
            Dim pattern As String = """" & key & """\s*:\s*""([^""]*)""|""" & key & """\s*:\s*([^,}]*)"
            Dim match As Match = Regex.Match(json, pattern)
            
            If match.Success Then
                If match.Groups(1).Success Then
                    Return match.Groups(1).Value
                ElseIf match.Groups(2).Success Then
                    Return match.Groups(2).Value.Trim()
                End If
            End If
            
            Return ""
        Catch ex As Exception
            Return ""
        End Try
    End Function
    
    ' ===== FONCTION UTILITAIRE : CRÉER JSON SIMPLE =====
    Private Function CreateJsonString(pairs As Dictionary(Of String, String)) As String
        Dim sb As New StringBuilder()
        sb.Append("{")
        
        Dim first As Boolean = True
        For Each kvp In pairs
            If Not first Then sb.Append(",")
            sb.Append("""" & kvp.Key & """:""" & kvp.Value & """")
            first = False
        Next
        
        sb.Append("}")
        Return sb.ToString()
    End Function
    
    ' ===== AUTHENTIFICATION ODOO =====
    Public Function AuthenticateOdoo() As Boolean
        Try
            Dim authUrl As String = ODOO_URL & "/web/session/authenticate"
            
            ' Créer la requête HTTP
            Dim request As HttpWebRequest = CType(WebRequest.Create(authUrl), HttpWebRequest)
            request.Method = "POST"
            request.ContentType = "application/json"
            request.CookieContainer = New CookieContainer()
            
            ' Créer le JSON d'authentification (manuellement)
            Dim authData As String = "{""jsonrpc"":""2.0"",""params"":{""db"":""" & DATABASE & """,""login"":""" & USERNAME & """,""password"":""" & PASSWORD & """}}"
            
            ' Envoyer la requête
            Dim dataBytes As Byte() = Encoding.UTF8.GetBytes(authData)
            request.ContentLength = dataBytes.Length
            
            Using stream As IO.Stream = request.GetRequestStream()
                stream.Write(dataBytes, 0, dataBytes.Length)
            End Using
            
            ' Lire la réponse
            Using response As HttpWebResponse = CType(request.GetResponse(), HttpWebResponse)
                Using reader As New IO.StreamReader(response.GetResponseStream())
                    Dim responseText As String = reader.ReadToEnd()
                    
                    ' Extraire session_id
                    odooSessionId = ExtractJsonValue(responseText, "session_id")
                    
                    ' Sauvegarder les cookies
                    If response.Cookies IsNot Nothing AndAlso response.Cookies.Count > 0 Then
                        cookies = response.Headers("Set-Cookie")
                    End If
                    
                    If Not String.IsNullOrEmpty(odooSessionId) Then
                        Return True
                    End If
                End Using
            End Using
            
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
            
            Dim readUrl As String = ODOO_URL & "/web/dataset/call_kw"
            
            ' Créer la requête
            Dim request As HttpWebRequest = CType(WebRequest.Create(readUrl), HttpWebRequest)
            request.Method = "POST"
            request.ContentType = "application/json"
            
            ' Ajouter les cookies de session
            If Not String.IsNullOrEmpty(cookies) Then
                request.Headers.Add("Cookie", cookies)
            End If
            
            ' Liste des champs à récupérer
            Dim fields As String = """qdv_nom_utilisateur_windows"",""qdv_opportunityname"",""qdv_oppowneremail"",""qdv_oppownermobilephone"",""qdv_oppownername"",""qdv_oppownertitle"",""qdv_lotnumber"",""qdv_customerreferencenumber"",""qdv_currencyisocode"",""qdv_workstartdate"",""qdv_workenddate""," &
                          """qdv_orgsfid"",""qdv_orgaddressline1"",""qdv_orgaddressline2"",""qdv_orgagencyname"",""qdv_orgcity"",""qdv_orgentitygeoidentifier"",""qdv_orgoperationalunit"",""qdv_orgphonenumber"",""qdv_orgpostalcode"",""qdv_orgprofitcentername"",""qdv_orgregion""," &
                          """qdv_primarycontactaccountname"",""qdv_primarycontactstreet"",""qdv_primarycontactaddressline2"",""qdv_primarycontactcity"",""qdv_primarycontactcountry"",""qdv_primarycontactdepartment"",""qdv_primarycontactemail"",""qdv_primarycontactlastname"",""qdv_primarycontactmailingcountry"",""qdv_primarycontactmobilephone"",""qdv_primarycontactpostalcode"",""qdv_primarycontactsalutation"",""qdv_primarycontactstate"",""qdv_primarycontacttitle""," &
                          """qdv_secondarycontactaccountname"",""qdv_secondarycontactstreet"",""qdv_secondarycontactaddressline2"",""qdv_secondarycontactcity"",""qdv_secondarycontactcountry"",""qdv_secondarycontactdepartment"",""qdv_secondarycontactemail"",""qdv_secondarycontactlastname"",""qdv_secondarycontactmailingcountry"",""qdv_secondarycontactmobilephone"",""qdv_secondarycontactpostalcode"",""qdv_secondarycontactsalutation"",""qdv_secondarycontactstate"",""qdv_secondarycontacttitle"""
            
            ' Créer le JSON de requête (manuellement)
            Dim requestData As String = "{""jsonrpc"":""2.0"",""params"":{""model"":""crm.lead"",""method"":""read"",""args"":[[" & opportunityId.ToString() & "]],""kwargs"":{""fields"":[" & fields & "]}}}"
            
            ' Envoyer
            Dim dataBytes As Byte() = Encoding.UTF8.GetBytes(requestData)
            request.ContentLength = dataBytes.Length
            
            Using stream As IO.Stream = request.GetRequestStream()
                stream.Write(dataBytes, 0, dataBytes.Length)
            End Using
            
            ' Lire la réponse
            Using response As HttpWebResponse = CType(request.GetResponse(), HttpWebResponse)
                Using reader As New IO.StreamReader(response.GetResponseStream())
                    Dim responseText As String = reader.ReadToEnd()
                    
                    ' Créer l'objet et extraire les valeurs
                    Dim gotObject As New GetObjectFromOdoo()
                    
                    ' Informations Opportunité (11 champs)
                    gotObject.nom_utilisateur_windows = ExtractJsonValue(responseText, "qdv_nom_utilisateur_windows")
                    gotObject.opportunityName = ExtractJsonValue(responseText, "qdv_opportunityname")
                    gotObject.oppOwnerEmail = ExtractJsonValue(responseText, "qdv_oppowneremail")
                    gotObject.oppOwnerMobilePhone = ExtractJsonValue(responseText, "qdv_oppownermobilephone")
                    gotObject.oppOwnerName = ExtractJsonValue(responseText, "qdv_oppownername")
                    gotObject.oppOwnerTitle = ExtractJsonValue(responseText, "qdv_oppownertitle")
                    gotObject.lotNumber = ExtractJsonValue(responseText, "qdv_lotnumber")
                    gotObject.customerReferenceNumber = ExtractJsonValue(responseText, "qdv_customerreferencenumber")
                    gotObject.currencyIsoCode = ExtractJsonValue(responseText, "qdv_currencyisocode")
                    
                    ' Dates (à parser)
                    Dim startDateStr As String = ExtractJsonValue(responseText, "qdv_workstartdate")
                    If Not String.IsNullOrEmpty(startDateStr) Then
                        Try
                            gotObject.workStartDate = DateTime.Parse(startDateStr)
                        Catch
                        End Try
                    End If
                    
                    Dim endDateStr As String = ExtractJsonValue(responseText, "qdv_workenddate")
                    If Not String.IsNullOrEmpty(endDateStr) Then
                        Try
                            gotObject.workEndDate = DateTime.Parse(endDateStr)
                        Catch
                        End Try
                    End If
                    
                    ' Organisation (11 champs)
                    gotObject.orgSfId = ExtractJsonValue(responseText, "qdv_orgsfid")
                    gotObject.orgAddressLine1 = ExtractJsonValue(responseText, "qdv_orgaddressline1")
                    gotObject.orgAddressLine2 = ExtractJsonValue(responseText, "qdv_orgaddressline2")
                    gotObject.orgAgencyName = ExtractJsonValue(responseText, "qdv_orgagencyname")
                    gotObject.orgCity = ExtractJsonValue(responseText, "qdv_orgcity")
                    gotObject.orgEntityGeoIdentifier = ExtractJsonValue(responseText, "qdv_orgentitygeoidentifier")
                    gotObject.orgOperationalUnit = ExtractJsonValue(responseText, "qdv_orgoperationalunit")
                    gotObject.orgPhoneNumber = ExtractJsonValue(responseText, "qdv_orgphonenumber")
                    gotObject.orgPostalCode = ExtractJsonValue(responseText, "qdv_orgpostalcode")
                    gotObject.orgProfitCenterName = ExtractJsonValue(responseText, "qdv_orgprofitcentername")
                    gotObject.orgRegion = ExtractJsonValue(responseText, "qdv_orgregion")
                    
                    ' Contact Principal (14 champs)
                    gotObject.primaryContactAccountName = ExtractJsonValue(responseText, "qdv_primarycontactaccountname")
                    gotObject.primaryContactStreet = ExtractJsonValue(responseText, "qdv_primarycontactstreet")
                    gotObject.primaryContactAddressLine2 = ExtractJsonValue(responseText, "qdv_primarycontactaddressline2")
                    gotObject.primaryContactCity = ExtractJsonValue(responseText, "qdv_primarycontactcity")
                    gotObject.primaryContactCountry = ExtractJsonValue(responseText, "qdv_primarycontactcountry")
                    gotObject.primaryContactDepartment = ExtractJsonValue(responseText, "qdv_primarycontactdepartment")
                    gotObject.primaryContactEmail = ExtractJsonValue(responseText, "qdv_primarycontactemail")
                    gotObject.primaryContactLastName = ExtractJsonValue(responseText, "qdv_primarycontactlastname")
                    gotObject.primaryContactMailingCountry = ExtractJsonValue(responseText, "qdv_primarycontactmailingcountry")
                    gotObject.primaryContactMobilePhone = ExtractJsonValue(responseText, "qdv_primarycontactmobilephone")
                    gotObject.primaryContactPostalCode = ExtractJsonValue(responseText, "qdv_primarycontactpostalcode")
                    gotObject.primaryContactSalutation = ExtractJsonValue(responseText, "qdv_primarycontactsalutation")
                    gotObject.primaryContactState = ExtractJsonValue(responseText, "qdv_primarycontactstate")
                    gotObject.primaryContactTitle = ExtractJsonValue(responseText, "qdv_primarycontacttitle")
                    
                    ' Contact Secondaire (14 champs)
                    gotObject.secondaryContactAccountName = ExtractJsonValue(responseText, "qdv_secondarycontactaccountname")
                    gotObject.secondaryContactStreet = ExtractJsonValue(responseText, "qdv_secondarycontactstreet")
                    gotObject.secondaryContactAddressLine2 = ExtractJsonValue(responseText, "qdv_secondarycontactaddressline2")
                    gotObject.secondaryContactCity = ExtractJsonValue(responseText, "qdv_secondarycontactcity")
                    gotObject.secondaryContactCountry = ExtractJsonValue(responseText, "qdv_secondarycontactcountry")
                    gotObject.secondaryContactDepartment = ExtractJsonValue(responseText, "qdv_secondarycontactdepartment")
                    gotObject.secondaryContactEmail = ExtractJsonValue(responseText, "qdv_secondarycontactemail")
                    gotObject.secondaryContactLastName = ExtractJsonValue(responseText, "qdv_secondarycontactlastname")
                    gotObject.secondaryContactMailingCountry = ExtractJsonValue(responseText, "qdv_secondarycontactmailingcountry")
                    gotObject.secondaryContactMobilePhone = ExtractJsonValue(responseText, "qdv_secondarycontactmobilephone")
                    gotObject.secondaryContactPostalCode = ExtractJsonValue(responseText, "qdv_secondarycontactpostalcode")
                    gotObject.secondaryContactSalutation = ExtractJsonValue(responseText, "qdv_secondarycontactsalutation")
                    gotObject.secondaryContactState = ExtractJsonValue(responseText, "qdv_secondarycontactstate")
                    gotObject.secondaryContactTitle = ExtractJsonValue(responseText, "qdv_secondarycontacttitle")
                    
                    Return gotObject
                End Using
            End Using
            
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
                    errAnswer.status = "error"
                    errAnswer.ErrorGot = "Erreur d'authentification Odoo"
                    Return errAnswer
                End If
            End If
            
            Dim writeUrl As String = ODOO_URL & "/web/dataset/call_kw"
            
            ' Créer la requête
            Dim request As HttpWebRequest = CType(WebRequest.Create(writeUrl), HttpWebRequest)
            request.Method = "POST"
            request.ContentType = "application/json"
            
            ' Ajouter les cookies
            If Not String.IsNullOrEmpty(cookies) Then
                request.Headers.Add("Cookie", cookies)
            End If
            
            ' Créer le JSON des valeurs (simplifié - ajouter tous les champs)
            Dim values As String = """qdv_sys_filepath"":""" & quoteData.sys_filepath.Replace("\", "\\").Replace("""", "\""") & """," &
                                  """qdv_sys_filename"":""" & quoteData.sys_filename.Replace("""", "\""") & """," &
                                  """qdv_sys_version_num"":""" & quoteData.sys_version_num & """"
            
            ' TODO: Ajouter les 55 autres champs ici
            
            ' Créer le JSON de requête
            Dim requestData As String = "{""jsonrpc"":""2.0"",""params"":{""model"":""crm.lead"",""method"":""write"",""args"":[[" & opportunityId.ToString() & "],{" & values & "}]}}"
            
            ' Envoyer
            Dim dataBytes As Byte() = Encoding.UTF8.GetBytes(requestData)
            request.ContentLength = dataBytes.Length
            
            Using stream As IO.Stream = request.GetRequestStream()
                stream.Write(dataBytes, 0, dataBytes.Length)
            End Using
            
            ' Lire la réponse
            Using response As HttpWebResponse = CType(request.GetResponse(), HttpWebResponse)
                Using reader As New IO.StreamReader(response.GetResponseStream())
                    Dim responseText As String = reader.ReadToEnd()
                    
                    Dim answer As New AnswerFromOdoo()
                    answer.status = "success"
                    answer.message = "Devis envoyé avec succès"
                    Return answer
                End Using
            End Using
            
        Catch ex As Exception
            Dim errAnswer As New AnswerFromOdoo()
            errAnswer.status = "error"
            errAnswer.ErrorGot = "Erreur écriture Odoo: " & ex.Message
            Return errAnswer
        End Try
    End Function
    
End Module
