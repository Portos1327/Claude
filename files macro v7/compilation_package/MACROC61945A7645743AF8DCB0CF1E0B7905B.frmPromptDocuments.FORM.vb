Imports System
Imports System.IO
Imports System.Windows.Forms
Imports System.Collections.Generic
Imports Microsoft.VisualBasic
Imports GemBox.Document
Public Class frmPromptDocuments
    Dim QDVInstalledPath As String = Path.GetDirectoryName(Application.ExecutablePath) & "\"
    Dim tempFolderForReports As String = System.IO.Path.GetTempPath & "SFReports\"
    'Dim Operation As Int16
    Dim CommercialOffer = ""
    Dim TechnicalOffer = ""
    Dim Overhead = ""
    Dim Wbs = ""
    'Dim Result As String = ""
    Friend btnClicked As String

    Private _Es As Qdv.UserApi.IEstimate = Nothing

    Public Sub New(es As Qdv.UserApi.IEstimate)
        ' Cet appel est requis par le concepteur.
        InitializeComponent()
        _Es = es
        ' Ajoutez une initialisation quelconque après l'appel InitializeComponent().
    End Sub
    Private Sub frmPromptDocuments_Load(sender As Object, e As EventArgs) Handles Me.Load

        If Not Directory.Exists(tempFolderForReports) Then Directory.CreateDirectory(tempFolderForReports)

    End Sub
    Private Sub btnOK_Click(sender As Object, e As System.EventArgs) Handles btnOK.Click
        Dim sw As New StreamWriter(tempFolderForReports & "Operation.inf", False)

        'Operation.inf contains :
        '  - 1 for word default
        '  - 2 for selection
        'If File.Exists(tempFolderForReports & "Operation.inf") Then File.Delete(tempFolderForReports & "Operation.inf")

        If rbnDefaultWord.Checked Then
            DisableButtons()
            'btnOK.Enabled = True
            Try
                sw.WriteLine(1)
                sw.Dispose()

                'Create word document from model
                Dim MyWBS As Qdv.UserApi.IEstimateVersion = _Es.CurrentVersion

                '===================
                'WITH GEMBOX OBJECTS
                '===================
                Dim TempPathToTemplate As String = System.IO.Path.GetTempFileName() & ".docx"
                Dim DefaultTemplate As String = "DEFAULT_WORD.docx"
                Dim pdfCommercialOffer As String = tempFolderForReports & "CommercialOffer.pdf"
                Try
                    If File.Exists(TempPathToTemplate) Then File.Delete(TempPathToTemplate)
                Catch ex As Exception
                    MessageBox.Show("Impossible de supprimer le modèle", "ERROR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End Try

                Try
                    If File.Exists(pdfCommercialOffer) Then File.Delete(pdfCommercialOffer)
                Catch ex As Exception
                    MessageBox.Show("Impossible de supprimer le fichier de sortie", "ERROR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End Try
                MyWBS.ExtractWordTemplate(DefaultTemplate, TempPathToTemplate)
                MyWBS.CreateWordDocument(TempPathToTemplate, pdfCommercialOffer, True)


                ''=====================
                '' WITH TELERIK OBJECTS
                ''=====================
                ''Create stream and import Docx in
                'Dim WordFormatProvider As Telerik.Windows.Documents.Flow.FormatProviders.Docx.DocxFormatProvider =
                '        New Telerik.Windows.Documents.Flow.FormatProviders.Docx.DocxFormatProvider
                'Dim Input As Stream = File.OpenRead(DocxFileName)
                'Dim Document As Telerik.Windows.Documents.Flow.Model.RadFlowDocument = WordFormatProvider.Import(Input)
                'Input.Dispose()

                ''Export to pdf
                'Dim PdfFormatProvider As Telerik.Windows.Documents.Flow.FormatProviders.Pdf.PdfFormatProvider =
                '    New Telerik.Windows.Documents.Flow.FormatProviders.Pdf.PdfFormatProvider
                'Dim output As Stream = File.OpenWrite(PdfFileName)
                'PdfFormatProvider.Export(Document, output)
                'output.Dispose()
            Catch ex As Exception
                MessageBox.Show("ERREUR DANS LA CREATION DE L'ETAT" & vbCrLf & vbCrLf & ex.Message, "ERREUR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                Exit Sub
            Finally
                sw.Dispose()
                'If File.Exists(tempFolderForReports & "CommercialOffer.docx") Then File.Delete(tempFolderForReports & "CommercialOffer.docx")
            End Try
        ElseIf rbnSelection.Checked Then
            EnableButtons()
            'Send Selected Documents
            sw.WriteLine(2)

            'Verify if files exist and write line in Operation.inf

            If txtCommercialOffer.Text.Trim <> "" Then
                If File.Exists(txtCommercialOffer.Text.Trim) Then
                    sw.WriteLine("COMMERCIALOFFER" & vbTab & txtCommercialOffer.Text.Trim)
                Else
                    MessageBox.Show("Le fichier : " & txtCommercialOffer.Text.Trim & " n'existe pas", "ERROR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End If
            End If

            If txtTechnicalOffer.Text.Trim <> "" Then
                If File.Exists(txtTechnicalOffer.Text.Trim) Then
                    sw.WriteLine("TECHNICALOFFER" & vbTab & txtTechnicalOffer.Text.Trim)
                Else
                    MessageBox.Show("Le fichier : " & txtTechnicalOffer.Text.Trim & " n'existe pas", "ERROR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End If
            End If

            If txtOverhead.Text.Trim <> "" Then
                If File.Exists(txtOverhead.Text.Trim) Then
                    sw.WriteLine("OVERHEAD" & vbTab & txtOverhead.Text.Trim)
                Else
                    MessageBox.Show("Le fichier : " & txtOverhead.Text.Trim & " n'existe pas", "ERROR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End If
            End If

            If txtwbs.Text.Trim <> "" Then
                If File.Exists(txtwbs.Text.Trim) Then
                    sw.WriteLine("WBS" & vbTab & txtwbs.Text.Trim)
                Else
                    MessageBox.Show("Le fichier : " & txtwbs.Text.Trim & " n'existe pas", "ERROR", MessageBoxButtons.OK, MessageBoxIcon.Error)
                    Exit Sub
                End If
            End If
            sw.Dispose()

        Else
            MessageBox.Show("Veuillez choisir une option", "ERREUR", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Exit Sub
        End If
        sw.Dispose()
        Me.Dispose()
    End Sub

    Private Sub btnCancel_Click(sender As Object, e As System.EventArgs) Handles btnCancel.Click
        btnClicked = "CANCEL"
        Me.Dispose()
    End Sub

    Private Sub btnCommercialOffer_Click(sender As Object, e As System.EventArgs) Handles btnCommercialOffer.Click
        Dim fd As OpenFileDialog = New OpenFileDialog
        fd.Title = "Choix de l'offre commerciale"
        fd.Filter = "Fichier pdf(*.pdf)|*.pdf"
        fd.RestoreDirectory = True
        If fd.ShowDialog = DialogResult.OK Then
            CommercialOffer = fd.FileName
            txtCommercialOffer.Text = CommercialOffer
        End If
    End Sub
    Private Sub btnTechnicalOffer_Click(sender As Object, e As System.EventArgs) Handles btnTechnicalOffer.Click
        Dim fd As OpenFileDialog = New OpenFileDialog
        fd.Title = "Choix de l'offre technique"
        fd.Filter = "Fichier pdf(*.pdf)|*.pdf"
        fd.RestoreDirectory = True
        If fd.ShowDialog = DialogResult.OK Then
            TechnicalOffer = fd.FileName
            txtTechnicalOffer.Text = TechnicalOffer
        End If
    End Sub
    Private Sub btnOverhead_Click(sender As Object, e As System.EventArgs) Handles btnOverhead.Click
        Dim fd As OpenFileDialog = New OpenFileDialog
        fd.Title = "Choix de la feuille de marge"
        fd.Filter = "Fichier pdf(*.pdf)|*.pdf"
        fd.RestoreDirectory = True
        If fd.ShowDialog = DialogResult.OK Then
            Overhead = fd.FileName
            txtOverhead.Text = Overhead
        End If
    End Sub
    Private Sub btnWbs_Click(sender As Object, e As System.EventArgs) Handles btnWbs.Click
        Dim fd As OpenFileDialog = New OpenFileDialog
        fd.Title = "Choix du WBS"
        fd.Filter = "Fichier Excel(*.xlsx)|*.xlsx"
        fd.RestoreDirectory = True
        If fd.ShowDialog = DialogResult.OK Then
            Wbs = fd.FileName
            txtwbs.Text = Wbs
        End If
    End Sub
    Private Sub txtCommercialOffer_Leave(sender As Object, e As EventArgs) Handles txtCommercialOffer.Leave
        CommercialOffer = txtCommercialOffer.Text
    End Sub
    Private Sub txtTechnicalOffer_Leave(sender As Object, e As EventArgs) Handles txtTechnicalOffer.Leave
        TechnicalOffer = txtTechnicalOffer.Text
    End Sub
    Private Sub txtOverhead_Leave(sender As Object, e As EventArgs) Handles txtOverhead.Leave
        Overhead = txtOverhead.Text
    End Sub
    Private Sub txtwbs_Leave(sender As Object, e As EventArgs) Handles txtwbs.Leave
        Wbs = txtwbs.Text
    End Sub
    Private Sub EnableButtons()
        btnCommercialOffer.Enabled = True
        btnTechnicalOffer.Enabled = True
        btnOverhead.Enabled = True
        btnWbs.Enabled = True
        txtCommercialOffer.Enabled = True
        txtTechnicalOffer.Enabled = True
        txtOverhead.Enabled = True
        txtwbs.Enabled = True
    End Sub
    Private Sub DisableButtons()
        btnCommercialOffer.Enabled = False
        btnTechnicalOffer.Enabled = False
        btnOverhead.Enabled = False
        btnWbs.Enabled = False
        txtCommercialOffer.Enabled = False
        txtTechnicalOffer.Enabled = False
        txtOverhead.Enabled = False
        txtwbs.Enabled = False
    End Sub

    Private Sub rbnDefaultPfl_CheckedChanged(sender As Object, e As EventArgs)
        DisableButtons()
    End Sub

    Private Sub rbnDefaultWord_CheckedChanged(sender As Object, e As EventArgs) Handles rbnDefaultWord.CheckedChanged
        DisableButtons()
    End Sub

    Private Sub rbnSelection_CheckedChanged(sender As Object, e As EventArgs) Handles rbnSelection.CheckedChanged
        EnableButtons()
    End Sub
End Class