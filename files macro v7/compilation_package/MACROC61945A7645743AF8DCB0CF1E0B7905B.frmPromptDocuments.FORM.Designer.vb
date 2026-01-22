<Global.Microsoft.VisualBasic.CompilerServices.DesignerGenerated()>
Partial Class frmPromptDocuments
    Inherits System.Windows.Forms.Form

    'Form remplace la méthode Dispose pour nettoyer la liste des composants.
    <System.Diagnostics.DebuggerNonUserCode()>
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
    <System.Diagnostics.DebuggerStepThrough()>
    Private Sub InitializeComponent()
        Dim resources As System.ComponentModel.ComponentResourceManager = New System.ComponentModel.ComponentResourceManager(GetType(frmPromptDocuments))
        Me.lblCommercialOffer = New System.Windows.Forms.Label()
        Me.lblTechnicalOffer = New System.Windows.Forms.Label()
        Me.lblOverhead = New System.Windows.Forms.Label()
        Me.lblWBS = New System.Windows.Forms.Label()
        Me.txtCommercialOffer = New System.Windows.Forms.TextBox()
        Me.txtwbs = New System.Windows.Forms.TextBox()
        Me.txtOverhead = New System.Windows.Forms.TextBox()
        Me.txtTechnicalOffer = New System.Windows.Forms.TextBox()
        Me.btnCommercialOffer = New System.Windows.Forms.Button()
        Me.btnWbs = New System.Windows.Forms.Button()
        Me.btnOverhead = New System.Windows.Forms.Button()
        Me.btnTechnicalOffer = New System.Windows.Forms.Button()
        Me.btnOK = New System.Windows.Forms.Button()
        Me.btnCancel = New System.Windows.Forms.Button()
        Me.rbnDefaultWord = New System.Windows.Forms.RadioButton()
        Me.rbnSelection = New System.Windows.Forms.RadioButton()
        Me.SuspendLayout()
        '
        'lblCommercialOffer
        '
        Me.lblCommercialOffer.AutoSize = True
        Me.lblCommercialOffer.Location = New System.Drawing.Point(7, 51)
        Me.lblCommercialOffer.Name = "lblCommercialOffer"
        Me.lblCommercialOffer.Size = New System.Drawing.Size(122, 13)
        Me.lblCommercialOffer.TabIndex = 0
        Me.lblCommercialOffer.Text = "Offre commerciale (pdf) :"
        '
        'lblTechnicalOffer
        '
        Me.lblTechnicalOffer.AutoSize = True
        Me.lblTechnicalOffer.Location = New System.Drawing.Point(7, 77)
        Me.lblTechnicalOffer.Name = "lblTechnicalOffer"
        Me.lblTechnicalOffer.Size = New System.Drawing.Size(110, 13)
        Me.lblTechnicalOffer.TabIndex = 1
        Me.lblTechnicalOffer.Text = "Offre technique (pdf) :"
        '
        'lblOverhead
        '
        Me.lblOverhead.AutoSize = True
        Me.lblOverhead.Location = New System.Drawing.Point(7, 106)
        Me.lblOverhead.Name = "lblOverhead"
        Me.lblOverhead.Size = New System.Drawing.Size(114, 13)
        Me.lblOverhead.TabIndex = 2
        Me.lblOverhead.Text = "Feuille de marge (pdf) :"
        '
        'lblWBS
        '
        Me.lblWBS.AutoSize = True
        Me.lblWBS.Location = New System.Drawing.Point(7, 137)
        Me.lblWBS.Name = "lblWBS"
        Me.lblWBS.Size = New System.Drawing.Size(77, 13)
        Me.lblWBS.TabIndex = 3
        Me.lblWBS.Text = "DPGF (Excel) :"
        '
        'txtCommercialOffer
        '
        Me.txtCommercialOffer.Enabled = False
        Me.txtCommercialOffer.Location = New System.Drawing.Point(129, 47)
        Me.txtCommercialOffer.Name = "txtCommercialOffer"
        Me.txtCommercialOffer.Size = New System.Drawing.Size(324, 20)
        Me.txtCommercialOffer.TabIndex = 4
        '
        'txtwbs
        '
        Me.txtwbs.Enabled = False
        Me.txtwbs.Location = New System.Drawing.Point(129, 133)
        Me.txtwbs.Name = "txtwbs"
        Me.txtwbs.Size = New System.Drawing.Size(324, 20)
        Me.txtwbs.TabIndex = 5
        '
        'txtOverhead
        '
        Me.txtOverhead.Enabled = False
        Me.txtOverhead.Location = New System.Drawing.Point(129, 102)
        Me.txtOverhead.Name = "txtOverhead"
        Me.txtOverhead.Size = New System.Drawing.Size(324, 20)
        Me.txtOverhead.TabIndex = 6
        '
        'txtTechnicalOffer
        '
        Me.txtTechnicalOffer.Enabled = False
        Me.txtTechnicalOffer.Location = New System.Drawing.Point(129, 73)
        Me.txtTechnicalOffer.Name = "txtTechnicalOffer"
        Me.txtTechnicalOffer.Size = New System.Drawing.Size(324, 20)
        Me.txtTechnicalOffer.TabIndex = 7
        '
        'btnCommercialOffer
        '
        Me.btnCommercialOffer.BackColor = System.Drawing.Color.Transparent
        Me.btnCommercialOffer.Enabled = False
        Me.btnCommercialOffer.Image = CType(resources.GetObject("btnCommercialOffer.Image"), System.Drawing.Image)
        Me.btnCommercialOffer.Location = New System.Drawing.Point(457, 46)
        Me.btnCommercialOffer.Name = "btnCommercialOffer"
        Me.btnCommercialOffer.Size = New System.Drawing.Size(20, 20)
        Me.btnCommercialOffer.TabIndex = 8
        Me.btnCommercialOffer.Text = " "
        Me.btnCommercialOffer.UseVisualStyleBackColor = False
        '
        'btnWbs
        '
        Me.btnWbs.Enabled = False
        Me.btnWbs.Image = CType(resources.GetObject("btnWbs.Image"), System.Drawing.Image)
        Me.btnWbs.Location = New System.Drawing.Point(458, 132)
        Me.btnWbs.Name = "btnWbs"
        Me.btnWbs.Size = New System.Drawing.Size(20, 20)
        Me.btnWbs.TabIndex = 9
        Me.btnWbs.Text = " "
        Me.btnWbs.UseVisualStyleBackColor = True
        '
        'btnOverhead
        '
        Me.btnOverhead.Enabled = False
        Me.btnOverhead.Image = CType(resources.GetObject("btnOverhead.Image"), System.Drawing.Image)
        Me.btnOverhead.Location = New System.Drawing.Point(457, 101)
        Me.btnOverhead.Name = "btnOverhead"
        Me.btnOverhead.Size = New System.Drawing.Size(20, 20)
        Me.btnOverhead.TabIndex = 10
        Me.btnOverhead.Text = " "
        Me.btnOverhead.UseVisualStyleBackColor = True
        '
        'btnTechnicalOffer
        '
        Me.btnTechnicalOffer.Enabled = False
        Me.btnTechnicalOffer.Image = CType(resources.GetObject("btnTechnicalOffer.Image"), System.Drawing.Image)
        Me.btnTechnicalOffer.Location = New System.Drawing.Point(457, 72)
        Me.btnTechnicalOffer.Name = "btnTechnicalOffer"
        Me.btnTechnicalOffer.Size = New System.Drawing.Size(20, 20)
        Me.btnTechnicalOffer.TabIndex = 11
        Me.btnTechnicalOffer.Text = " "
        Me.btnTechnicalOffer.UseVisualStyleBackColor = True
        '
        'btnOK
        '
        Me.btnOK.Location = New System.Drawing.Point(187, 172)
        Me.btnOK.Name = "btnOK"
        Me.btnOK.Size = New System.Drawing.Size(75, 23)
        Me.btnOK.TabIndex = 12
        Me.btnOK.Text = "OK"
        Me.btnOK.UseVisualStyleBackColor = True
        '
        'btnCancel
        '
        Me.btnCancel.Location = New System.Drawing.Point(277, 172)
        Me.btnCancel.Name = "btnCancel"
        Me.btnCancel.Size = New System.Drawing.Size(75, 23)
        Me.btnCancel.TabIndex = 13
        Me.btnCancel.Text = "Annuler"
        Me.btnCancel.UseVisualStyleBackColor = True
        '
        'rbnDefaultWord
        '
        Me.rbnDefaultWord.AutoSize = True
        Me.rbnDefaultWord.Location = New System.Drawing.Point(61, 12)
        Me.rbnDefaultWord.Name = "rbnDefaultWord"
        Me.rbnDefaultWord.Size = New System.Drawing.Size(176, 17)
        Me.rbnDefaultWord.TabIndex = 16
        Me.rbnDefaultWord.TabStop = True
        Me.rbnDefaultWord.Text = "Envoyer le document par défaut"
        Me.rbnDefaultWord.UseVisualStyleBackColor = True
        '
        'rbnSelection
        '
        Me.rbnSelection.AutoSize = True
        Me.rbnSelection.Location = New System.Drawing.Point(267, 12)
        Me.rbnSelection.Name = "rbnSelection"
        Me.rbnSelection.Size = New System.Drawing.Size(173, 17)
        Me.rbnSelection.TabIndex = 17
        Me.rbnSelection.TabStop = True
        Me.rbnSelection.Text = "Envoyer la sélection ci-dessous"
        Me.rbnSelection.UseVisualStyleBackColor = True
        '
        'frmPromptDocuments
        '
        Me.AutoScaleDimensions = New System.Drawing.SizeF(6.0!, 13.0!)
        Me.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font
        Me.ClientSize = New System.Drawing.Size(497, 197)
        Me.ControlBox = False
        Me.Controls.Add(Me.rbnSelection)
        Me.Controls.Add(Me.rbnDefaultWord)
        Me.Controls.Add(Me.btnCancel)
        Me.Controls.Add(Me.btnOK)
        Me.Controls.Add(Me.btnTechnicalOffer)
        Me.Controls.Add(Me.btnOverhead)
        Me.Controls.Add(Me.btnWbs)
        Me.Controls.Add(Me.btnCommercialOffer)
        Me.Controls.Add(Me.txtTechnicalOffer)
        Me.Controls.Add(Me.txtOverhead)
        Me.Controls.Add(Me.txtwbs)
        Me.Controls.Add(Me.txtCommercialOffer)
        Me.Controls.Add(Me.lblWBS)
        Me.Controls.Add(Me.lblOverhead)
        Me.Controls.Add(Me.lblTechnicalOffer)
        Me.Controls.Add(Me.lblCommercialOffer)
        Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle
        Me.MaximizeBox = False
        Me.Name = "frmPromptDocuments"
        Me.ShowIcon = False
        Me.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent
        Me.Text = "Documents associés"
        Me.ResumeLayout(False)
        Me.PerformLayout()

    End Sub

    Friend WithEvents lblCommercialOffer As System.Windows.Forms.Label
    Friend WithEvents lblTechnicalOffer As System.Windows.Forms.Label
    Friend WithEvents lblOverhead As System.Windows.Forms.Label
    Friend WithEvents lblWBS As System.Windows.Forms.Label
    Friend WithEvents txtCommercialOffer As System.Windows.Forms.TextBox
    Friend WithEvents txtwbs As System.Windows.Forms.TextBox
    Friend WithEvents txtOverhead As System.Windows.Forms.TextBox
    Friend WithEvents txtTechnicalOffer As System.Windows.Forms.TextBox
    Friend WithEvents btnCommercialOffer As System.Windows.Forms.Button
    Friend WithEvents btnWbs As System.Windows.Forms.Button
    Friend WithEvents btnOverhead As System.Windows.Forms.Button
    Friend WithEvents btnTechnicalOffer As System.Windows.Forms.Button
    Friend WithEvents btnOK As System.Windows.Forms.Button
    Friend WithEvents btnCancel As System.Windows.Forms.Button
    Friend WithEvents rbnDefaultWord As System.Windows.Forms.RadioButton
    Friend WithEvents rbnSelection As System.Windows.Forms.RadioButton
End Class
