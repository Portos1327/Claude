Imports System
Imports System.Windows.Forms
Imports System.Collections.Generic
Imports Microsoft.VisualBasic
Imports SpreadsheetGear
Imports SpreadsheetGear.Advanced.Cells
Imports Qdv.CommonApi
Imports Qdv.UserApi
Imports Qdv.UserApi.DistributionCurves
Imports Qdv.UserApi.Fields
Imports Qdv.UserApi.Profiles


'DO NOT REMOVE OR CHANGE THE NAME OF QDV_Macro NAMESPACE
Namespace QDV_Macro


	''' <summary>
	''' The main class of the macro.
	''' </summary>
	''' <devdoc>
	''' DO NOT REMOVE OR CHANGE THE NAME OF Startup CLASS!
	''' YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED.
	''' </devdoc>
	Public Class Startup

		''' <summary>
		''' The entry point of the macro. This method is called when the macro is started.
		''' </summary>
		''' <param name="Es">The calling estimate. When the macro is not attached to an estimate, this parameter is <see langword="Nothing"/>.</param>
		''' <param name="context">The information about a context in which the macro is being executed.</param>
		''' <devdoc>
		''' DO NOT REMOVE OR CHANGE THE SIGNATURE OF EntryMethod METHOD!
		''' YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED.
		''' </devdoc>
		Public Shared Sub EntryMethod(ByVal Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext)

			Try
				'Open the window with functions.
				Dim FunctWindow = New FormTest(Es)
				FunctWindow.ShowDialog()

			Catch generalError As Exception
				' Catch all errors to get the proper message.
				MessageBox.Show(generalError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error)

				' Cancel the event if the macro is called through an event. But don't do this, if it's called
				' from an "On_Open_Estimate" event. Otherwise, it will prevent from opening the estimate and fixing the macro.
				Context.MustCancel = True
			End Try

		End Sub

	End Class

End Namespace