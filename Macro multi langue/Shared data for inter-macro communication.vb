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
		/// This macro displays how many times it was called in the current application session.
		/// The counter is stored in the shared user data.
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
            try
			{
				MessageBox.Show("This macro shows how to pass data from a macro to another invoked later using the centralized storage object.\r\n\r\nNotice that the centralized storage object is not persistent. It will be reset each time you restart QDV.", "Demo centralized storage", MessageBoxButtons.OK, MessageBoxIcon.Exclamation);
				// The user data keys, one for this estimate and one for all estimates.
				// All user data is global and accessible from any macro (that can be called from any event).
				// Use a unique data key to make sure you don't conflict with other data, for example estimate full path.

				// Counter just for this estimate.
				string thisEstimateCallCounterKey = es.FullPath + "_" + "MyMacroCallCounter";
				// Counter for all estimates if you copy this macro to another estimate(s).
				string anyEstimateCallCounterKey = "MyMacroCallCounter";

				// Get stored data, if any.
				int thisEstimateCallCounter = 1;
				if (context.QdvManager.Environment.UserData.ContainsKey(thisEstimateCallCounterKey))
				{
					thisEstimateCallCounter = (int)context.QdvManager.Environment.UserData[thisEstimateCallCounterKey];
					thisEstimateCallCounter++;
				}

				int anyEstimateCallCounter = 1;
				if (context.QdvManager.Environment.UserData.ContainsKey(anyEstimateCallCounterKey))
				{
					anyEstimateCallCounter = (int)context.QdvManager.Environment.UserData[anyEstimateCallCounterKey];
					anyEstimateCallCounter++;
				}

				string msg = "This macro was called\n";
				msg += thisEstimateCallCounter.ToString() + " times from this estimate\n";
				msg += anyEstimateCallCounter.ToString() + " times from any estimate";
				MessageBox.Show(msg);

				// Store the data.
				context.QdvManager.Environment.UserData[thisEstimateCallCounterKey] = thisEstimateCallCounter;
				context.QdvManager.Environment.UserData[anyEstimateCallCounterKey] = anyEstimateCallCounter;
            }
            catch (Exception generalError)
            {
                // Catches all errors to get the proper message.
                MessageBox.Show(generalError.Message, "Error!", MessageBoxButtons.OK, MessageBoxIcon.Error);
                context.MustCancel = true;  // Cancel the event if the macro is called through an event
            }
        }


    }
}
