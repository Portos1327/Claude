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

				Dim TempFile As String = System.IO.Path.GetTempFileName & ".txt"
				Dim sw As New System.IO.StreamWriter(TempFile)
				
				Dim WBS As IWbs = Es.CurrentVersion.Wbs
				Dim Tasks As List(Of ITask) = WBS.GetTasksForScope("", True)
				For Each MyTask As ITask In Tasks
					'Get description of WBS
					Dim Description As String = MyTask.GetFieldValue("WBS_Description", PositionInWbsBranch.Top).Tostring.Replace(chr(10), "").Replace(Chr(13), "")
					'Get unit of WBS
					Dim Unit As String = MyTask.GetFieldValue("WBS_Unit", PositionInWbsBranch.Bottom).Tostring.Replace(chr(10), "").Replace(Chr(13), "")
					'Note that you could get both fields at once by reading directly the db using GetFieldsValuesFromDb. This is faster but only fields stored in db are accessibles, not those calculated in the WBS workbook.
					sw.WriteLine(Description & "|" & Unit)
					If not isnothing(MyTask.Minute) then
						Dim MyMinute As IMinute = MyTask.Minute
						Dim MaxRow As Integer = MyMinute.GetRowsCount
						'Get image of minute for two fields
						Dim FieldsToGet As New list(of String)
						FieldsToGet.Add("Description")
						FieldsToGet.Add("Unit")
						'Get description and unit from minute for all rows
						Dim ImageOfMinute As dictionary(of String, dictionary(of Integer, Object)) = MyMinute.GetFieldsValues(1, MaxRow, FieldsToGet, False) 'Notice that we could collapse groups here
						Dim AllDescriptions As Dictionary(of Integer, Object) = ImageOfMinute("Description")
						Dim AllUnits As Dictionary(of Integer, Object) = ImageOfMinute("Unit")
						For i As Integer = 0 to MaxRow - 1
							Dim MinuteDescription As String = AllDescriptions(i).ToString.Replace(chr(10), "").Replace(Chr(13), "")
							Dim Minuteunit As String = AllUnits(i).ToString.Replace(chr(10), "").Replace(Chr(13), "")
							sw.WriteLine("             " & MinuteDescription & "|" & MinuteUnit)
						Next
					End If
				Next

				sw.Close
				System.Diagnostics.Process.Start(TempFile)

			Catch GeneralError As Exception 'Catches all error to get proper message

				MessageBox.Show(GeneralError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error)

				Context.MustCancel = True 'Cancel the event if it is called through an event

			End Try

		End Sub

	End Class

End Namespace
