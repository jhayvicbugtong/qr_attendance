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
        port=3306,
        user="root",
        password="",
        database="qr_attendance_db"
    )

# Generate QR Code and Show Preview
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

# Scan QR Code and Mark Attendance
def scan_qr():
    cap = cv2.VideoCapture(0)

    def update_frame():
        ret, frame = cap.read()
        if not ret:
            return

        # Convert frame to RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Decode QR code
        decoded_objs = decode(frame)
        for obj in decoded_objs:
            data = obj.data.decode("utf-8")
            student_id, name, email, contact = data.split(",")

            # Save attendance in database
            db = connect_db()
            cursor = db.cursor()
            cursor.execute("INSERT INTO attendance (student_id) VALUES (%s)", (student_id,))
            db.commit()
            db.close()

            messagebox.showinfo("Success", f"Attendance recorded for {name}")

            cap.release()
            return  # Stop after detecting a QR code

        # Convert frame to ImageTk format
        img = Image.fromarray(frame)
        img = img.resize((300, 220))  # Adjust size
        img_tk = ImageTk.PhotoImage(img)

        # Update label
        camera_label.img_tk = img_tk
        camera_label.configure(image=img_tk)
        root.after(10, update_frame)  # Update every 10ms

    update_frame()


# View Attendance Records
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

# Modern UI with CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

root = ctk.CTk()
root.title("QR Code Attendance System")
root.geometry("900x500")

main_frame = ctk.CTkFrame(root)
main_frame.pack(pady=10, padx=10, fill="both", expand=True)

# Left Side - Inputs & Buttons
# Left Side - Inputs & Buttons
left_frame = ctk.CTkFrame(main_frame, width=350)
left_frame.pack(side="left", fill="y", padx=10, pady=5)

# Add Camera Feed Label to UI (AFTER left_frame is created)
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

# Right Side - Attendance Table
right_frame = ctk.CTkFrame(main_frame)
right_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

columns = ("Student ID", "Name", "Email", "Contact", "Scan Time")
tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=15)

for col in columns:
    tree.heading(col, text=col)
    tree.column(col, anchor="center")

tree.pack(fill="both", expand=True)

root.mainloop()
