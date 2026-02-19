'Version 3
Imports System.IO
Imports System.Data.SqlClient


''' <summary>
''' This class is intended to adapt prices and data "on the fly", when connected to a foreign database.
''' </summary>
''' <remarks>
''' <para>
''' By default, the functions of this class bring no change to the data passed, so that they have no effect at all.
''' </para>
''' <para>
''' You can customize this class to return data from your own database. Function is called each time QDV requires an article, whatever the purpose: 
''' update, drop article, called by a set, etc.
''' </para>
''' </remarks>
Public Class clCustomArticle

    Private Shared _ConnectedToDB As Boolean
    Private Shared WithEvents TimerCloseConnection As System.Timers.Timer = Nothing
    Private Shared cnn As SqlConnection = Nothing

    'This source is delivered with the application. Feel free to customize it for you own purpose.


    ''' <summary>
    ''' Gets the version of this class.
    ''' </summary>
    ''' <remarks>
    ''' <para>
    ''' This function must exist since version 2.
    ''' </para>
    ''' <para>
    ''' It is used internally to keep compatibility with old versions of the DLL. Tells the application that some new functions exist in this DLL.
    ''' </para>
    ''' </remarks>
    ''' <returns></returns>
    Public Shared Function GetVersion() As Integer

        Return 3 'Must remain 3. 
        'Must be incremented only by the publisher

    End Function

    Private Shared Sub TimerCloseConnectionTimedEvent(source As Object, e As System.Timers.ElapsedEventArgs)
        CloseConnection()
    End Sub

    Private Shared Function ConnectToDB() As Boolean

        If Not IsNothing(TimerCloseConnection) Then
            TimerCloseConnection.Enabled = False 'safe
        End If
        TimerCloseConnection = Nothing

        'Establishes a connection to the DB and sets a timer to diconnect after a while
        Dim connectionString As String = ""
        'connetionString = "Data Source=ServerName;Initial Catalog=DatabaseName;User ID=UserName;Password=Password"
        'connetionString = "data source=Sql01;initial catalog=Northwind;integrated security=SSPI;persist security info=False;Trusted_Connection=Yes."

        connectionString = "Data Source=localhost;Initial Catalog=Contextual_Prices;User ID=sample_user;Password=sample_password"
        'connectionString = "Data Source=localhost\SQLEXPRESS;Initial Catalog=Contextual_Prices;User ID=sample_user;Password=sample_password"


        cnn = New SqlConnection(connectionString)
        Try
            cnn.Open()
            _ConnectedToDB = True
        Catch ex As Exception
            Return False
        End Try
        'Set a timer to close the connection after a while (Say 5 seconds after latest exchange)
        TimerCloseConnection = New System.Timers.Timer(20000)
        AddHandler TimerCloseConnection.Elapsed, AddressOf TimerCloseConnectionTimedEvent
        TimerCloseConnection.Enabled = True
        Return True
    End Function

    ''' <summary>
    ''' Allows for adapting the article data.
    ''' </summary>
    ''' <param name="FullPathToDb"></param>
    ''' <param name="Fields">Returns the fields values.
    ''' The dictionary represents a complete line from the database with all fields as mapped to the estimate. 
    ''' See <see cref="GetMoreFieldsIntoFieldsDictionary()"/> function for further information.
    ''' </param>
    ''' <param name="CallingEstimateContext">The estimate global variables and their values.</param>
    ''' <returns>
    ''' The result status:<br/>
    ''' 0 = OK<br/>
    ''' 1 = Error message shown but can continue<br/>
    ''' 2 = Post error message, prompt user not to connect during the session<br/>
    ''' 3 = Post error message, don't prompt user not to connect during the session<br/>
    ''' </returns>
    ''' <remarks>
    ''' <para>
    ''' This function exist since version 0. Its signature is used in versions 0, 1, 2 and 3.
    ''' </para>
    ''' </remarks>
    Public Shared Function CustomizeArticles(ByVal FullPathToDb As String, ByRef Fields As Dictionary(Of String, Object), ByVal CallingEstimateContext As Dictionary(Of String, Object)) As Integer

        'This function exist since version 0. Its signature is used in versions 0, 1, 2 and 3.
        Return CustomizeArticles(FullPathToDb, Fields, CallingEstimateContext, Nothing)

    End Function

    ''' <summary>
    ''' Allows for adapting the article data.
    ''' </summary>
    ''' <param name="FullPathToDb"></param>
    ''' <param name="Fields">Returns the fields values.
    ''' The dictionary represents a complete line from the database with all fields as mapped to the estimate. 
    ''' See <see cref="GetMoreFieldsIntoFieldsDictionary()"/> function for further information.
    ''' </param>
    ''' <param name="CallingEstimateContext">The estimate global variables and their values.</param>
    ''' <param name="FieldsFromMinuteLine"></param>
    ''' <returns>
    ''' The result status:<br/>
    ''' 0 = OK<br/>
    ''' 1 = Error message shown but can continue<br/>
    ''' 2 = Post error message, prompt user not to connect during the session<br/>
    ''' 3 = Post error message, don't prompt user not to connect during the session<br/>
    ''' </returns>
    ''' <remarks>
    ''' <para>
    ''' This function with the <paramref name="FieldsFromMinuteLine"/> parameter must exist since version 3.
    ''' </para>
    ''' </remarks>
    Public Shared Function CustomizeArticles(ByVal FullPathToDb As String,
                                             ByRef Fields As Dictionary(Of String, Object),
                                             ByVal CallingEstimateContext As Dictionary(Of String, Object),
                                             ByVal FieldsFromMinuteLine As Dictionary(Of String, Object)) As Integer


        'The dictionary passed in the "Fields" parameter represents a complete line from the database with all fields as mapped to the estimate. See GetMoreFieldsIntoFieldsDictionary function for further information.
        'You can easily change these values by addressing them this way:

        'Fields("MATERIAL_CostPerUnit") = 12.44
        'or
        'Fields("Description") = "My own description"

        'According to the structure of the database, some fields receive numeric values, some others dates, some strings, some blobs..
        'Make sure you apply proper types when you intend to change these fields

        'You certainly will need the reference of the article in order to get it's price. So do this
        'Dim Reference_Of_Article = CType(Field("Reference), String)

        'You may also need information given by the context of calling estimate.

        'If you need fields from the database which may not be listed here because they are not mapped in the estimate or not
        'requested by the user, consider using the GetMoreFieldsIntoFieldsDictionary function

        'The last dictionary passed (FieldsFromMinuteLine) can bring you values of the rows being updated. See GetFieldsFromMinuteLineAtUpdateTime() to figure out how to request these fields.
        'Notice that this dictionary contains values only when you UPDATE a line. It is set to nothing when you insert a line or when the function is called by a version of QDV prior to 7.21.861.

        'First check if connected to DB

        If _ConnectedToDB = False Or IsNothing(cnn) Then
            If ConnectToDB() = False Then
                CloseConnection()
                Return 2 'Tells calling application that it's impossible to connect DB
            End If
        End If

        'Reset timer for another period of time
        If Not IsNothing(TimerCloseConnection) Then
            TimerCloseConnection.Enabled = False
        End If

        'Check estimate fields
        If Not Fields.ContainsKey("MATERIAL_CostPerUnit") Or Not Fields.ContainsKey("MATERIAL_Rebate") Or Not Fields.ContainsKey("MATERIAL_Currency") Then
            MsgBox("In order to get contextual data from this database, your estimate must contain fiels MATERIAL_CostPerUnit, MATERIAL_Rebate and MATERIAL_Currency!", MsgBoxStyle.Exclamation, "")
            CloseConnection()
            Return 2
        End If

        'Read from variables
        Dim Country As String = ""
        Dim Business As String = ""

        If CallingEstimateContext.ContainsKey("GLV_BUSINESS") = True Then
            Business = CallingEstimateContext("GLV_BUSINESS").ToString
        End If
        If CallingEstimateContext.ContainsKey("GLV_COUNTRY") = True Then
            Country = CallingEstimateContext("GLV_COUNTRY").ToString
        End If
        If Country = "" Or Business = "" Then
            MsgBox("Your estimate must contain a variable GLV_BUSINESS and a variable GLV_COUNTRY to connect to contextual data in this context!", MsgBoxStyle.Exclamation, "")
            CloseConnection()
            Return 2
        End If

        'Get reference from row
        Dim Reference As String = Fields("Reference").ToString.Trim

        If Reference = "" Then
            MsgBox("The article has no reference. Cannot query contextual rebates!", MsgBoxStyle.Exclamation, "")
            CloseConnection()
            Return 1
        End If

        'Query contexual rebates
        Dim PricePerUnit As Double = 0
        Dim Rebate As Double = 0
        Dim Currency As String = ""
        Dim cmd As SqlCommand = Nothing
        Dim reader As SqlDataReader = Nothing
        Try
            cmd = New SqlCommand("Select Price, Rebate, Currency FROM dbo.prices WHERE Context = '" & Business & "' AND Country = '" & Country & "' AND Reference = '" & Reference.Replace("'", "''") & "'", cnn)
            reader = cmd.ExecuteReader()
            If reader.HasRows Then
                Try
                    reader.Read() 'Read first row, should not have more!
                    PricePerUnit = CDbl(reader("Price"))
                    Rebate = CDbl(reader("Rebate"))
                    Currency = CStr(reader("Currency"))
                    'Return data to row
                    Fields("MATERIAL_CostPerUnit") = PricePerUnit
                    Fields("MATERIAL_Rebate") = Rebate
                    Fields("MATERIAL_Currency") = Currency
                Catch ex As Exception
                    MsgBox("Error getting data from database for " & Business & " " & Country & " " & Reference & "!" & vbCrLf & vbCrLf & ex.Message, MsgBoxStyle.Exclamation, "")
                    CloseConnection()
                    Return 1
                Finally
                    reader.Close()
                End Try
            Else
                MsgBox("No data found in contextual database for " & Business & " " & Country & " " & Reference & "!", MsgBoxStyle.Exclamation, "")
                Try
                    reader.Close()
                    CloseConnection()
                Catch
                End Try
                Return 1
            End If
        Catch ex As Exception
            MsgBox("Error getting data from database for " & Business & " " & Country & " " & Reference & "!" & vbCrLf & vbCrLf & ex.Message, MsgBoxStyle.Exclamation, "")
            Return 1
        Finally
            reader.Close()
            CloseConnection()
        End Try

        If Not IsNothing(TimerCloseConnection) Then
            TimerCloseConnection.Enabled = True
        End If

        Return 0

    End Function

    Public Shared Function GetMoreFieldsIntoFieldsDictionary() As Dictionary(Of String, Integer)

        'This function must exist since version 2

        'The Fields dictionary of objects passed to the Customize articles function contains data requested by the estimate and nothing else. It doesn't contain all possible
        'data being in the selected article row of the articles manager. This is done that way for performance issues.
        'This is a major concern when using the update function to update a row being in the estimate. In this case, only fields that the user wants to update are passed.
        'It is possible that, in order to seek data in your program, you need more fields. As an example, let's say you need the Family field to decide which rebate you want to return.
        'In this context, when you want to update a row, the Family field may not be passed because the user doesn't want to update it.
        'So, to make sure you have it anyway. You can tell this function that you need it.
        'In the returned dictionary, you provide the mnemonic of the field you want to add, and the value tells if you need to update the field with it.
        'When 1, the field is updated, even if the user didn't want to do this. This can be necessary to ensure consistency.
        'When 0, the field is not updated and kept as it was in the estimate.
        'Other values are not supported

        Dim AddedFields As New Dictionary(Of String, Integer)
        AddedFields.Add("Family", 1)
        AddedFields.Add("Reference", 0)

        'In this example, you ensure Family and Reference are available for your process even if the user don't want to update them.
        'The family field is forcibly updated even if the user didn't select it for updates.

        Return AddedFields
        'Just return Nothing if you don't need added fields

    End Function

    Public Shared Function GetFieldsFromMinuteLineAtUpdateTime() As List(Of String)

        'This function must exist since version 3

        'When you update your lines, you may want to get information from the minute line which doesn't come from the database
        'Let's say, you want to select the supplier or provide "GROSS" in a free column of the minutes when you want to get the gross price for a specific line,
        'you can get such information from the minute as a dictionary named FieldsFromMinuteLine() passed to the CustomizeArticles() function
        'QDV will check that all fields listed here do exist in the estimate. It'll bring an error message when the estimate lacks some fields.

        Dim FieldsToGetFromMinuteLine As New List(Of String)

        FieldsToGetFromMinuteLine.Add("MATERIAL_Coefficient")
        FieldsToGetFromMinuteLine.Add("WORKFORCE_Coefficient")
        FieldsToGetFromMinuteLine.Add("WORKFORCE_TimePerUnit")
        FieldsToGetFromMinuteLine.Add("WORKFORCE_KindID")
        FieldsToGetFromMinuteLine.Add("Supplier")

        'Just leave the list blank or return nothing if you need no field from the minute line.

        Return FieldsToGetFromMinuteLine

    End Function

    Protected Overrides Sub Finalize()
        CloseConnection()
        MyBase.Finalize()
    End Sub

    Public Shared Sub CloseConnection()

        'This function must exist since version 0

        If Not IsNothing(TimerCloseConnection) Then
            TimerCloseConnection.Enabled = False
        End If
        TimerCloseConnection = Nothing
        If Not IsNothing(cnn) Then
            cnn.Close()
            cnn.Dispose()
            cnn = Nothing
            _ConnectedToDB = False
        End If
    End Sub

End Class
