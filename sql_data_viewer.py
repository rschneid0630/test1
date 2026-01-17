import pyodbc
import psycopg2
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
from datetime import datetime
import threading
from fpdf import FPDF
import os

# Version of the program
VERSION = "V2.8"

# User credentials for Sybase and DataLake connections
userid = 'rschneid'     # Replace with your actual username
password = 'rrsrrsrrs_12'   # Replace with your actual password

# Helper function to run UI updates in the main thread
def run_in_main_thread(func):
    if threading.current_thread() == threading.main_thread():
        func()
    else:
        root.after(0, func)

# Function to update the status in the scrollable text box
def update_status(message):
    def append_message():
        status_box.insert(tk.END, message + '\n')
        status_box.see(tk.END)  # Auto-scroll to the latest entry

    run_in_main_thread(append_message)

# Function to generate the PDF report
def generate_pdf_report():
    pdf = FPDF(orientation='L', unit='mm', format='A4')  # Landscape mode
    pdf.add_page()

    # Set title and font
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="SQL Query Results Report", ln=True, align="C")

    pdf.ln(10)  # Add a line break

    # Set general font
    pdf.set_font("Arial", '', 12)

    # Add EIS.MASTER results
    pdf.cell(200, 10, txt=f"EIS.MASTER Max Date: {max_date_label_eis['text']}, Count: {count_label_eis['text']}", ln=True)

    # Add FINMASTER results
    pdf.cell(200, 10, txt=f"FINMASTER Max Date: {max_date_label_finmaster['text']}, Count: {count_label_finmaster['text']}", ln=True)

    # Add EIS.EPSCoR results
    pdf.cell(200, 10, txt=f"EIS.EPSCoR Max Date: {max_date_label_epscor['text']}, Count: {count_label_epscor['text']}", ln=True)

    # Add DBO.MASTER results
    pdf.cell(200, 10, txt=f"DBO.MASTER Max Date: {max_date_label_dbo['text']}, Count: {count_label_dbo['text']}", ln=True)

    # Add RD-REPORTING results
    pdf.cell(200, 10, txt=f"RD-REPORTING Max Date: {max_date_label_rd_reporting['text']}, Count: {count_label_rd_reporting['text']}", ln=True)

    # Add Sybase.rptsql results
    pdf.cell(200, 10, txt=f"Sybase.daly_oblg_bal Max Date: {max_date_label_sybase['text']}, Count: {count_label_sybase['text']}", ln=True)
    pdf.cell(200, 10, txt=f"Sybase.xpnd_bal Max Date: {max_date_label_sybase_xpnd['text']}, Count: {count_label_sybase_xpnd['text']}", ln=True)

    # Add DataLake.rptsql results
    pdf.cell(200, 10, txt=f"DataLake.daly_oblg_bal Max Date: {max_date_label_datalake['text']}, Count: {count_label_datalake['text']}", ln=True)
    pdf.cell(200, 10, txt=f"DataLake.xpnd_bal Max Date: {max_date_label_datalake_xpnd['text']}, Count: {count_label_datalake_xpnd['text']}", ln=True)

    # Add SOF Data Date and File Name
    pdf.cell(200, 10, txt=f"SOF Data File: {sof_file_name_label['text']}", ln=True)
    pdf.cell(200, 10, txt=f"Date Modified: {sof_data_label['text']}", ln=True)

    pdf.ln(10)  # Another line break

    # Save the PDF file
    pdf_output_path = f"query_results_report_{VERSION}.pdf"
    pdf.output(pdf_output_path)

    update_status(f"PDF report generated: {pdf_output_path}")
    messagebox.showinfo("Success", f"PDF report saved as {pdf_output_path}")

# Function to update the "Report As Of" label with current date and time
def update_report_time():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")  # Date and time down to the minute
    report_time_label.config(text=current_time)

# Function to check if the max date is more than 5 days old
def check_date_and_color(label_widget, date_str):
    def update_color():
        try:
            max_date = datetime.strptime(date_str, "%Y-%m-%d")
            if (datetime.now() - max_date).days > 5:
                label_widget.config(bg="red")  # Change to red if more than 5 days old
            else:
                label_widget.config(bg="white")  # Keep white if within 5 days
        except Exception:
            label_widget.config(bg="white")  # Default to white if any error in parsing

    run_in_main_thread(update_color)

# Query function for pyodbc databases
def run_query(conn_string, query, label_widget, result_format="{}"):
    try:
        update_status(f"Connecting to database with query: {query[:30]}...")

        # Establish connection
        conn = pyodbc.connect(conn_string)
        cursor = conn.cursor()

        # Execute query
        update_status(f"Running query: {query[:30]}...")
        cursor.execute(query)
        result = cursor.fetchone()

        # Prepare the UI updates
        if result and result[0]:
            if isinstance(result[0], str):
                formatted_result = result[0][:10]  # Trim string to 'YYYY-MM-DD'
            elif isinstance(result[0], (pyodbc.Timestamp, datetime)):
                formatted_result = result[0].strftime("%Y-%m-%d")  # Handle timestamp
            else:
                formatted_result = result_format.format(result[0])

            def update_label():
                label_widget.config(text=formatted_result)
                if 'max_date' in label_widget._name:
                    check_date_and_color(label_widget, formatted_result)
            run_in_main_thread(update_label)
        else:
            def update_label():
                label_widget.config(text="No data found")
                label_widget.config(bg="white")  # Default to white if no data
            run_in_main_thread(update_label)

        update_status(f"Query completed: {query[:30]}...")
        conn.close()
    except Exception as e:
        message = f"Error: {str(e)}"
        update_status(message)

        def show_error():
            messagebox.showerror("Error", message)
        run_in_main_thread(show_error)

# Query function for PostgreSQL databases
def run_postgres_query(conn_params, query, label_widget, result_format="{}"):
    try:
        update_status(f"Connecting to PostgreSQL with query: {query[:30]}...")

        # Establish connection
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()

        # Execute query
        update_status(f"Running query: {query[:30]}...")
        cursor.execute(query)
        result = cursor.fetchone()

        # Prepare the UI updates
        if result and result[0]:
            if isinstance(result[0], datetime):
                formatted_result = result[0].strftime("%Y-%m-%d")
            else:
                formatted_result = result_format.format(result[0])

            def update_label():
                label_widget.config(text=formatted_result)
                if 'max_date' in label_widget._name:
                    check_date_and_color(label_widget, formatted_result)
            run_in_main_thread(update_label)
        else:
            def update_label():
                label_widget.config(text="No data found")
                label_widget.config(bg="white")
            run_in_main_thread(update_label)

        update_status(f"Query completed: {query[:30]}...")
        conn.close()
    except Exception as e:
        message = f"Error: {str(e)}"
        update_status(message)

        def show_error():
            messagebox.showerror("Error", message)
        run_in_main_thread(show_error)

# Function to run the MSDB job query and display results in the Treeview
def run_job_query():
    try:
        update_status("Connecting to the msdb database on p-budg-w-sas19...")

        # Establish connection to msdb database on p-budg-w-sas19 using Trusted Connection
        conn = pyodbc.connect(
            f'DRIVER={{SQL Server}};'
            f'SERVER=p-budg-w-sas19;'
            f'DATABASE=msdb;'
            f'Trusted_Connection=yes;'
            f'TrustServerCertificate=yes;'
        )
        cursor = conn.cursor()

        # SQL query to fetch job details
        sql_query = '''
        SELECT
            [sJOB].[name] AS [JobName],
            CASE
                WHEN [sJOBH].[run_date] IS NULL OR [sJOBH].[run_time] IS NULL THEN NULL
                ELSE CAST(
                    CAST([sJOBH].[run_date] AS CHAR(8))
                    + ' '
                    + STUFF(
                        STUFF(RIGHT('000000' + CAST([sJOBH].[run_time] AS VARCHAR(6)), 6), 3, 0, ':'), 6, 0, ':'
                    ) AS DATETIME
                )
            END AS [LastRunDateTime],
            CASE [sJOBH].[run_status]
                WHEN 0 THEN 'Failed'
                WHEN 1 THEN 'Succeeded'
                WHEN 2 THEN 'Retry'
                WHEN 3 THEN 'Canceled'
                WHEN 4 THEN 'Running' -- In Progress
            END AS [LastRunStatus],
            STUFF(
                STUFF(RIGHT('000000' + CAST([sJOBH].[run_duration] AS VARCHAR(6)), 6), 3, 0, ':'), 6, 0, ':'
            ) AS [LastRunDuration],
            [sJOBH].[message] AS [LastRunStatusMessage],
            CASE [sJOBSCH].[NextRunDate]
                WHEN 0 THEN NULL
                ELSE CAST(
                    CAST([sJOBSCH].[NextRunDate] AS CHAR(8))
                    + ' '
                    + STUFF(
                        STUFF(RIGHT('000000' + CAST([sJOBSCH].[NextRunTime] AS VARCHAR(6)), 6), 3, 0, ':'), 6, 0, ':'
                    ) AS DATETIME
                )
            END AS [NextRunDateTime]
        FROM
            [msdb].[dbo].[sysjobs] AS [sJOB]
            LEFT JOIN (
                SELECT
                    [job_id],
                    MIN([next_run_date]) AS [NextRunDate],
                    MIN([next_run_time]) AS [NextRunTime]
                FROM [msdb].[dbo].[sysjobschedules]
                GROUP BY [job_id]
            ) AS [sJOBSCH]
            ON [sJOB].[job_id] = [sJOBSCH].[job_id]
            LEFT JOIN (
                SELECT
                    [job_id],
                    [run_date],
                    [run_time],
                    [run_status],
                    [run_duration],
                    [message],
                    ROW_NUMBER() OVER (
                        PARTITION BY [job_id]
                        ORDER BY [run_date] DESC, [run_time] DESC
                    ) AS RowNumber
                FROM [msdb].[dbo].[sysjobhistory]
                WHERE [step_id] = 0
            ) AS [sJOBH]
            ON [sJOB].[job_id] = [sJOBH].[job_id]
            AND [sJOBH].[RowNumber] = 1
        WHERE
            [sJOBH].[run_date] IS NOT NULL AND [sJOBH].[run_time] IS NOT NULL
        ORDER BY [sJOB].[name]
        '''

        # Execute the query
        update_status("Running MSDB job query...")
        cursor.execute(sql_query)
        results = cursor.fetchall()

        # Prepare the UI update function
        def update_job_tree():
            # Clear existing data in the Treeview (if any)
            for i in job_tree.get_children():
                job_tree.delete(i)

            # Insert new data into the Treeview and apply color tags
            for row in results:
                last_run_status = row[2]  # The status field
                tag = "success" if last_run_status == "Succeeded" else "fail"
                job_tree.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5]), tags=(tag))

            update_status("Job query executed successfully!")

        # Update the UI on the main thread
        run_in_main_thread(update_job_tree)
        conn.close()

    except Exception as e:
        error_message = f"Error: {str(e)}"
        update_status(error_message)
        def show_error():
            messagebox.showerror("Error", error_message)
        run_in_main_thread(show_error)

# Function to fetch data for all queries, each in its own thread
def fetch_data_multithreaded():
    # Update the report time when fetching data
    update_report_time()

    # EIS.MASTER Queries
    eis_conn_string = 'DRIVER={SQL Server};SERVER=p-budg-w-db19;DATABASE=BUDG;Trusted_Connection=yes;TrustServerCertificate=yes;'
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT MAX(postDate) FROM eis.master", max_date_label_eis, "{}")).start()
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT COUNT(*) FROM eis.master", count_label_eis, "{:,}")).start()

    # EIS.EPSCoR Queries
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT MAX(postdate) FROM eis.EPSCOR_TARGET_TRACKING ett", max_date_label_epscor, "{}")).start()
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT COUNT(*) FROM eis.EPSCOR_TARGET_TRACKING ett", count_label_epscor, "{:,}")).start()

    # DBO.MASTER Queries
    dbo_conn_string = 'DRIVER={SQL Server};SERVER=p-budg-w-db19;DATABASE=FINTRAN;Trusted_Connection=yes;TrustServerCertificate=yes;'
    threading.Thread(target=run_query, args=(dbo_conn_string, "SELECT MAX(b.postDate) FROM dbo.master b", max_date_label_dbo, "{}")).start()
    threading.Thread(target=run_query, args=(dbo_conn_string, "SELECT COUNT(*) FROM dbo.master b", count_label_dbo, "{:,}")).start()

    # FINMASTER Queries
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT MAX(last_updt_Tmsp) FROM eis.finmaster", max_date_label_finmaster, "{}")).start()
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT COUNT(*) FROM eis.finmaster", count_label_finmaster, "{:,}")).start()

    # RD-REPORTING Queries
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT COUNT(*) FROM eis.RD_REPORTING_2025 rr", count_label_rd_reporting, "{:,}")).start()
    threading.Thread(target=run_query, args=(eis_conn_string, "SELECT MAX(rs.glpostdate) FROM eis.RD_REPORTING_2025 rs", max_date_label_rd_reporting, "{}")).start()

    # Sybase.rptsql Queries using the RPTSERVER ODBC DSN
    sybase_conn_string = (
        f'DSN=RPTSERVER;DATABASE=rptdb;UID={userid};PWD={password};Port=5010;Encrypt=yes;'
    )

    # Queries for csd.daly_oblg_bal
    threading.Thread(target=run_query, args=(sybase_conn_string, "select max(dob.itrk_updt_date)   from csd.daly_oblg_bal dob ", max_date_label_sybase, "{}")).start()
    threading.Thread(target=run_query, args=(sybase_conn_string, "SELECT COUNT(*) FROM csd.daly_oblg_bal dob", count_label_sybase, "{:,}")).start()

    # Queries for csd.xpnd_bal
    threading.Thread(target=run_query, args=(sybase_conn_string, "SELECT MAX(xb.last_updt_tmsp) FROM csd.xpnd_bal xb", max_date_label_sybase_xpnd, "{}")).start()
    threading.Thread(target=run_query, args=(sybase_conn_string, "SELECT COUNT(*) FROM csd.xpnd_bal xb", count_label_sybase_xpnd, "{:,}")).start()

    # Fetch latest file modification date for SOF data in a new thread
    threading.Thread(target=fetch_latest_file_date).start()

    # Run MSDB Job Query in a new thread
    threading.Thread(target=run_job_query).start()

    # DataLake Queries using PostgreSQL
    datalake_conn_params = {
        'host': 'disprdedwrdspgdbirep0101.cu00yqxproth.us-east-1.rds.amazonaws.com',
        'port': 5432,
        'dbname': 'disprdedwrdspgdb01',
        'user': 'rschneid@AD.NSF.GOV',  # User ID hardcoded as per instruction
        'password': password  # Use the 'password' variable
    }

    # Queries for rptdb.daly_oblg_bal
    threading.Thread(
        target=run_postgres_query,
        args=(datalake_conn_params, "SELECT COUNT(*) FROM rptdb.daly_oblg_bal", count_label_datalake, "{:,}")
    ).start()
    threading.Thread(
        target=run_postgres_query,
        args=(datalake_conn_params, "SELECT MAX(last_updt_Tmsp) FROM rptdb.daly_oblg_bal", max_date_label_datalake, "{}")
    ).start()

    # Queries for rptdb.xpnd_bal
    threading.Thread(
        target=run_postgres_query,
        args=(datalake_conn_params, "SELECT COUNT(*) FROM rptdb.xpnd_bal", count_label_datalake_xpnd, "{:,}")
    ).start()
    threading.Thread(
        target=run_postgres_query,
        args=(datalake_conn_params, "SELECT MAX(last_updt_Tmsp) FROM rptdb.xpnd_bal", max_date_label_datalake_xpnd, "{}")
    ).start()

# Function to fetch the latest file date for "iTRAK_SOF_"
def fetch_latest_file_date():
    try:
        folder = r'K:\SASPrograms\iTRAKReports'  # Replace with your actual folder path
        files = [f for f in os.listdir(folder) if f.startswith("iTRAK_SOF_")]
        if files:
            latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder, f)))
            latest_file_path = os.path.join(folder, latest_file)
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file_path))
            mod_time_str = mod_time.strftime("%Y-%m-%d %H:%M")

            # Check if the modification date is today
            is_today = mod_time.date() == datetime.now().date()

            def update_ui():
                sof_file_name_label.config(text=latest_file)
                sof_data_label.config(text=mod_time_str)
                if not is_today:
                    sof_data_label.config(bg="red")
                else:
                    sof_data_label.config(bg="white")
                update_status(f"SOF Data File: {latest_file} modified on {mod_time_str}")
            run_in_main_thread(update_ui)
        else:
            def update_ui():
                sof_file_name_label.config(text="No file found")
                sof_data_label.config(text="")
                sof_data_label.config(bg="white")
                update_status("No SOF data file found")
            run_in_main_thread(update_ui)
    except Exception as e:
        def update_ui():
            sof_file_name_label.config(text="Error")
            sof_data_label.config(text="")
            sof_data_label.config(bg="white")
            update_status(f"Error fetching SOF data file: {str(e)}")
        run_in_main_thread(update_ui)

# Function to handle column sorting in the Treeview
def treeview_sort_column(tv, col, reverse):
    try:
        l = [(tv.set(k, col), k) for k in tv.get_children('')]
        l.sort(reverse=reverse)

        # Rearranging items in sorted positions
        for index, (val, k) in enumerate(l):
            tv.move(k, '', index)

        # Reverse sort next time
        tv.heading(col, command=lambda: treeview_sort_column(tv, col, not reverse))
    except Exception as e:
        update_status(f"Error sorting column {col}: {str(e)}")

# Tkinter UI Setup
root = tk.Tk()
root.title(f"SQL Server Data Viewer with Multi-Frame Queries - {VERSION}")

# Main frames
main_frame = tk.Frame(root)
main_frame.grid(row=0, column=0, padx=10, pady=10)

# First row (EIS.MASTER, FINMASTER, EIS.EPSCoR, SOF Data)
master_frame_eis = tk.LabelFrame(main_frame, text="EIS.MASTER")
master_frame_eis.grid(row=0, column=0, padx=5, pady=5)

tk.Label(master_frame_eis, text="Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_eis = tk.Label(master_frame_eis, name='max_date_eis', text="", bg="white", relief="sunken", width=20)
max_date_label_eis.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_eis, text="Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_eis = tk.Label(master_frame_eis, text="", bg="white", relief="sunken", width=20)
count_label_eis.grid(row=1, column=1, padx=5, pady=5)

master_frame_finmaster = tk.LabelFrame(main_frame, text="FINMASTER")
master_frame_finmaster.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_finmaster, text="Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_finmaster = tk.Label(master_frame_finmaster, name='max_date_finmaster', text="", bg="white", relief="sunken", width=20)
max_date_label_finmaster.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_finmaster, text="Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_finmaster = tk.Label(master_frame_finmaster, text="", bg="white", relief="sunken", width=20)
count_label_finmaster.grid(row=1, column=1, padx=5, pady=5)

master_frame_epscor = tk.LabelFrame(main_frame, text="EIS.EPSCoR")
master_frame_epscor.grid(row=0, column=2, padx=5, pady=5)

tk.Label(master_frame_epscor, text="Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_epscor = tk.Label(master_frame_epscor, name='max_date_epscor', text="", bg="white", relief="sunken", width=20)
max_date_label_epscor.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_epscor, text="Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_epscor = tk.Label(master_frame_epscor, text="", bg="white", relief="sunken", width=20)
count_label_epscor.grid(row=1, column=1, padx=5, pady=5)

sof_data_frame = tk.LabelFrame(main_frame, text="SOF Data")
sof_data_frame.grid(row=0, column=3, padx=5, pady=5)

tk.Label(sof_data_frame, text="File Name:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
sof_file_name_label = tk.Label(sof_data_frame, text="", bg="white", relief="sunken", width=20)
sof_file_name_label.grid(row=0, column=1, padx=5, pady=5)

tk.Label(sof_data_frame, text="Date Modified:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
sof_data_label = tk.Label(sof_data_frame, text="", bg="white", relief="sunken", width=20)
sof_data_label.grid(row=1, column=1, padx=5, pady=5)

# Second row (DBO.MASTER, RD-REPORTING, Sybase.rptsql, DataLake.rptsql)
master_frame_dbo = tk.LabelFrame(main_frame, text="DBO.MASTER")
master_frame_dbo.grid(row=1, column=0, padx=5, pady=5)

tk.Label(master_frame_dbo, text="Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_dbo = tk.Label(master_frame_dbo, name='max_date_dbo', text="", bg="white", relief="sunken", width=20)
max_date_label_dbo.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_dbo, text="Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_dbo = tk.Label(master_frame_dbo, text="", bg="white", relief="sunken", width=20)
count_label_dbo.grid(row=1, column=1, padx=5, pady=5)

master_frame_rd_reporting = tk.LabelFrame(main_frame, text="RD-REPORTING")
master_frame_rd_reporting.grid(row=1, column=1, padx=5, pady=5)

tk.Label(master_frame_rd_reporting, text="Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_rd_reporting = tk.Label(master_frame_rd_reporting, name='max_date_rd_reporting', text="", bg="white", relief="sunken", width=20)
max_date_label_rd_reporting.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_rd_reporting, text="Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_rd_reporting = tk.Label(master_frame_rd_reporting, text="", bg="white", relief="sunken", width=20)
count_label_rd_reporting.grid(row=1, column=1, padx=5, pady=5)

# Modified Sybase Frame to include additional queries
master_frame_sybase = tk.LabelFrame(main_frame, text="Sybase.rptsql")
master_frame_sybase.grid(row=1, column=2, padx=5, pady=5)

# csd.daly_oblg_bal
tk.Label(master_frame_sybase, text="daly_oblg_bal Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_sybase = tk.Label(master_frame_sybase, name='max_date_sybase', text="", bg="white", relief="sunken", width=20)
max_date_label_sybase.grid(row=0, column=1, padx=5, pady=5)

tk.Label(master_frame_sybase, text="daly_oblg_bal Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_sybase = tk.Label(master_frame_sybase, text="", bg="white", relief="sunken", width=20)
count_label_sybase.grid(row=1, column=1, padx=5, pady=5)

# csd.xpnd_bal
tk.Label(master_frame_sybase, text="xpnd_bal Max Date:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
max_date_label_sybase_xpnd = tk.Label(master_frame_sybase, name='max_date_sybase_xpnd', text="", bg="white", relief="sunken", width=20)
max_date_label_sybase_xpnd.grid(row=2, column=1, padx=5, pady=5)

tk.Label(master_frame_sybase, text="xpnd_bal Count:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
count_label_sybase_xpnd = tk.Label(master_frame_sybase, text="", bg="white", relief="sunken", width=20)
count_label_sybase_xpnd.grid(row=3, column=1, padx=5, pady=5)

# Modified DataLake Frame to include additional queries and rename it
datalake_frame = tk.LabelFrame(main_frame, text="DataLake.rptsql")
datalake_frame.grid(row=1, column=3, padx=5, pady=5)

# rptdb.daly_oblg_bal
tk.Label(datalake_frame, text="daly_oblg_bal Max Date:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
max_date_label_datalake = tk.Label(datalake_frame, name='max_date_datalake', text="", bg="white", relief="sunken", width=20)
max_date_label_datalake.grid(row=0, column=1, padx=5, pady=5)

tk.Label(datalake_frame, text="daly_oblg_bal Count:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
count_label_datalake = tk.Label(datalake_frame, text="", bg="white", relief="sunken", width=20)
count_label_datalake.grid(row=1, column=1, padx=5, pady=5)

# rptdb.xpnd_bal
tk.Label(datalake_frame, text="xpnd_bal Max Date:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
max_date_label_datalake_xpnd = tk.Label(datalake_frame, name='max_date_datalake_xpnd', text="", bg="white", relief="sunken", width=20)
max_date_label_datalake_xpnd.grid(row=2, column=1, padx=5, pady=5)

tk.Label(datalake_frame, text="xpnd_bal Count:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
count_label_datalake_xpnd = tk.Label(datalake_frame, text="", bg="white", relief="sunken", width=20)
count_label_datalake_xpnd.grid(row=3, column=1, padx=5, pady=5)

# Third row (MSDB Job Query Results)
msdb_frame = tk.LabelFrame(main_frame, text="MSDB Job Query Results")
msdb_frame.grid(row=2, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

columns = ("JobName", "LastRunDateTime", "LastRunStatus", "LastRunDuration", "LastRunStatusMessage", "NextRunDateTime")
job_tree = ttk.Treeview(msdb_frame, columns=columns, show='headings')
for col in columns:
    job_tree.heading(col, text=col, command=lambda _col=col: treeview_sort_column(job_tree, _col, False))
job_tree.grid(row=0, column=0, sticky="nsew")

# Add color tags for success/fail
job_tree.tag_configure("success", background="lightgreen")
job_tree.tag_configure("fail", background="lightcoral")

# Configure scrollbar
scrollbar_y = ttk.Scrollbar(msdb_frame, orient="vertical", command=job_tree.yview)
scrollbar_y.grid(row=0, column=1, sticky="ns")
job_tree.config(yscrollcommand=scrollbar_y.set)

# Make the Treeview expand to fill the frame
msdb_frame.rowconfigure(0, weight=1)
msdb_frame.columnconfigure(0, weight=1)

# Report As Of frame, positioned above Fetch Data
report_frame = tk.LabelFrame(root, text="Report As Of")
report_frame.grid(row=3, column=0, padx=10, pady=10, columnspan=4)

report_time_label = tk.Label(report_frame, text="", bg="white", relief="sunken", width=20)
report_time_label.grid(row=0, column=0, padx=5, pady=5)

version_label = tk.Label(report_frame, text=f"Version: {VERSION}")
version_label.grid(row=1, column=0, padx=5, pady=5)

# Fetch Data and Generate PDF Buttons
button_frame = tk.Frame(root)
button_frame.grid(row=4, column=0, padx=10, pady=10, columnspan=4)

fetch_button = tk.Button(button_frame, text="Fetch All Data", command=fetch_data_multithreaded)
fetch_button.grid(row=0, column=0, padx=10, pady=5)

generate_pdf_button = tk.Button(button_frame, text="Generate PDF Report", command=generate_pdf_report)
generate_pdf_button.grid(row=0, column=1, padx=10, pady=5)

# Running Status Frame
status_frame = tk.LabelFrame(root, text="Running Status")
status_frame.grid(row=5, column=0, columnspan=4, padx=10, pady=10, sticky="ew")

status_box = scrolledtext.ScrolledText(status_frame, width=100, height=10, wrap=tk.WORD)
status_box.grid(row=0, column=0, sticky="ew")

# Initial Report Time Update
update_report_time()

root.mainloop()
