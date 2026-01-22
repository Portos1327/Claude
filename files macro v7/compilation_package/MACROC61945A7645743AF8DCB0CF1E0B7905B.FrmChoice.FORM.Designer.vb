<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()> _
Partial Class FrmChoice
    Inherits System.Windows.Forms.Form

    'Form remplace la méthode Dispose pour nettoyer la liste des composants.
    <System.Diagnostics.DebuggerNonUserCode()> _
    Protected Overrides Sub Dispose(ByVal disposing As Boolean)
        Try
            If disposing AndAlso components IsNot Nothing Then
                components.Dispose()
            End If
        Finally
            MyBase.Dispose(disposing)
        End Try
    End Sub

    'Requise par le Concepteur Windows Form
    Private components As System.ComponentModel.IContainer

    'REMARQUE : la procédure suivante est requise par le Concepteur Windows Form
    'Elle peut être modifiée à l'aide du Concepteur Windows Form.  
    'Ne la modifiez pas à l'aide de l'éditeur de code.
    <System.Diagnostics.DebuggerStepThrough()> _
    Private Sub InitializeComponent()
        Me.btnClose = New System.Windows.Forms.Button()
        Me.btnAccessSFEstimate = New System.Windows.Forms.Button()
        Me.btnAccessOpportunity = New System.Windows.Forms.Button()
        Me.btnReadFromSF = New System.Windows.Forms.Button()
        Me.btnSendToSF = New System.Windows.Forms.Button()
        Me.lblOpportunity = New System.Windows.Forms.Label()
        Me.lblEstimate = New System.Windows.Forms.Label()
        Me.SuspendLayout()
        '
        'btnClose
        '
        Me.btnClose.Location = New System.Drawing.Point(191, 128)
        Me.btnClose.Name = "btnClose"
        Me.btnClose.Size = New System.Drawing.Size(59, 20)
        Me.btnClose.TabIndex = 8
        Me.btnClose.Text = "Fermer"
        Me.btnClose.UseVisualStyleBackColor = True
        '
        'btnAccessSFEstimate
        '
        Me.btnAccessSFEstimate.BackColor = System.Drawing.Color.Transparent
        Me.btnAccessSFEstimate.Image = Global.My.Resources.Resources.SFEstimate
        Me.btnAccessSFEstimate.Location = New System.Drawing.Point(191, 70)
        Me.btnAccessSFEstimate.Name = "btnAccessSFEstimate"
        Me.btnAccessSFEstimate.Size = New System.Drawing.Size(59, 52)
        Me.btnAccessSFEstimate.TabIndex = 7
        Me.btnAccessSFEstimate.UseVisualStyleBackColor = False
        '
        'btnAccessOpportunity
        '
        Me.btnAccessOpportunity.BackColor = System.Drawing.Color.Transparent
        Me.btnAccessOpportunity.Image = Global.My.Resources.Resources.Opportunity
        Me.btnAccessOpportunity.Location = New System.Drawing.Point(191, 12)
        Me.btnAccessOpportunity.Name = "btnAccessOpportunity"
        Me.btnAccessOpportunity.Size = New System.Drawing.Size(59, 52)
        Me.btnAccessOpportunity.TabIndex = 6
        Me.btnAccessOpportunity.UseVisualStyleBackColor = False
        '
        'btnReadFromSF
        '
        Me.btnReadFromSF.BackColor = System.Drawing.Color.Transparent
        Me.btnReadFromSF.Image = Global.My.Resources.Resources.SF2QDV
        Me.btnReadFromSF.Location = New System.Drawing.Point(12, 12)
        Me.btnReadFromSF.Name = "btnReadFromSF"
        Me.btnReadFromSF.Size = New System.Drawing.Size(164, 52)
        Me.btnReadFromSF.TabIndex = 5
        Me.btnReadFromSF.UseVisualStyleBackColor = False
        '
        'btnSendToSF
        '
        Me.btnSendToSF.BackColor = System.Drawing.Color.Transparent
        Me.btnSendToSF.Image = Global.My.Resources.Resources.QDV2SF
        Me.btnSendToSF.Location = New System.Drawing.Point(12, 70)
        Me.btnSendToSF.Name = "btnSendToSF"
        Me.btnSendToSF.Size = New System.Drawing.Size(164, 52)
        Me.btnSendToSF.TabIndex = 0
        Me.btnSendToSF.UseVisualStyleBackColor = False
        '
        'lblOpportunity
        '
        Me.lblOpportunity.AutoSize = True
        Me.lblOpportunity.Location = New System.Drawing.Point(12, 125)
        Me.lblOpportunity.Name = "lblOpportunity"
        Me.lblOpportunity.Size = New System.Drawing.Size(71, 13)
        Me.lblOpportunity.TabIndex = 9
        Me.lblOpportunity.Text = "Opportunité : "
        '
        'lblEstimate
        '
        Me.lblEstimate.AutoSize = True
        Me.lblEstimate.Location = New System.Drawing.Point(12, 142)
        Me.lblEstimate.Name = "lblEstimate"
        Me.lblEstimate.Size = New System.Drawing.Size(43, 13)
        Me.lblEstimate.TabIndex = 10
        Me.lblEstimate.Text = "Devis : "
        '
        'FrmChoice
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(6.0!, 13.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.BackColor = System.Drawing.Color.Silver
        Me.ClientSize = New System.Drawing.Size(262, 161)
        Me.Controls.Add(Me.lblEstimate)
        Me.Controls.Add(Me.lblOpportunity)
        Me.Controls.Add(Me.btnClose)
        Me.Controls.Add(Me.btnAccessSFEstimate)
        Me.Controls.Add(Me.btnAccessOpportunity)
        Me.Controls.Add(Me.btnReadFromSF)
        Me.Controls.Add(Me.btnSendToSF)
        Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.None
        Me.MaximizeBox = False
        Me.MinimizeBox = False
        Me.Name = "FrmChoice"
        Me.ShowIcon = False
        Me.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent
        Me.Text = "FrmChoice"
        Me.ResumeLayout(False)
        Me.PerformLayout()

    End Sub

    Friend WithEvents btnSendToSF As System.Windows.Forms.Button
    Friend WithEvents btnReadFromSF As System.Windows.Forms.Button
    Friend WithEvents btnAccessOpportunity As System.Windows.Forms.Button
    Friend WithEvents btnAccessSFEstimate As System.Windows.Forms.Button
    Friend WithEvents btnClose As System.Windows.Forms.Button
    Friend WithEvents lblOpportunity As System.Windows.Forms.Label
    Friend WithEvents lblEstimate As System.Windows.Forms.Label
End Class
