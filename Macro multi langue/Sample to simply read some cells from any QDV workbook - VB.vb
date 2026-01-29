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
                MessageBox.Show("This macro demonstrates how to read some cells from the overhead without acquiring a lock on the workbook! Two approaches will be presented.", "Demo", MessageBoxButtons.OK, MessageBoxIcon.Information)

                '*******************
                ' Approach 1.
                ' Suitable, if you only want to read few cells. It is slower when you want to read many cells.
                ' Moreover, the GetCellValueFromWorkbook method below can only find the worksheet by its LOCALIZED name.
                ' This is the localized name that is displayed in QDV tab name. So it may be different in other languages!
                ' Therefore, this approach with hard-coded localized name may work in one language, but it will fail in another one.

                ' Read a few cells from the Sheet of Sales, using ranges.
                Dim title1 = Convert.ToString(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "B11"))
                Dim value1 = Convert.ToDouble(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "E25"))
                Dim title2 = Convert.ToString(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "B26"))
                Dim value2 = Convert.ToDouble(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "E31"))
                Dim title3 = Convert.ToString(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "B32"))
                Dim value3 = Convert.ToDouble(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "E41"))
                Dim title4 = Convert.ToString(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "B42"))
                Dim value4 = Convert.ToDouble(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", "E46"))
                ' You may also want to address the cell using Row/Column instead of range. Keep in mind that you must use base 0.
                Dim title5 = Convert.ToString(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", 46, 1)) ' stands for B47
                Dim value5 = Convert.ToDouble(Es.CurrentVersion.Overhead.GetCellValueFromWorkbook("Sheet of Sales", 50, 4)) ' stands for E51

                MessageBox.Show($"{title1}: {value1}
{title2}: {value2}
{title3}: {value3}
{title4}: {value4}
{title5}: {value5}", "APPOACH 1 - Read from 'Sheet of Sales'", MessageBoxButtons.OK, MessageBoxIcon.Information)

                '*******************
                ' Approach 2.
                ' Faster when you want to read many cells.
                ' And it allows for using the language neutral ID of the overhead sheet. So it will work for estimates in any QDV language.

                ' Get the overhead workbook in the readonly mode. No locking required.
                Dim wbParams = New WorkbookParameters()
                wbParams.KeepProtected = True
                wbParams.KeepFormulas = True
                Dim overheadWorkbook = Es.CurrentVersion.Overhead.GetReadOnlyCopyOfWorkbook(wbParams)

                ' Get the 'Sheet of Sales' sheet by its language neutral ID, which is "Sheet of Sales".
                ' You can display all sheet language neutral IDs with the following line:
                'DisplayAllOverheadSheetNamesAndIDs(es, overheadWorkbook);
                Dim wsheet = GetOverheadSheetByNeutralName(Es, overheadWorkbook, "Sheet of Sales")

                If wsheet IsNot Nothing Then
                    ' Read a few cells from the Sheet of Sales, using ranges.
                    title1 = Convert.ToString(wsheet.Cells("B11").Value)
                    value1 = Convert.ToDouble(wsheet.Cells("E25").Value)
                    title2 = Convert.ToString(wsheet.Cells("B26").Value)
                    value2 = Convert.ToDouble(wsheet.Cells("E31").Value)
                    title3 = Convert.ToString(wsheet.Cells("B32").Value)
                    value3 = Convert.ToDouble(wsheet.Cells("E41").Value)
                    title4 = Convert.ToString(wsheet.Cells("B42").Value)
                    value4 = Convert.ToDouble(wsheet.Cells("E46").Value)
                    ' You may also want to address the cell using Row/Column instead of range. Keep in mind that you must use base 0.
                    title5 = Convert.ToString(wsheet.Cells(46, 1).Value) ' stands for B47
                    value5 = Convert.ToDouble(wsheet.Cells(50, 4).Value) ' stands for E51

                    MessageBox.Show($"{title1}: {value1}
{title2}: {value2}
{title3}: {value3}
{title4}: {value4}
{title5}: {value5}", "APPOACH 2 - Read from 'Sheet of Sales'", MessageBoxButtons.OK, MessageBoxIcon.Information)
                End If

            Catch generalError As Exception
                ' Catch all errors to get the proper message.
                MessageBox.Show(generalError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error)

                ' Cancel the event if the macro is called through an event. But don't do this, if it's called
                ' from an "On_Open_Estimate" event. Otherwise, it will prevent from opening the estimate and fixing the macro.
                Context.MustCancel = True
            End Try

        End Sub


        ''' <summary>
        ''' Gets the overhead sheet by its language neutral name (ID).
        ''' </summary>
        ''' <param name="overheadWorkbook"></param>
        ''' <param name="neutralName">The language neutral name to find.</param>
        ''' <returns>
        ''' The worksheet that was found or null if none.
        ''' </returns>
        Private Shared Function GetOverheadSheetByNeutralName(es As IEstimate, overheadWorkbook As IWorkbook, neutralName As String) As IWorksheet
            For Each wsheet As IWorksheet In overheadWorkbook.Worksheets
                Dim info = es.CurrentVersion.Overhead.WorksheetManager.GetOverheadSheetInformation(wsheet)
                If Equals(info.Name, neutralName) Then
                    Return wsheet
                End If
            Next
            Return Nothing
        End Function


        ''' <summary>
        ''' Displays all overhead sheet names and their corresponding language neutral names (IDs).
        ''' </summary>
        ''' <param name="overheadWorkbook"></param>
        ''' <remarks>
        ''' For diagnostic purposes.
        ''' </remarks>
        Private Shared Function DisplayAllOverheadSheetNamesAndIDs(es As IEstimate, overheadWorkbook As IWorkbook) As String
            Dim str = ""
            For Each wsheet As IWorksheet In overheadWorkbook.Worksheets
                Dim info = es.CurrentVersion.Overhead.WorksheetManager.GetOverheadSheetInformation(wsheet)
                str += $"{info.LocalizedName}: {info.Name}
"
            Next
            MessageBox.Show(str, "Overhead sheets", MessageBoxButtons.OK, MessageBoxIcon.Information)
            Return str
        End Function


    End Class

End Namespace
