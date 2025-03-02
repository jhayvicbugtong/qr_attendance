import mysql.connector
import os
from tkinter import messagebox
from tkinter import ttk
import customtkinter as ctk
import pandas as pd
import qrcode
from PIL import Image, ImageTk
from tkcalendar import DateEntry

# --- Database Functions ---
def connect_db():
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="",
            database="qr_attendance_db"
        )
        return mydb
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Could not connect to database: {err}")
        return None

def fetch_students(mydb):
    try:
        cursor = mydb.cursor()
        query = "SELECT student_id, name, email, contact FROM students"
        cursor.execute(query)
        data = cursor.fetchall()
        columns = ["student_id", "name", "email", "contact"]
        df = pd.DataFrame(data, columns=columns)
        cursor.close()
        return df
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error fetching students: {err}")
        return None
    finally:
        if mydb.is_connected():
            mydb.close()

def fetch_attendance_report(mydb, query):
    try:
        df = pd.read_sql(query, mydb)
        return df
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error fetching attendance: {err}")
        return None
    finally:
        if mydb.is_connected():
            mydb.close()

# --- GUI Functions ---
def update_report_table(query):
    mydb = connect_db()
    if mydb:
        data = fetch_attendance_report(mydb, query)
        if data is not None:
            for item in report_table.get_children():
                report_table.delete(item)
            for row in data.itertuples(index=False):
                report_table.insert("", "end", values=row)

def show_daily_report():
    query = """
    SELECT s.name, a.student_id, 
           SUM(CASE WHEN a.action = 'Time In' THEN 1 ELSE 0 END) AS present_count,
           COUNT(DISTINCT DATE(a.scan_time)) AS total_days,
           (SUM(CASE WHEN a.action = 'Time In' THEN 1 ELSE 0 END) / COUNT(DISTINCT DATE(a.scan_time))) * 100 AS attendance_rate
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    WHERE DATE(a.scan_time) = CURDATE()
    GROUP BY s.name, a.student_id;
    """
    update_report_table(query)

def show_weekly_report():
    query = """
    SELECT s.name, a.student_id, 
           SUM(CASE WHEN a.action = 'Time In' THEN 1 ELSE 0 END) AS present_count,
           COUNT(DISTINCT DATE(a.scan_time)) AS total_days,
           (SUM(CASE WHEN a.action = 'Time In' THEN 1 ELSE 0 END) / COUNT(DISTINCT DATE(a.scan_time))) * 100 AS attendance_rate
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    WHERE DATE(a.scan_time) BETWEEN CURDATE() - INTERVAL 7 DAY AND CURDATE()
    GROUP BY s.name, a.student_id;
    """
    update_report_table(query)

def show_monthly_report():
    query = """
    SELECT s.name, a.student_id, 
           SUM(CASE WHEN a.action = 'Time In' THEN 1 ELSE 0 END) AS present_count,
           COUNT(DISTINCT DATE(a.scan_time)) AS total_days,
           (SUM(CASE WHEN a.action = 'Time In' THEN 1 ELSE 0 END) / COUNT(DISTINCT DATE(a.scan_time))) * 100 AS attendance_rate
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    WHERE MONTH(a.scan_time) = MONTH(CURDATE()) AND YEAR(a.scan_time) = YEAR(CURDATE())
    GROUP BY s.name, a.student_id;
    """
    update_report_table(query)

def show_top_absentees():
    query = """
    SELECT s.name, a.student_id,
           COUNT(DISTINCT DATE(a.scan_time)) AS days_present,
           (30 - COUNT(DISTINCT DATE(a.scan_time))) AS absent_count,
           ((30 - COUNT(DISTINCT DATE(a.scan_time))) / 30) * 100 AS absence_percentage
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    WHERE MONTH(a.scan_time) = MONTH(CURDATE()) AND YEAR(a.scan_time) = YEAR(CURDATE())
    GROUP BY s.name, a.student_id
    ORDER BY absent_count DESC
    LIMIT 5;
    """
    update_report_table(query)

def show_low_attendance():
    query = """
    SELECT s.name, a.student_id,
           COUNT(DISTINCT DATE(a.scan_time)) AS present_days,
           (COUNT(DISTINCT DATE(a.scan_time)) / 30) * 100 AS attendance_rate
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    WHERE MONTH(a.scan_time) = MONTH(CURDATE()) AND YEAR(a.scan_time) = YEAR(CURDATE())
    GROUP BY s.name, a.student_id
    HAVING attendance_rate < 75;
    """
    update_report_table(query)

# --- GUI Setup ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("Attendance Reports")
root.geometry("800x500")

tabview = ctk.CTkTabview(root)
tabview.pack(expand=True, fill="both", padx=10, pady=10)

tab1 = tabview.add("Attendance Reports")

# --- Tab 1 Content ---
report_frame = ctk.CTkFrame(tab1)
report_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("Name", "Student ID", "Present Count", "Total Days", "Attendance Rate") #Updated Columns
report_table = ttk.Treeview(report_frame, columns=columns, show="headings")
for col in columns:
    report_table.heading(col, text=col)
    report_table.column(col, width=150, anchor="center")
report_table.pack(pady=10, fill="both", expand=True)


btn_frame = ctk.CTkFrame(report_frame)
btn_frame.pack(pady=10)

btn_daily = ctk.CTkButton(btn_frame, text="Daily Report", command=show_daily_report)
btn_daily.grid(row=0, column=0, padx=5)

btn_weekly = ctk.CTkButton(btn_frame, text="Weekly Report", command=show_weekly_report)
btn_weekly.grid(row=0, column=1, padx=5)

btn_monthly = ctk.CTkButton(btn_frame, text="Monthly Report", command=show_monthly_report)
btn_monthly.grid(row=0, column=2, padx=5)

btn_top_absentees = ctk.CTkButton(btn_frame, text="Top Absentees", command=show_top_absentees)
btn_top_absentees.grid(row=0, column=3, padx=5)

btn_low_attendance = ctk.CTkButton(btn_frame, text="Low Attendance Alert", command=show_low_attendance)
btn_low_attendance.grid(row=0, column=4, padx=5)

root.mainloop()