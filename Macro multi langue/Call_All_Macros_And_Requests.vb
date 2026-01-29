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

	' DO NOT REMOVE OR CHANGE THE NAME OF THE Startup CLASS
	' YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED
	' Es is the calling estimate. When the macro is not attached to an estimate, Es is set to Nothing
	Public Class Startup

		' DO NOT REMOVE OR CHANGE THE SIGNATURE OF THE EntryMethod METHOD
		' YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED
		' If you want your macro to be compatible with older versions – before 7.12.445,
		' you can switch to the legacy API format by removing all occurrences of the 'Qdv.UserApi' text in the macro
		' and by replacing the signature with this one:
		' Public Shared Sub EntryMethod(ByRef Es As QDVUserAPI.QDVEstimate, ByRef Context as QDVUserAPI.QDVAPIFunctions.CallingContext)
		Public Shared Sub EntryMethod(ByVal Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext)

			Try 'This is recommended to catch all errors to deliver proper error messages

				'This is the entry point of your macro
				'You can add your code here below...
				Dim myForm As New MainForm(Es, Context)
				myForm.ShowDialog

			Catch GeneralError As Exception 'Catches all error to get proper message

				MessageBox.Show(GeneralError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error)

				Context.MustCancel = True 'Cancel the event if it is called through an event

			End Try

		End Sub

	End Class

End Namespace
