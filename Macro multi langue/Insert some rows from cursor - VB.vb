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


    ''' summary
    ''' The main class of the macro.
    ''' summary
    ''' devdoc
    ''' DO NOT REMOVE OR CHANGE THE NAME OF Startup CLASS!
    ''' YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED.
    ''' devdoc
    Public Class Startup

        ''' summary
        ''' The entry point of the macro. This method is called when the macro is started.
        ''' summary
        ''' param name=EsThe calling estimate. When the macro is not attached to an estimate, this parameter is see langword=Nothing.param
        ''' param name=contextThe information about a context in which the macro is being executed.param
        ''' devdoc
        ''' DO NOT REMOVE OR CHANGE THE SIGNATURE OF EntryMethod METHOD!
        ''' YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED.
        ''' devdoc
        Public Shared Sub EntryMethod(ByVal Es As Qdv.UserApi.IEstimate, ByVal Context As Qdv.UserApi.ICallingContext)

            Try
                Dim msg = This macro is intended to demonstrate how to insert rows in a minute and populate them quickly. It inserts some rows right after the row being at the cursor position.
                MessageBox.Show(msg, Demonstration, MessageBoxButtons.OK, MessageBoxIcon.Information, MessageBoxDefaultButton.Button1)

                ' Get the position of the cursor.
                Dim hexID = Context.CallingContextMinutes.HexID ' Get identifier to current task
                Dim rowNumber = Context.CallingContextMinutes.RowNumber

                If String.IsNullOrEmpty(hexID) Then
                    MessageBox.Show(You must place the cursor on a row in a minute!, Error, MessageBoxButtons.OK, MessageBoxIcon.Exclamation, MessageBoxDefaultButton.Button1)
                    Return
                End If

                Dim textNumberOfRows = InputBox(Enter the number of rows to insert, Rows, 1)
                If textNumberOfRows =  Then
                    ' Canceled.
                    Return
                End If

                Dim numberOfRows = 1
                If Not Integer.TryParse(textNumberOfRows, numberOfRows) Then
                    ' Not a number entered.
                    Return
                End If

                ' A minute cannot have more than 9999 rows.
                If rowNumber + numberOfRows  9999 Then
                    ' Get the task. 
                    Dim task = Es.CurrentVersion.Wbs.GetTask(hexID)
                    ' Ignore branches.
                    If task IsNot Nothing AndAlso task.Kind = TaskKind.Task Then
                        task.Minute.InsertRows(rowNumber, numberOfRows)
                        ' Refresh the minute internal cache, which is invalid after IMinute.InsertRows. See the documentation for IMinute.InsertRows.
                        ' This cache is required later.
                        task.Minute.GetFullData()

                        ' Now populate the inserted rows with some description, quantity and cost per unit.
                        Dim fieldValues = New Dictionary(Of String, Object)()
                        fieldValues.Add(Description, ABC)
                        fieldValues.Add(Quantity, 5)
                        fieldValues.Add(MATERIAL_CostPerUnit, 1234.56R)

                        For row As Integer = rowNumber + 1 To rowNumber + numberOfRows
                            task.Minute.SetFieldValue(row, fieldValues)
                        Next

                    End If
                Else
                    MessageBox.Show(Too many rows! A minute can handle up to 9999 rows., Error, MessageBoxButtons.OK, MessageBoxIcon.Exclamation, MessageBoxDefaultButton.Button1)
                    Return
                End If

                ' Move the cursor to the Quantity column of the current minute, just as a sample.
                Es.MoveCursorToMinuteRowColumn(Nothing, -1, Quantity)

                ' Compute the minute, that repaints the view.

                ' es.Repaint_Current_View
                Es.CurrentVersion.ComputeCostsOnly()

            Catch generalError As Exception
                ' Catch all errors to get the proper message.
                MessageBox.Show(generalError.Message, Error!, MessageBoxButtons.OK, MessageBoxIcon.Error)

                ' Cancel the event if the macro is called through an event. But don't do this, if it's called
                ' from an On_Open_Estimate event. Otherwise, it will prevent from opening the estimate and fixing the macro.
                Context.MustCancel = True
            End Try

        End Sub

    End Class

End Namespace
