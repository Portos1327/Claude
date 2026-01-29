using System;
using System.Windows.Forms;
using System.Collections.Generic;
using Qdv.UserApi;
using Qdv.UserApi.Fields;
using Qdv.UserApi.Profiles;
using System.Text.Json;

// DO NOT REMOVE OR CHANGE THE NAME OF QDV_Macro NAMESPACE
namespace QDV_Macro
{

    /// <summary>
    /// The main class of the macro.
    /// </summary>
    /// <devdoc>
    /// DO NOT REMOVE OR CHANGE THE NAME OF Startup CLASS!
    /// YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED.
    /// </devdoc>
    public class Startup
    {
		[STAThread]
		public static void EntryMethod(Qdv.UserApi.IEstimate es, Qdv.UserApi.ICallingContext context)
		{

			DialogResult response = MessageBox.Show("This macro dumps the content of the WBS and the content of the minutes to a Json temporary file.", "Run macro?", MessageBoxButtons.OKCancel, MessageBoxIcon.Question);
			if (response != DialogResult.OK)
			{
				context.MustCancel = true;  // Cancel the event if the macro is called through an event
				return;
			}

			try
			{

				//Here we need accurate costs because we push costs to the Json.
				//Make sure costs are valid (hano N/A)
				if (es.NeedsRecalculateCosts)
				{
					es.CurrentVersion.ComputeCostsOnly();
				}
				if (es.NeedsRecalculateCosts)
				{
					MessageBox.Show("Cannot get accurate costs. Please compute your estimate first!", "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error);
					context.MustCancel = true;  // Cancel the event if the macro is called through an event
					return;
				}

				IWbs WBS = es.CurrentVersion.Wbs;
				//Get available fields in the WBS
				var wbsFields = es.WbsFieldsRepository;

				//Following lines can be used to list all available fields in the WBS expanded workbook
				//They don't contain system fields (native) which are accessible using GetFieldsValuesFromDb. See below.

				goto bypassDisplay; //remove this to display fields
				
				IEnumerable<IWbsField> allWbsFields = wbsFields.GetAllFields();
				//Get IDs for information
				string ids = "";
				foreach (var wbsField in allWbsFields)
				{
					string id = wbsField.Mnemonic;
					string numericID = wbsField.NumericID.ToString();
					ids += id + "|" + numericID + "\r\n";
				}
				//Will display all available fields in WBS
				MessageBox.Show(ids);

			bypassDisplay:

				var sw = new System.Diagnostics.Stopwatch();
				sw.Start();
				
				List<ITask> Tasks = WBS.GetTasksForScope("", true); //We take all lines of the WBS "" means all, true means also branches

				//Create a collection of QDVLines
				var AllLines = new List<QDVLine>();

				//Increment an absolute line position, starting at 1
				int overallLineNumber = 1;

				foreach (ITask MyTask in Tasks)
				{
					//Create the object which receives line data
					var QDVLine = new QDVLine();
					QDVLine.Reset();
					
					//Get level of WBS
					int level = MyTask.DepthLevel;

					//Get item of WBS
					var dummy = MyTask.GetFieldValue("WBS_Item", PositionInWbsBranch.Top);
					string item = (dummy != null) ? dummy.ToString().Replace("\n", "").Replace("\r", "") : "";
					//Notice that item is indented by default according to the depth of the WBS. Just remove the leading spaces if you don't want this
					item = item.Trim();

					//Get description of WBS
					dummy = MyTask.GetFieldValue("WBS_Description", PositionInWbsBranch.Top);
					string description = (dummy != null) ? dummy.ToString().Replace("\n", "").Replace("\r", "") : "";
					
					//Get unit of WBS
					dummy = MyTask.GetFieldValue("WBS_Unit", PositionInWbsBranch.Bottom);
					string unit = (dummy != null) ? dummy.ToString().Replace("\n", "").Replace("\r", "") : "";
					
					//Get cost per unit
					dummy = MyTask.GetFieldValue("WBS_CostPerUnit", PositionInWbsBranch.Bottom);
					double costPerUnit = ((dummy != null) && dummy.ToString() != "NA") ? (double)dummy : 0; //Could return NA

					//Get total cost
					dummy = MyTask.GetFieldValue("WBS_CostTotal", PositionInWbsBranch.Bottom);
					double totalCost = ((dummy != null) && dummy.ToString() != "NA") ? (double)dummy : 0; //Could return NA

					//Tell if it's a chapter or a minute
					var typeLine = TypeOfLine.wbsChapter;
					switch (MyTask.Kind)
					{
						case TaskKind.Branch:
							typeLine = TypeOfLine.wbsChapter;
							break;
						case TaskKind.Root:
							typeLine = TypeOfLine.wbsRoot;
							break;
						case TaskKind.Task:
							typeLine = TypeOfLine.wbsTask;
							break;
						default:
							break;
					}
					List<string> columnsToGet = new List<string>();
					columnsToGet.Add("WBS_IsOption");
					//We could get all fields at once from the following but only physical fields are there.
					//Free fields or fields returned by minutes (breakdowns) cannot be returned with this method
					//see documentation form more information
					var fieldsFromDB = MyTask.GetFieldsValuesFromDb(columnsToGet);
					int optionStatus = (fieldsFromDB["WBS_IsOption"] != null) ? (int)fieldsFromDB["WBS_IsOption"] : 0;
					//Feed the line
					QDVLine.typeLine = typeLine;
					QDVLine.depthLevel = level;
					QDVLine.item = item;
					QDVLine.description = description;
					QDVLine.unit = unit;
					QDVLine.costPerUnit = costPerUnit;
					QDVLine.totalCost = totalCost;
					QDVLine.overallLineNumber = overallLineNumber;
					overallLineNumber += 1;
					//Let's add the WBS line to the collection
					AllLines.Add(QDVLine);

					// Note that you could get both fields at once by reading directly the db using GetFieldsValuesFromDb. This is faster but only fields stored in db are accessibles, not those calculated in the WBS workbook.
					if (!(MyTask.Minute == null))
					//This way we can access the minute of any task being in the WBS
					//You can also access the overhead minute and the database of the estimate if needed. For this purpose, use the followings:
					//es.CurrentVersion.OverheadCostsMinute
					//es.CurrentVersion.DatabaseOfEstimateMinute
					{
						IMinute MyMinute = MyTask.Minute;
						int MaxRow = MyMinute.GetRowsCount();
						// Get image of minute for two fields
						List<string> FieldsToGet = new List<string>();
						FieldsToGet.Add("LineNumber");
						FieldsToGet.Add("Description");
						FieldsToGet.Add("Unit");
						FieldsToGet.Add("CostPerUnit");
						FieldsToGet.Add("TotalCost");
						// Get description and unit from minute for all rows
						Dictionary<string, Dictionary<int, object>> ImageOfMinute = MyMinute.GetFieldsValues(1, MaxRow, FieldsToGet, false); // Notice that we could collapse groups here
						Dictionary<int, object> AllLineNumbers = ImageOfMinute["LineNumber"];
						Dictionary<int, object> AllDescriptions = ImageOfMinute["Description"];
						Dictionary<int, object> AllUnits = ImageOfMinute["Unit"];
						Dictionary<int, object> AllCostsPerUnit = ImageOfMinute["CostPerUnit"];
						Dictionary<int, object> AllTotalCosts = ImageOfMinute["TotalCost"];
						for (int i = 0; i <= MaxRow - 1; i++)
						{
							dummy = AllLineNumbers[i];
							int minuteLineNumber = (dummy != null) ? (int)dummy : 0;
							dummy = AllDescriptions[i];
							string minuteDescription = (dummy != null) ? dummy.ToString().Replace("\n", "").Replace("\r", "") : "";
							dummy = AllUnits[i];
							string minuteUnit = (dummy != null) ? dummy.ToString().Replace("\n", "").Replace("\r", "") : "";
							dummy = AllCostsPerUnit[i];
							double minuteCostPerUnit = (dummy != null) ? (double)dummy : 0;
							dummy = AllTotalCosts[i];
							double minuteTotalCost = (dummy != null) ? (double)dummy : 0;
							//Create the object which receives line data
							var MinuteQDVLine = new QDVLine();
							MinuteQDVLine.Reset();
							MinuteQDVLine.typeLine = TypeOfLine.minute;
							MinuteQDVLine.minuteLineNumber = minuteLineNumber;
							MinuteQDVLine.description = minuteDescription;
							MinuteQDVLine.unit = minuteUnit;
							MinuteQDVLine.costPerUnit = minuteCostPerUnit;
							MinuteQDVLine.totalCost = minuteTotalCost;
							MinuteQDVLine.overallLineNumber = overallLineNumber;
							overallLineNumber += 1;
							//Let's add the minute line to the collection
							AllLines.Add(MinuteQDVLine);
						}
					}
				}

				sw.Stop();

				//Now we have all lines with all fields. Let's serialize AllLines to JSon
				string tempFileName = System.IO.Path.GetTempFileName() + ".json";
				string jsonString = JsonSerializer.Serialize(AllLines);
				System.IO.File.WriteAllText(tempFileName, jsonString);

				string messageEnd = "JSON string created in " + sw.ElapsedMilliseconds.ToString() + " milliseconds. Do you want to open restuling JSON file?";
				DialogResult endResponse = MessageBox.Show(messageEnd, "Open JSON file?", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
				if (endResponse == DialogResult.Yes)
				{
					System.Diagnostics.Process.Start(tempFileName);
				}

			}
			catch (Exception generalError)
			{
				// Catches all errors to get the proper message.
				MessageBox.Show(generalError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error);
                context.MustCancel = true;  // Cancel the event if the macro is called through an event
            }
		}

		public enum TypeOfLine
		{
			wbsRoot = 0,
			wbsChapter = 1,
			wbsTask = 2,
			minute = 3
		}

		public class QDVLine
		{
			public TypeOfLine typeLine { get; set; } //Important to declare them as properties. Otherwise they cannot be serialized to Json
			public int depthLevel { get; set; }
			public string item { get; set; }
			public string description { get; set; }
			public string unit { get; set; }
			public double costPerUnit { get; set; }
			public double totalCost { get; set; }
			public int isOptional { get; set; }
			public int minuteLineNumber { get; set; }
			public int overallLineNumber { get; set; }
			public void Reset()
			{
				typeLine = TypeOfLine.minute;
				depthLevel = 0;
				item = "";
				description = "";
				unit = "";
				costPerUnit = 0;
				totalCost = 0;
				isOptional = 0;
				minuteLineNumber = 0;
				overallLineNumber = 0;
			}
		}

	}
}
