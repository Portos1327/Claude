Imports Microsoft.VisualBasic
Imports System.Drawing
Imports System.Windows.Forms

Namespace QDV_Macro

    <Microsoft.VisualBasic.CompilerServices.DesignerGeneratedAttribute()>
    Partial Public Class PromptSFOperation
        Inherits System.Windows.Forms.Form

        Public WithEvents button2 As System.Windows.Forms.Button

        Public WithEvents textBox1 As System.Windows.Forms.TextBox

        Public WithEvents label1 As System.Windows.Forms.Label

        Public WithEvents button1 As System.Windows.Forms.Button

        Private components As System.ComponentModel.IContainer = Nothing

        Protected Overrides Sub Dispose(ByVal disposing As Boolean)
            If disposing Then
                If (Me.components Is Nothing) Then
                Else
                    Me.components.Dispose()
                End If
            End If
            MyBase.Dispose(disposing)
        End Sub

        Private Sub InitializeComponent()
            Me.button2 = New System.Windows.Forms.Button()
            Me.textBox1 = New System.Windows.Forms.TextBox()
            Me.label1 = New System.Windows.Forms.Label()
            Me.button1 = New System.Windows.Forms.Button()
            Me.SuspendLayout()
            '
            'button2
            '
            Me.button2.DialogResult = System.Windows.Forms.DialogResult.Cancel
            Me.button2.Location = New System.Drawing.Point(175, 64)
            Me.button2.Name = "button2"
            Me.button2.Size = New System.Drawing.Size(97, 23)
            Me.button2.TabIndex = 2
            Me.button2.Text = "&Annuler"
            Me.button2.UseVisualStyleBackColor = True
            '
            'textBox1
            '
            Me.textBox1.Location = New System.Drawing.Point(12, 23)
            Me.textBox1.Name = "textBox1"
            Me.textBox1.Size = New System.Drawing.Size(260, 20)
            Me.textBox1.TabIndex = 0
            '
            'label1
            '
            Me.label1.Location = New System.Drawing.Point(12, 3)
            Me.label1.Name = "label1"
            Me.label1.Size = New System.Drawing.Size(175, 17)
            Me.label1.TabIndex = 3
            Me.label1.Text = "Numéro Sales Force :"
            '
            'button1
            '
            Me.button1.DialogResult = System.Windows.Forms.DialogResult.Cancel
            Me.button1.Location = New System.Drawing.Point(12, 64)
            Me.button1.Name = "button1"
            Me.button1.Size = New System.Drawing.Size(97, 23)
            Me.button1.TabIndex = 4
            Me.button1.Text = "&Ok"
            Me.button1.UseVisualStyleBackColor = True
            '
            'PromptSFOperation
            '
            Me.AcceptButton = Me.button1
            Me.CancelButton = Me.button2
            Me.ClientSize = New System.Drawing.Size(284, 99)
            Me.Controls.Add(Me.button1)
            Me.Controls.Add(Me.label1)
            Me.Controls.Add(Me.textBox1)
            Me.Controls.Add(Me.button2)
            Me.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedToolWindow
            Me.Name = "PromptSFOperation"
            Me.StartPosition = System.Windows.Forms.FormStartPosition.CenterParent
            Me.Text = "Connexion à Sales Force"
            Me.ResumeLayout(False)
            Me.PerformLayout()

        End Sub
    End Class
End Namespace

