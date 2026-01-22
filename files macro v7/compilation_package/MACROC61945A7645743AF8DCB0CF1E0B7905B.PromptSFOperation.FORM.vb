Imports System.Drawing
Imports Microsoft.VisualBasic
Imports System.Windows.Forms
Imports Qdv.UserApi

Namespace QDV_Macro

	Partial Public Class PromptSFOperation
		Inherits System.Windows.Forms.Form

		Public _SalesForceID As String = ""

		Sub New(ByVal salesForceID As String)
			InitializeComponent()
			textBox1.Text = salesForceID
		End Sub

		Private Sub button1_Click(ByVal sender As Object, ByVal e As System.EventArgs) Handles button1.Click
			'	Dim sfTemp As String = textBox1.Text.Trim.Replace(" ", "")
			'	Dim wrongSFID As Boolean = False
			'	If Len(sfTemp) <> Len("YY-NNNNNNN") Then
			'		wrongSFID = True
			'	Else
			'		If sfTemp.Substring(2, 1) <> "-" Then
			'			wrongSFID = True		
			'		End If
			'	End If
			'	For i As Integer = 3 To sfTemp.Length - 1
			'		If asc(sfTemp.Substring(i, 1)) < 48 or asc(sfTemp.Substring(i, 1)) > 57 Then
			'			wrongSFID = True
			'			Exit For
			'		End If
			'	Next i
			'	For i As Integer = 0 To 1
			'		If asc(sfTemp.Substring(i, 1)) < 48 or asc(sfTemp.Substring(i, 1)) > 57 Then
			'			wrongSFID = True
			'			Exit For
			'		End If
			'	Next i
			'	If wrongSFID = True Then
			'		MsgBox("Un numéro Sales Force doit avoir la forme YY-NNNNNNN !", MsgBoxStyle.Exclamation, "Saisie invalide !")
			'		textBox1.Focus
			'		Exit Sub
			'	End If
			_SalesForceID = textBox1.Text.Trim
			Me.Close()
		End Sub

		Private Sub button2_Click(ByVal sender As Object, ByVal e As System.EventArgs) Handles button2.Click
			Me.Close()
		End Sub

	End Class

End Namespace

