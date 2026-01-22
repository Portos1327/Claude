Imports System
Imports System.Windows.Forms

Public Class FrmChoice
    Private _Es As Qdv.UserApi.IEstimate = Nothing
    'Friend ComingFromChoice As Boolean = False
    Public Sub New(es As Qdv.UserApi.IEstimate)
        ' Cet appel est requis par le concepteur.
        InitializeComponent()
        _Es = es
        ' Ajoutez une initialisation quelconque après l'appel InitializeComponent().
    End Sub
    Private Sub FrmChoice_Load(sender As Object, e As EventArgs) Handles Me.Load
        Dim Tooltip As New ToolTip
        Tooltip.SetToolTip(Me.btnSendToSF, "Créer une nouvelle version et envoyer les données à SaleForce")
        Tooltip.SetToolTip(Me.btnReadFromSF, "Lire les données de l'opportunité")
        Tooltip.SetToolTip(Me.btnAccessOpportunity, "Accéder à l'opportunité")
        Tooltip.SetToolTip(Me.btnAccessSFEstimate, "Accéder au devis SalesForce")
        lblOpportunity.Text = "Opportunité : "
        lblEstimate.Text = "Devis : "
        If _Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_ID").ToString.Trim = "" Then
            lblOpportunity.Text &= "N/A"
        Else
            lblOpportunity.Text &= _Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_ID")
        End If
        If _Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_QDVQuoteName").ToString.Trim = "" Then
            lblEstimate.Text &= "N/A"
        Else
            lblEstimate.Text &= _Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_QDVQuoteName")

        End If
    End Sub

    Private Sub btnClose_Click(sender As Object, e As EventArgs) Handles btnClose.Click
        _Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_Operation", "", Qdv.UserApi.GlobalVariableType.TypeString)
        Me.Dispose()
    End Sub

    Private Sub btnSendToSF_Click(sender As Object, e As EventArgs) Handles btnSendToSF.Click
        _Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_Operation", "WRITETOSF", Qdv.UserApi.GlobalVariableType.TypeString)

        'Set global variable ComingFromChoice to true to Create a new estimate version automaticaly
        'ComingFromChoice = True
        Me.Dispose()
    End Sub

    Private Sub btnReadFromSF_Click(sender As Object, e As EventArgs) Handles btnReadFromSF.Click
        If _Es.CurrentVersion.GlobalVariables.GetVariableValue("GLV_SF_ID").ToString.Trim = "" Then
            _Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_Operation", "GETSFID", Qdv.UserApi.GlobalVariableType.TypeString)
        Else
            _Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_Operation", "READFROMSF", Qdv.UserApi.GlobalVariableType.TypeString)
        End If

        Me.Dispose()
    End Sub

    Private Sub btnAccessOpportunity_Click(sender As Object, e As EventArgs) Handles btnAccessOpportunity.Click
        _Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_Operation", "ACCESSSFOPP", Qdv.UserApi.GlobalVariableType.TypeString)
        Me.Dispose()
    End Sub

    Private Sub btnAccessSFEstimate_Click(sender As Object, e As EventArgs) Handles btnAccessSFEstimate.Click
        _Es.CurrentVersion.GlobalVariables.SetVariableValue("GLV_SF_Operation", "ACCESSQUOTE", Qdv.UserApi.GlobalVariableType.TypeString)
        Me.Dispose()
    End Sub
End Class