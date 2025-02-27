import cv2
import qrcode
import mysql.connector
import pandas as pd
import customtkinter as ctk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from pyzbar.pyzbar import decode
import os

# Database Connection
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        port=3308,
        user="root",
        password="",
        database="qr_attendance_db"
    )

def generate_qr():
    student_id = entry_id.get().strip()
    name = entry_name.get().strip()
    email = entry_email.get().strip()
    contact = entry_contact.get().strip()

    if not student_id or not name or not email or not contact:
        messagebox.showerror("Error", "Please enter all fields!")
        return

    qr_data = f"{student_id},{name},{email},{contact}"
    qr = qrcode.make(qr_data)

    os.makedirs("qr_codes", exist_ok=True)
    qr_path = f"qr_codes/{student_id}.png"
    qr.save(qr_path)

    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO students (student_id, name, email, contact, qr_code) VALUES (%s, %s, %s, %s, %s)",
                       (student_id, name, email, contact, qr_path))
        db.commit()
        messagebox.showinfo("Success", "QR Code generated and student added!")
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
    finally:
        db.close()

    img = Image.open(qr_path).resize((150, 150))
    qr_img = ImageTk.PhotoImage(img)
    qr_label.configure(image=qr_img)
    qr_label.image = qr_img

def scan_qr():
    cap = cv2.VideoCapture(0)

    def update_frame():
        ret, frame = cap.read()
        if not ret:
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        decoded_objs = decode(frame)
        for obj in decoded_objs:
            data = obj.data.decode("utf-8")
            student_id, name, email, contact = data.split(",")

            db = connect_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO attendance (student_id) VALUES (%s)", (student_id,))
            db.commit()
            db.close()

            messagebox.showinfo("Success", f"Attendance recorded for {name}")

            cap.release()
            return

        img = Image.fromarray(frame)
        img = img.resize((300, 220))  # Adjust size
        img_tk = ImageTk.PhotoImage(img)

        camera_label.img_tk = img_tk
        camera_label.configure(image=img_tk)
        root.after(10, update_frame)

    update_frame()

def view_attendance():
    db = connect_db()
    query = """SELECT a.student_id, s.name, s.email, s.contact, a.scan_time 
               FROM attendance a 
               JOIN students s ON a.student_id = s.student_id"""
    df = pd.read_sql(query, db)
    db.close()

    for item in tree.get_children():
        tree.delete(item)

    for row in df.itertuples(index=False):
        tree.insert("", "end", values=row)
def fetch_students():
    db = connect_db()
    query = "SELECT student_id, name, email, contact FROM students"
    df = pd.read_sql(query, db)
    db.close()
    return df

def fetch_attendance_report():
    db = connect_db()
    query = "SELECT s.student_id, s.name, s.email, s.contact, COUNT(a.student_id) AS attendance_count FROM attendance a JOIN students s ON a.student_id = s.student_id GROUP BY a.student_id"
    df = pd.read_sql(query, db)
    db.close()
    return df

# UI Setup
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("QR Code Attendance System")
root.geometry("900x500")

# Tab Configuration
tabview = ctk.CTkTabview(root)
tabview.pack(expand=True, fill="both", padx=10, pady=10)

tab1 = tabview.add("Attendance System")
tab2 = tabview.add("List of Students")
tab3 = tabview.add("Full Attendance Report")

# Main Frame in Tab 1
main_frame = ctk.CTkFrame(tab1)
main_frame.pack(pady=10, padx=10, fill="both", expand=True)

left_frame = ctk.CTkFrame(main_frame, width=350)
left_frame.pack(side="left", fill="y", padx=10, pady=5)

camera_label = ctk.CTkLabel(left_frame, text="QR Scanner", width=300, height=220, fg_color="gray", corner_radius=10)
camera_label.pack(pady=10)

# Input Fields
ctk.CTkLabel(left_frame, text="Student ID:").pack(pady=2)
entry_id = ctk.CTkEntry(left_frame)
entry_id.pack(pady=2, padx=5, fill="x")

ctk.CTkLabel(left_frame, text="Student Name:").pack(pady=2)
entry_name = ctk.CTkEntry(left_frame)
entry_name.pack(pady=2, padx=5, fill="x")

ctk.CTkLabel(left_frame, text="Email:").pack(pady=2)
entry_email = ctk.CTkEntry(left_frame)
entry_email.pack(pady=2, padx=5, fill="x")

ctk.CTkLabel(left_frame, text="Contact Number:").pack(pady=2)
entry_contact = ctk.CTkEntry(left_frame)
entry_contact.pack(pady=2, padx=5, fill="x")

frame_buttons = ctk.CTkFrame(left_frame)
frame_buttons.pack(pady=10, fill="x")

ctk.CTkButton(frame_buttons, text="Generate QR Code", command=generate_qr, corner_radius=20).pack(pady=3, padx=5, fill="x")
ctk.CTkButton(frame_buttons, text="Scan QR Code", command=scan_qr, fg_color="green", corner_radius=20).pack(pady=3, padx=5, fill="x")
ctk.CTkButton(frame_buttons, text="View Attendance", command=view_attendance, fg_color="orange", corner_radius=20).pack(pady=3, padx=5, fill="x")

qr_label = ctk.CTkLabel(left_frame, text="QR Preview", width=150, height=150, fg_color="gray", corner_radius=10)
qr_label.pack(pady=10)

# Attendance Table in Tab 1
right_frame = ctk.CTkFrame(main_frame)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

columns = ("Student ID", "Name", "Email", "Contact", "Scan Time")
tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(fill="both", expand=True)

# Student List in Tab 2
student_frame = ctk.CTkFrame(tab2)
student_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("Student ID", "Name", "Email", "Contact")
student_tree = ttk.Treeview(student_frame, columns=columns, show="headings", height=10)
for col in columns:
    student_tree.heading(col, text=col)
    student_tree.column(col, anchor="center")
student_tree.pack(fill="both", expand=True)

def update_student_list():
    for item in student_tree.get_children():
        student_tree.delete(item)
    for row in fetch_students().itertuples(index=False):
        student_tree.insert("", "end", values=row)
update_student_list()

# Add Student Form
add_student_frame = ctk.CTkFrame(tab2)
add_student_frame.pack(pady=10, padx=10, fill="x")

ctk.CTkLabel(add_student_frame, text="Student ID:").grid(row=0, column=0, padx=5, pady=5)
entry_new_id = ctk.CTkEntry(add_student_frame)
entry_new_id.grid(row=0, column=1, padx=5, pady=5)

ctk.CTkLabel(add_student_frame, text="Name:").grid(row=1, column=0, padx=5, pady=5)
entry_new_name = ctk.CTkEntry(add_student_frame)
entry_new_name.grid(row=1, column=1, padx=5, pady=5)

ctk.CTkLabel(add_student_frame, text="Email:").grid(row=2, column=0, padx=5, pady=5)
entry_new_email = ctk.CTkEntry(add_student_frame)
entry_new_email.grid(row=2, column=1, padx=5, pady=5)

ctk.CTkLabel(add_student_frame, text="Contact:").grid(row=3, column=0, padx=5, pady=5)
entry_new_contact = ctk.CTkEntry(add_student_frame)
entry_new_contact.grid(row=3, column=1, padx=5, pady=5)

def add_student():
    student_id = entry_new_id.get().strip()
    name = entry_new_name.get().strip()
    email = entry_new_email.get().strip()
    contact = entry_new_contact.get().strip()
    if not student_id or not name or not email or not contact:
        messagebox.showerror("Error", "All fields are required!")
        return
    db = connect_db()
    cursor = db.cursor()
    try:
        cursor.execute("INSERT INTO students (student_id, name, email, contact) VALUES (%s, %s, %s, %s)",
                       (student_id, name, email, contact))
        db.commit()
        messagebox.showinfo("Success", "Student added successfully!")
        update_student_list()
    except mysql.connector.Error as err:
        messagebox.showerror("Database Error", f"Error: {err}")
    finally:
        db.close()

ctk.CTkButton(add_student_frame, text="Add Student", command=add_student).grid(row=4, columnspan=2, pady=10)

# Attendance Report in Tab 3
report_frame = ctk.CTkFrame(tab3)
report_frame.pack(fill="both", expand=True, padx=10, pady=10)

columns = ("Student ID", "Name", "Email", "Contact", "Attendance Count")
report_tree = ttk.Treeview(report_frame, columns=columns, show="headings", height=10)
for col in columns:
    report_tree.heading(col, text=col)
    report_tree.column(col, anchor="center")
report_tree.pack(fill="both", expand=True)

total_label = ctk.CTkLabel(tab3, text="Total Present: 0", font=("Arial", 14, "bold"))
total_label.pack(pady=10)

def update_attendance_report():
    for item in report_tree.get_children():
        report_tree.delete(item)
    data = fetch_attendance_report()
    for row in data.itertuples(index=False):
        report_tree.insert("", "end", values=row)
    total_label.configure(text=f"Total Present: {len(data)}")

update_attendance_report()

root.mainloop()
