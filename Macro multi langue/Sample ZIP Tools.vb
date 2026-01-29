Imports System
Imports System.IO
Imports System.Windows.Forms
Imports System.Collections.Generic
Imports Microsoft.VisualBasic
Imports SpreadsheetGear
Imports SpreadsheetGear.Advanced.Cells
Imports Qdv.CommonApi
Imports Qdv.UserApi

'YOU MUST KEEP QDV_Macro AS NAMESPACE'S NAME
Namespace QDV_Macro

	Public Class Startup

		Public Shared Sub EntryMethod(ByVal Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext)

			Try 'This is recommended to catch all errors to deliver proper error messages

				Dim response As MsgBoxResult = msgbox("With this sample macro, you can either compress or expand a file. Check API documentation for extended features of these functions (expanding multiple files, managing passwords, etc.)." & vbcrlf & vbcrlf & "Do you want to compress?", MsgBoxStyle.YesNoCancel, "Compress?")
				Select Case response
					Case MsgBoxResult.Yes
						Dim openFileDialog1 As New OpenFileDialog()
						openFileDialog1.Title = "Select file to be compressed..."
						openFileDialog1.Filter = "All files (*.*)|*.*"
						openFileDialog1.FilterIndex = 1
						openFileDialog1.RestoreDirectory = False
						If openFileDialog1.ShowDialog() = System.Windows.Forms.DialogResult.OK Then
							Dim saveFileDialog1 As New SaveFileDialog()
							openFileDialog1.Title = "Select archive to be created..."
							saveFileDialog1.Filter = "Compressed files (*.zip)|*.zip"
							saveFileDialog1.FilterIndex = 1
							saveFileDialog1.RestoreDirectory = False
							If saveFileDialog1.ShowDialog() = DialogResult.OK Then
								Try
									Context.QdvManager.ZipFileManager.CompressFilesToZip(openFileDialog1.FileName, saveFileDialog1.FileName)
									MsgBox("Compression OK!", MsgBoxStyle.Information, "")
								Catch Ex As Exception
									MsgBox("An error occured while compressing!" & vbCrLf & vbcrlf & Ex.Message, MsgBoxStyle.Exclamation, "")
								End Try
							End If
						End If
					Case MsgBoxResult.No
						Dim openFileDialog1 As New OpenFileDialog()
						openFileDialog1.Title = "Selection archive you want to expand..."
						openFileDialog1.Filter = "Compressed files (*.zip)|*.zip"
						openFileDialog1.FilterIndex = 1
						openFileDialog1.RestoreDirectory = False
						If openFileDialog1.ShowDialog() = System.Windows.Forms.DialogResult.OK Then
							Dim saveFileDialog1 As New SaveFileDialog()
							openFileDialog1.Title = "Select file to be expanded to..."
							saveFileDialog1.Filter = "All files (*.*)|*.*"
							saveFileDialog1.FilterIndex = 1
							saveFileDialog1.RestoreDirectory = False
							If saveFileDialog1.ShowDialog() = DialogResult.OK Then
								Try
									Context.QdvManager.ZipFileManager.ExtractZip(openFileDialog1.FileName, saveFileDialog1.FileName)
									MsgBox("Expansion OK!", MsgBoxStyle.Information, "")
								Catch Ex As Exception
									MsgBox("An error occured while expanding!" & vbCrLf & vbcrlf & Ex.Message, MsgBoxStyle.Exclamation, "")
								End Try
							End If
						End If
					Case Else
						Exit Sub
				End Select

			Catch GeneralError As Exception 'Catches all error to get proper message

				MessageBox.Show(GeneralError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error)

				Context.MustCancel = True 'Cancel the event if it is called through an event

			End Try

		End Sub

	End Class

End Namespace
