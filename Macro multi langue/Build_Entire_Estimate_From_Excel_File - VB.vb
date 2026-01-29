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
Imports System.Linq


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
                Dim message As String = "This macro program demonstrates how to build an estimate WBS and associated minute rows starting from an Excel workbook in custom format." & vbCrLf
                message += "you can use file named Sample_Import_Structure.xlsx provided in <installation folder>\Samples\Stuff_4_Macros."

                MessageBox.Show(message, "Sample import structured workbook!", MessageBoxButtons.OK, MessageBoxIcon.Information)

                ' Prompt the user to select the source XLSX file.
                Dim openFileDialog1 = New OpenFileDialog()
                openFileDialog1.InitialDirectory = Application.StartupPath & "\Samples\Stuff_4_Macros"
                openFileDialog1.Filter = "xlsx files (*.xlsx)|*.xlsx"
                openFileDialog1.FilterIndex = 1

                If openFileDialog1.ShowDialog() <> DialogResult.OK Then
                    Return
                End If

                ' Open the file.
                Dim workbook = Factory.GetWorkbook(openFileDialog1.FileName)
                Dim worksheet = workbook.Worksheets(0)

                ' Empty the entire estimate.
                Es.CurrentVersion.EmptyCompleteEstimate()
                ' We need to refresh the WBS workbook in QDV and also our WBS internal info after emptying the estimate.
                Es.CheckAndRepaint()
                Es.CurrentVersion.Wbs.Refresh()
                ' Note that the empty estimate already contains one empty task A under the root.

                ' Prepare the tasks parent chain.
                Dim taskParentChain As List(Of ITask) = New List(Of ITask)()
                taskParentChain.Add(Es.CurrentVersion.Wbs.Root)    ' The parent chain starts with the root task.

                ' Browse the sheet.
                Dim lastUsedRowInSheet = worksheet.UsedRange.Row + worksheet.UsedRange.RowCount - 1
                For rowInSheet As Integer = 1 To lastUsedRowInSheet   ' Row 0 is just a header.
                    Dim level = Convert.ToInt32(worksheet.Cells(rowInSheet, 0).Value)
                    Dim item = worksheet.Cells(rowInSheet, 1).Text
                    Dim description = worksheet.Cells(rowInSheet, 2).Text
                    Dim unit = worksheet.Cells(rowInSheet, 3).Text
                    Dim quantity = Convert.ToDouble(worksheet.Cells(rowInSheet, 4).Value)
                    Dim cost = worksheet.Cells(rowInSheet, 5).Text
                    Dim reference = worksheet.Cells(rowInSheet, 6).Text

                    If level = 0 Then
                        ' This is a minute row. Insert it in the last created task (the last one in the parent chain).
                        Dim task As ITask = taskParentChain.Last()
                        If task.Kind = TaskKind.Task Then    ' the branch task cannot have minutes
                            ' Insert a new row.
                            Dim rowsCount As Integer = task.Minute.GetRowsCount()
                            ' There is always one empty minute row. It cannot be deleted. Keep it empty, as the last one.
                            Dim rowToInsertAfter = rowsCount - 1
                            task.Minute.InsertRows(rowToInsertAfter, 1)
                            ' The IMinute.InsertRows invalidates the internal cache, we need to refresh the cache. See the docs for IMinute.InsertRows.
                            task.Minute.GetFullData()

                            ' Fill the new row with data.
                            Dim insertedRow = rowToInsertAfter + 1
                            Dim fieldsValues = New Dictionary(Of String, Object)()
                            fieldsValues.Add("Reference", reference)
                            fieldsValues.Add("MATERIAL_CostPerUnit", cost)
                            fieldsValues.Add("Unit", unit)
                            fieldsValues.Add("Description", description)
                            fieldsValues.Add("Quantity", quantity)
                            task.Minute.SetFieldValue(insertedRow, fieldsValues)
                        End If ' level >= 1
                    Else
                        ' This is a task or branch. Create it as a sub-task under the correct parent.

                        ' Keep only the required number of nodes in the parent chain (which starts with the root node).
                        ' This means that the last index in the chain must be level-1. Remove the no longer needed nodes.
                        If taskParentChain.Count > level Then
                            Dim start = level
                            Dim removeCount = taskParentChain.Count - start
                            taskParentChain.RemoveRange(start, removeCount)
                        End If

                        ' Get the task object.
                        Dim task As ITask
                        If rowInSheet = 1 Then
                            ' The very first task. Don't create it, because the empty estimate already contains one empty task A under the root.
                            ' Use this existing one.
                            task = Es.CurrentVersion.Wbs.Root.SubTasks.First()
                        Else
                            ' Create the new task.
                            Dim parentTask As ITask = taskParentChain.Last()
                            If parentTask.SubTasks.Count = 0 Then
                                task = parentTask.CreateNewSubTask()
                            Else
                                ' The CreateNewSubTask inserts the new subtask as the FIRST one, before the existing ones.
                                ' To append it after existing sub-tasks, we need to create it as a new task below the last child.
                                Dim lastChild As ITask = parentTask.SubTasks.Last()
                                task = lastChild.Wbs.CreateNewTask(lastChild)
                            End If
                        End If

                        ' Add the task to the parent chain.
                        taskParentChain.Add(task)

                        ' Fill the new task with data.
                        Dim fieldsValues = New Dictionary(Of String, Object)()
                        fieldsValues.Add("WBS_Item", item)
                        fieldsValues.Add("WBS_Unit", unit)
                        fieldsValues.Add("WBS_Description", description)
                        fieldsValues.Add("WBS_Quantity", quantity)
                        task.SetFieldsValuesToDb(fieldsValues)
                    End If
                Next

                Es.CheckAndRepaint()

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
