' ============================================================
' MACRO QDV7 : ImportOdooChanges.bas
' Import des modifications Odoo dans une base d'ouvrage QDV7
'
' Usage :
'  1. Dans QDV7, ouvrir votre base d'ouvrage
'  2. Exécuter cette macro via Outils > Macros
'  3. Sélectionner le fichier JSON exporté depuis Odoo
'
' Version : 1.0.0
' Auteur : BYes - Centre GTB Turquand
' ============================================================

Option Explicit

Sub ImportOdooChanges()
    ' Sélection du fichier JSON
    Dim jsonFilePath As String
    jsonFilePath = SelectJsonFile()
    If jsonFilePath = "" Then
        MsgBox "Import annulé.", vbInformation, "QDV Ouvrage Manager"
        Exit Sub
    End If
    
    ' Lecture du fichier JSON
    Dim jsonContent As String
    jsonContent = ReadFile(jsonFilePath)
    If jsonContent = "" Then
        MsgBox "Impossible de lire le fichier JSON.", vbCritical, "Erreur"
        Exit Sub
    End If
    
    ' Parse JSON (simplifié - utilise les fonctions built-in QDV7 ou ScriptControl)
    Dim ouvragesData As Object
    Set ouvragesData = ParseJson(jsonContent)
    
    If ouvragesData Is Nothing Then
        MsgBox "Impossible de parser le fichier JSON.", vbCritical, "Erreur"
        Exit Sub
    End If
    
    ' Connexion à la base SQLite (.grp)
    Dim dbPath As String
    dbPath = GetCurrentGrpPath() ' À adapter selon l'API QDV7
    
    Dim conn As Object
    Set conn = CreateObject("ADODB.Connection")
    conn.Open "Driver={SQLite3 ODBC Driver};Database=" & dbPath & ";"
    
    Dim updatedCount As Integer
    Dim createdCount As Integer
    updatedCount = 0
    createdCount = 0
    
    ' Traitement de chaque ouvrage
    Dim ouvrages As Object
    Set ouvrages = ouvragesData("ouvrages")
    
    Dim i As Integer
    For i = 0 To ouvrages.Count - 1
        Dim ouvrage As Object
        Set ouvrage = ouvrages(i)
        
        Dim rowId As Long
        rowId = CLng(ouvrage("RowID"))
        
        ' Vérifier si l'ouvrage existe
        Dim rs As Object
        Set rs = conn.Execute("SELECT RowID FROM Groups WHERE RowID = " & rowId)
        
        If rs.EOF Then
            ' Créer l'ouvrage
            Dim insertSql As String
            insertSql = "INSERT INTO Groups (RowID, Description, Reference, Family, " & _
                       "Manufacturer, UserDefinedField, Unit, ForcedSellingPricePerUnit, " & _
                       "TakeForcedSellingPrice, LockTheGroup) VALUES (" & _
                       rowId & ", " & _
                       QuoteSql(ouvrage("Description")) & ", " & _
                       QuoteSql(ouvrage("Reference")) & ", " & _
                       QuoteSql(ouvrage("Family")) & ", " & _
                       QuoteSql(ouvrage("Manufacturer")) & ", " & _
                       QuoteSql(ouvrage("UserDefinedField")) & ", " & _
                       QuoteSql(ouvrage("Unit")) & ", " & _
                       ouvrage("ForcedSellingPricePerUnit") & ", " & _
                       ouvrage("TakeForcedSellingPrice") & ", " & _
                       ouvrage("LockTheGroup") & ")"
            conn.Execute insertSql
            createdCount = createdCount + 1
        Else
            ' Mettre à jour l'ouvrage
            Dim updateSql As String
            updateSql = "UPDATE Groups SET " & _
                       "Description = " & QuoteSql(ouvrage("Description")) & ", " & _
                       "Reference = " & QuoteSql(ouvrage("Reference")) & ", " & _
                       "Family = " & QuoteSql(ouvrage("Family")) & ", " & _
                       "Manufacturer = " & QuoteSql(ouvrage("Manufacturer")) & ", " & _
                       "UserDefinedField = " & QuoteSql(ouvrage("UserDefinedField")) & ", " & _
                       "Unit = " & QuoteSql(ouvrage("Unit")) & ", " & _
                       "ForcedSellingPricePerUnit = " & ouvrage("ForcedSellingPricePerUnit") & ", " & _
                       "TakeForcedSellingPrice = " & ouvrage("TakeForcedSellingPrice") & ", " & _
                       "LockTheGroup = " & ouvrage("LockTheGroup") & " " & _
                       "WHERE RowID = " & rowId
            conn.Execute updateSql
            updatedCount = updatedCount + 1
        End If
        
        rs.Close
        Set rs = Nothing
    Next i
    
    conn.Close
    Set conn = Nothing
    
    MsgBox "✅ Import terminé !" & vbCrLf & vbCrLf & _
           "Ouvrages mis à jour : " & updatedCount & vbCrLf & _
           "Ouvrages créés : " & createdCount, _
           vbInformation, "QDV Ouvrage Manager - Import Odoo"
    
    ' Recharger la base dans QDV7
    RefreshDatabase()
End Sub

' ============================================================
' Fonctions utilitaires
' ============================================================

Function SelectJsonFile() As String
    Dim dialog As Object
    Set dialog = CreateObject("UserAccounts.CommonDialog")
    dialog.Filter = "Fichiers JSON (*.json)|*.json|Tous fichiers (*.*)|*.*"
    dialog.FilterIndex = 1
    dialog.InitDir = Environ("USERPROFILE") & "\Downloads"
    If dialog.ShowOpen Then
        SelectJsonFile = dialog.FileName
    Else
        SelectJsonFile = ""
    End If
End Function

Function ReadFile(filePath As String) As String
    Dim fso As Object
    Dim ts As Object
    Set fso = CreateObject("Scripting.FileSystemObject")
    Set ts = fso.OpenTextFile(filePath, 1, False, -1) ' -1 = Unicode
    ReadFile = ts.ReadAll
    ts.Close
End Function

Function QuoteSql(value As String) As String
    ' Echapper les apostrophes pour SQL
    QuoteSql = "'" & Replace(value, "'", "''") & "'"
End Function

Function ParseJson(jsonStr As String) As Object
    ' Utilisation de ScriptControl pour parser le JSON
    ' (Disponible sur Windows 32bit, ou via alternative sur 64bit)
    On Error Resume Next
    Dim sc As Object
    Set sc = CreateObject("MSScriptControl.ScriptControl")
    If Err.Number <> 0 Then
        ' Fallback : tenter via WScript.Shell ou autre méthode
        Set ParseJson = Nothing
        Exit Function
    End If
    sc.Language = "JScript"
    sc.ExecuteStatement "var data = " & jsonStr
    Set ParseJson = sc.CodeObject.data
    On Error GoTo 0
End Function

Sub RefreshDatabase()
    ' Commande spécifique QDV7 pour recharger la base
    ' À adapter selon l'API QDV7 disponible
    ' QDV7.RefreshCurrentDatabase  ' Exemple
End Sub

Function GetCurrentGrpPath() As String
    ' Retourne le chemin de la base d'ouvrage actuellement ouverte dans QDV7
    ' À adapter selon l'API QDV7 disponible
    ' GetCurrentGrpPath = QDV7.CurrentDatabase.Path  ' Exemple
    GetCurrentGrpPath = ""  ' Placeholder
End Function
