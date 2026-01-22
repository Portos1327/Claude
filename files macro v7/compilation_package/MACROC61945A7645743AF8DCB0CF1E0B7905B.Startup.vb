Imports System
Imports System.IO
Imports System.Windows.Forms
Imports System.Collections.Generic
Imports System.Environment
Imports Microsoft.VisualBasic
Imports Qdv.CommonApi
Imports Qdv.UserApi

Namespace QDV_Macro

    Public Class Startup
        Public Shared Sub EntryMethod(ByVal Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext)
            Dim clOdoo As OdooStuff
            Try
                clOdoo = New OdooStuff
                clOdoo.MainCall(Es, Context)
            Catch GeneralError As Exception
                MessageBox.Show(GeneralError.Message, "Erreur!", MessageBoxButtons.OK, MessageBoxIcon.Error)
                Context.MustCancel = True
            Finally
                clOdoo = Nothing
            End Try
        End Sub
    End Class

    Public Class OdooStuff
        
        Dim waitForm As frmMessage = Nothing
        Dim showDebugMessages As String = "NO"
        Dim tempFolder As String = System.IO.Path.GetTempPath
        Dim ComingFrom As String = Nothing
        
        Public Sub MainCall(ByRef Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext)
            
            ' Vérifier que le devis est enregistré
            If Es.FullPath.ToLower.Contains("\qdvtempfilesmain\") Then
                MsgBox("Veuillez enregistrer votre devis avant d'interagir avec Odoo.", MsgBoxStyle.Critical, "ERREUR !")
                Exit Sub
            End If
            
            Dim operationRequired As String = Nothing
            
            ' Afficher le formulaire de choix
            ComingFrom = Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_ComingFrom")
            If ComingFrom = "CHOICE" Then
                Dim frmChoice As New FrmChoice(Es)
                frmChoice.ShowDialog()
            End If
            
            ' Récupérer l'opération demandée
            Try
                operationRequired = Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_Operation").ToString
            Catch ex As Exception
                MsgBox("La variable GLV_SF_Operation est introuvable dans ce devis !" & vbCrLf & vbCrLf & ex.Message, MsgBoxStyle.Critical, "Impossible de communiquer avec Odoo !")
                Exit Sub
            End Try
            
            If String.IsNullOrEmpty(operationRequired) Then
                Exit Sub
            End If
            
            ' Récupérer le numéro d'opportunité
            Dim oppNumber As String = Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_oppId")
            
            ' Selon l'opération demandée
            Select Case operationRequired.ToUpper
                Case "READFROMODOO", "GETOPPID"
                    ' Lire depuis Odoo
                    ReadFromOdoo(Es, Context, oppNumber)
                    
                Case "WRITETOODOO"
                    ' Écrire vers Odoo
                    WriteToOdoo(Es, Context, oppNumber)
                    
                Case Else
                    MsgBox("Opération inconnue : " & operationRequired, MsgBoxStyle.Critical, "Erreur")
            End Select
            
        End Sub
        
        ' ===== LECTURE DEPUIS ODOO =====
        Private Sub ReadFromOdoo(ByRef Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext, ByVal oppNumber As String)
            Try
                ' Demander le numéro d'opportunité si vide
                If String.IsNullOrEmpty(oppNumber) Then
                    oppNumber = InputBox("Entrez le numéro d'opportunité Odoo :", "Connexion à Odoo", "")
                    If String.IsNullOrEmpty(oppNumber) Then
                        Exit Sub
                    End If
                    ' Sauvegarder le numéro
                    Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_oppId", oppNumber, GlobalVariableType.TypeString)
                End If
                
                ' Convertir en Integer
                Dim oppId As Integer
                If Not Integer.TryParse(oppNumber, oppId) Then
                    MsgBox("Le numéro d'opportunité doit être un nombre entier.", MsgBoxStyle.Critical, "Erreur")
                    Exit Sub
                End If
                
                ' Afficher message d'attente
                waitForm = New frmMessage()
                waitForm.Show()
                waitForm.Refresh()
                Application.DoEvents()
                
                ' Appeler l'API Odoo pour récupérer les données
                Dim gotObject As GetObjectFromOdoo = Functions_Odoo.GetOpportunityFromOdoo(oppId)
                
                ' Fermer le message d'attente
                If waitForm IsNot Nothing Then
                    waitForm.Close()
                    waitForm = Nothing
                End If
                
                ' Vérifier les erreurs
                If Not String.IsNullOrEmpty(gotObject.ErrorGot) Then
                    MsgBox("Erreur lors de la récupération des données Odoo :" & vbCrLf & gotObject.ErrorGot, MsgBoxStyle.Critical, "Erreur")
                    Exit Sub
                End If
                
                ' Remplir les variables QuickDevis avec les données Odoo (50 champs)
                FillQuickDevisVariables(Es, gotObject)
                
                MsgBox("Données récupérées depuis Odoo avec succès !" & vbCrLf & "Opportunité : " & gotObject.opportunityName, MsgBoxStyle.Information, "Succès")
                
            Catch ex As Exception
                If waitForm IsNot Nothing Then
                    waitForm.Close()
                    waitForm = Nothing
                End If
                MsgBox("Erreur lors de la lecture depuis Odoo :" & vbCrLf & ex.Message, MsgBoxStyle.Critical, "Erreur")
            End Try
        End Sub
        
        ' ===== ÉCRITURE VERS ODOO =====
        Private Sub WriteToOdoo(ByRef Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext, ByVal oppNumber As String)
            Try
                ' Vérifier que l'opportunité est définie
                If String.IsNullOrEmpty(oppNumber) Then
                    MsgBox("Aucun numéro d'opportunité Odoo défini." & vbCrLf & "Veuillez d'abord récupérer les données depuis Odoo.", MsgBoxStyle.Critical, "Erreur")
                    Exit Sub
                End If
                
                ' Convertir en Integer
                Dim oppId As Integer
                If Not Integer.TryParse(oppNumber, oppId) Then
                    MsgBox("Le numéro d'opportunité doit être un nombre entier.", MsgBoxStyle.Critical, "Erreur")
                    Exit Sub
                End If
                
                ' Afficher message d'attente
                waitForm = New frmMessage()
                waitForm.Show()
                waitForm.Refresh()
                Application.DoEvents()
                
                ' Créer l'objet avec les données QuickDevis (58 champs)
                Dim sendObject As SendObjectToOdoo = CreateSendObject(Es)
                
                ' Envoyer vers Odoo
                Dim answer As AnswerFromOdoo = Functions_Odoo.SendQuoteToOdoo(oppId, sendObject)
                
                ' Fermer le message d'attente
                If waitForm IsNot Nothing Then
                    waitForm.Close()
                    waitForm = Nothing
                End If
                
                ' Vérifier la réponse
                If answer.status = "success" Then
                    MsgBox("Devis envoyé à Odoo avec succès !" & vbCrLf & "Opportunité ID : " & oppId, MsgBoxStyle.Information, "Succès")
                Else
                    MsgBox("Erreur lors de l'envoi vers Odoo :" & vbCrLf & answer.ErrorGot, MsgBoxStyle.Critical, "Erreur")
                End If
                
            Catch ex As Exception
                If waitForm IsNot Nothing Then
                    waitForm.Close()
                    waitForm = Nothing
                End If
                MsgBox("Erreur lors de l'écriture vers Odoo :" & vbCrLf & ex.Message, MsgBoxStyle.Critical, "Erreur")
            End Try
        End Sub
        
        ' ===== REMPLIR LES VARIABLES QUICKDEVIS (50 champs Odoo → QDV) =====
        Private Sub FillQuickDevisVariables(ByRef Es As Qdv.UserApi.IEstimate, ByVal gotObject As GetObjectFromOdoo)
            ' Informations Opportunité
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_nom_utilisateur_windows", gotObject.nom_utilisateur_windows, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_opportunityName", gotObject.opportunityName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_oppOwnerEmail", gotObject.oppOwnerEmail, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_oppOwnerMobilePhone", gotObject.oppOwnerMobilePhone, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_oppOwnerName", gotObject.oppOwnerName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_oppOwnerTitle", gotObject.oppOwnerTitle, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_lotNumber", gotObject.lotNumber, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_customerReferenceNumber", gotObject.customerReferenceNumber, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_currencyIsoCode", gotObject.currencyIsoCode, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_workStartDate", gotObject.workStartDate, GlobalVariableType.TypeDate)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_workEndDate", gotObject.workEndDate, GlobalVariableType.TypeDate)
            
            ' Organisation (11 champs)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgSfId", gotObject.orgSfId, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgAddressLine1", gotObject.orgAddressLine1, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgAddressLine2", gotObject.orgAddressLine2, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgAgencyName", gotObject.orgAgencyName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgCity", gotObject.orgCity, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgEntityGeoIdentifier", gotObject.orgEntityGeoIdentifier, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgOperationalUnit", gotObject.orgOperationalUnit, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgPhoneNumber", gotObject.orgPhoneNumber, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgPostalCode", gotObject.orgPostalCode, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgProfitCenterName", gotObject.orgProfitCenterName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_orgRegion", gotObject.orgRegion, GlobalVariableType.TypeString)
            
            ' Contact Principal (14 champs)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactAccountName", gotObject.primaryContactAccountName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactStreet", gotObject.primaryContactStreet, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactAddressLine2", gotObject.primaryContactAddressLine2, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactCity", gotObject.primaryContactCity, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactCountry", gotObject.primaryContactCountry, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactDepartment", gotObject.primaryContactDepartment, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactEmail", gotObject.primaryContactEmail, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactLastName", gotObject.primaryContactLastName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactMailingCountry", gotObject.primaryContactMailingCountry, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactMobilePhone", gotObject.primaryContactMobilePhone, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactPostalCode", gotObject.primaryContactPostalCode, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactSalutation", gotObject.primaryContactSalutation, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactState", gotObject.primaryContactState, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_primaryContactTitle", gotObject.primaryContactTitle, GlobalVariableType.TypeString)
            
            ' Contact Secondaire (14 champs)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactAccountName", gotObject.secondaryContactAccountName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactStreet", gotObject.secondaryContactStreet, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactAddressLine2", gotObject.secondaryContactAddressLine2, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactCity", gotObject.secondaryContactCity, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactCountry", gotObject.secondaryContactCountry, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactDepartment", gotObject.secondaryContactDepartment, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactEmail", gotObject.secondaryContactEmail, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactLastName", gotObject.secondaryContactLastName, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactMailingCountry", gotObject.secondaryContactMailingCountry, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactMobilePhone", gotObject.secondaryContactMobilePhone, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactPostalCode", gotObject.secondaryContactPostalCode, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactSalutation", gotObject.secondaryContactSalutation, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactState", gotObject.secondaryContactState, GlobalVariableType.TypeString)
            Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_secondaryContactTitle", gotObject.secondaryContactTitle, GlobalVariableType.TypeString)
        End Sub
        
        ' ===== CRÉER L'OBJET À ENVOYER (58 champs QDV → Odoo) =====
        Private Function CreateSendObject(ByRef Es As Qdv.UserApi.IEstimate) As SendObjectToOdoo
            Dim sendObj As New SendObjectToOdoo()
            
            ' TODO: Remplir les 58 champs avec les valeurs du devis QuickDevis
            ' Pour l'instant, récupérer depuis les variables globales si elles existent
            
            ' Informations Fichier
            sendObj.sys_filepath = Es.FullPath
            sendObj.sys_filename = Path.GetFileName(Es.FullPath)
            sendObj.sys_version_num = Es.CurrentVersion.Number.ToString()
            
            ' TODO: Ajouter ici la logique pour remplir les 58 champs depuis QuickDevis
            ' Exemple :
            ' sendObj.totalExclTax = Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_TotalHT").ToString()
            ' sendObj.totalInclTax = Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_TotalTTC").ToString()
            ' etc.
            
            Return sendObj
        End Function
        
    End Class

End Namespace
