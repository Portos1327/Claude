using System;
using System.Windows.Forms;
using System.Collections.Generic;
using SpreadsheetGear;
using SpreadsheetGear.Advanced.Cells;
using Qdv.CommonApi;
using Qdv.UserApi;
using Qdv.UserApi.DistributionCurves;
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

        /// <summary>
        /// The entry point of the macro. This method is called when the macro is started.
        /// </summary>
        /// <param name="es">The calling estimate. When the macro is not attached to an estimate, this parameter is <see langword="null"/>.</param>
        /// <param name="context">The information about a context in which the macro is being executed.</param>
        /// <devdoc>
        /// DO NOT REMOVE OR CHANGE THE SIGNATURE OF EntryMethod METHOD!
        /// YOUR MACRO WILL NOT RUN IF REMOVED OR CHANGED.
        /// </devdoc>
        [STAThread]
        public static void EntryMethod(Qdv.UserApi.IEstimate es, Qdv.UserApi.ICallingContext context)
        {
			DialogResult response = MessageBox.Show("This macro dumps the content of a named area in the overhead to a Json temporary file.", "Run macro?", MessageBoxButtons.OKCancel, MessageBoxIcon.Question);
			if (response != DialogResult.OK)
			{
				context.MustCancel = true;  // Cancel the event if the macro is called through an event
				return;
			}
			try
			{

				//Get the area we want to dump. Name is PROJECT_BREAKDOWN
				IWorkbook OverheadWorkbook = null;
				//When we get the workbook this way, it copies in memory the complete workbook to a copy. So we cannot alter the QDV workbook
				//First get a read only copy of the overhead workbook. But this is not the fastest solution
				goto fastMethod;
				var wbParms = new WorkbookParameters();
				wbParms.KeepFormulas = true;
				wbParms.KeepProtected = true;
				OverheadWorkbook = es.CurrentVersion.Overhead.GetReadOnlyCopyOfWorkbook(wbParms);
			//This copy takes about 150 ms in this sample

			fastMethod:
				//This takes only 2 ms but the finally statment is manadatory. Otherwise the estimate could be left in an instable state.
				var sw = new System.Diagnostics.Stopwatch();
				sw.Start();

				//Let's take a reference on the real workbook now, without copy. This is much faster. Some 2 ms
				//but we have to make sure we release the lock in a try/catch/finally statment
				es.CurrentVersion.Overhead.GetLockOnWorkbook(); //We must lock it to access the workbook
				var ListToJson = new List<QDVLine>();
				try
				{
					OverheadWorkbook = es.CurrentVersion.Overhead.GetWorkbook();

					bool nameFound = false;
					SpreadsheetGear.IRange TheRange = null;
					foreach (SpreadsheetGear.IName name in OverheadWorkbook.Names)
					{
						if (name.Name == "PROJECT_BREAKDOWN")
						{
							TheRange = name.RefersToRange;
							nameFound = true;
							break;
						}
					}
					if (nameFound == false)
					{
						MessageBox.Show("This estimate doesn't contain any area named PROJECT_BREAKDOWN!", "Wrong template!", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
						context.MustCancel = true;
						return;
					}
					//Get the range
					//Browse all lines and populate an object
					string currentTitle = "";
					bool wrongFiguresFound = false;
					for (int i = 0; i < TheRange.RowCount - 1; i++)
					{
						//If the text is centered, this is a title. Just to show how to check alignment
						if (TheRange.Cells[i, 0].HorizontalAlignment == HAlign.Center && TheRange.Cells[i, 0].Text.Trim() != "")
						{
							currentTitle = TheRange.Cells[i, 0].Text.Trim();
						}
						else if (TheRange.Cells[i, 0].Text.Trim() != "")
						{
							var QdvLine = new QDVLine();
							QdvLine.Reset();
							string description = TheRange.Cells[i, 0].Text.Trim();
							//We could have N/A or #Ref so maybe interesting to have a test
							double value = 0;
							if (TheRange.Cells[i, 1].ValueType == SpreadsheetGear.ValueType.Number)
							{
								value = (double)TheRange.Cells[i, 1].Value;
							}
							else if (TheRange.Cells[i, 1].ValueType == SpreadsheetGear.ValueType.Empty) { }
							else
							{
								wrongFiguresFound = true;
							}
							double rate = 0;
							if (TheRange.Cells[i, 2].ValueType == SpreadsheetGear.ValueType.Number)
							{
								rate = (double)TheRange.Cells[i, 2].Value;
							}
							else if (TheRange.Cells[i, 1].ValueType == SpreadsheetGear.ValueType.Empty) { }
							else
							{
								wrongFiguresFound = true;
							}
							double price = 0;
							if (TheRange.Cells[i, 3].ValueType == SpreadsheetGear.ValueType.Number)
							{
								price = (double)TheRange.Cells[i, 3].Value;
							}
							else if (TheRange.Cells[i, 1].ValueType == SpreadsheetGear.ValueType.Empty) { }
							else
							{
								wrongFiguresFound = true;
							}
							QdvLine.area = currentTitle;
							QdvLine.description = description;
							QdvLine.value = value;
							QdvLine.rate = rate;
							QdvLine.price = price;
							ListToJson.Add(QdvLine);
						}
					}
					//Do we have wrong figures
					if (wrongFiguresFound)
					{
						MessageBox.Show("Some figures are wrong in the area named PROJECT_BREAKDOWN. Please check your overhead workbook!", "Wrong figures!", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
						context.MustCancel = true;
						return;
					}
				}
				catch (Exception)
				{
					throw;
				}
				finally
				{
					es.CurrentVersion.Overhead.ReleaseLockOnWorkbook(); //We must lock it to access the workbook
				}
				sw.Stop();
				//Now we have all lines with all fields. Let's serialize AllLines to JSon
				string tempFileName = System.IO.Path.GetTempFileName() + ".json";
				string jsonString = JsonSerializer.Serialize(ListToJson);
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
			data = 0,
			title = 1,
		}

		public class QDVLine
		{
			public TypeOfLine typeLine { get; set; } //Important to declare them as properties. Otherwise they cannot be serialized to Json
			public string area { get; set; }
			public string description { get; set; }
			public double value { get; set; }
			public double rate { get; set; }
			public double price { get; set; }
			public void Reset()
			{
				typeLine = TypeOfLine.data;
				area = "";
				description = "";
				value = 0;
				rate = 0;
				price = 0;
			}
		}

	}
}
