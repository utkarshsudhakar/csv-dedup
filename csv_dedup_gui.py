""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, MULTIPLE, Listbox, Scrollbar
import pandas as pd
import os
from simple_salesforce import Salesforce, SalesforceLogin

class CSVDeDuplicatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Akarshans Edge Data Tool")
        self.root.geometry("800x700")
        self.root.resizable(False, False)

        self.selected_file = None
        self.df = None
        self.sf = None
        self.sf_objects = []
        self.selected_object = tk.StringVar()
        self.mobile_column_var = tk.StringVar()
        self.mobile_column_var.set("Select Mobile Column (Optional)")

        self.setup_widgets()

    def setup_widgets(self):
        notebook = ttk.Notebook(self.root)
        self.dedup_frame = ttk.Frame(notebook)
        self.salesforce_frame = ttk.Frame(notebook)

        notebook.add(self.dedup_frame, text="CSV De-Dup & Clean")
        notebook.add(self.salesforce_frame, text="Salesforce Wizard")
        notebook.pack(expand=True, fill='both')

        self.setup_dedup_tab()
        self.setup_salesforce_tab()

    def setup_dedup_tab(self):
        tk.Label(self.dedup_frame, text="Step 1: Select a CSV File").pack(pady=10)
        tk.Button(self.dedup_frame, text="Browse CSV...", command=self.load_csv).pack()

        self.status_label = tk.Label(self.dedup_frame, text="", fg="green")
        self.status_label.pack(pady=5)

        tk.Label(self.dedup_frame, text="Step 2: Select Column(s) to Deduplicate On").pack(pady=(15, 5))

        frame = tk.Frame(self.dedup_frame)
        frame.pack()

        self.column_listbox = Listbox(frame, selectmode=MULTIPLE, width=50, height=8)
        self.column_listbox.pack(side=tk.LEFT, padx=10)

        scrollbar = Scrollbar(frame, orient="vertical")
        scrollbar.config(command=self.column_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.column_listbox.config(yscrollcommand=scrollbar.set)

        tk.Label(self.dedup_frame, text="Step 3: Select Mobile Number Column (Optional)").pack(pady=(10, 5))
        self.mobile_dropdown = tk.OptionMenu(self.dedup_frame, self.mobile_column_var, "")
        self.mobile_dropdown.pack()

        tk.Button(self.dedup_frame, text="Preview Duplicates", command=self.preview_duplicates).pack(pady=10)
        tk.Button(self.dedup_frame, text="Deduplicate and Save", command=self.deduplicate_and_save, bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(self.dedup_frame, text="Filter Bad Data and Save", command=self.filter_bad_data, bg="#f39c12", fg="white").pack(pady=5)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return
        try:
            self.df = pd.read_csv(file_path)
            self.selected_file = file_path
            self.column_listbox.delete(0, tk.END)
            columns = list(self.df.columns)
            for col in columns:
                self.column_listbox.insert(tk.END, col)

            menu = self.mobile_dropdown["menu"]
            menu.delete(0, "end")
            for col in columns:
                menu.add_command(label=col, command=lambda value=col: self.mobile_column_var.set(value))
            self.mobile_column_var.set("Select Mobile Column (Optional)")

            self.status_label.config(text=f"✅ Loaded: {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load CSV:\n{e}")

    def get_selected_columns(self):
        selected_indices = self.column_listbox.curselection()
        return [self.column_listbox.get(i) for i in selected_indices]

    def preview_duplicates(self):
        if self.df is None:
            messagebox.showwarning("No File", "Please load a CSV file first.")
            return
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            messagebox.showwarning("No Columns", "Please select one or more columns.")
            return
        before = len(self.df)
        after = len(self.df.drop_duplicates(subset=selected_columns))
        removed = before - after
        messagebox.showinfo("Preview", f"{removed} duplicate rows will be removed based on:\n{', '.join(selected_columns)}")

    def deduplicate_and_save(self):
        if self.df is None:
            messagebox.showwarning("No File", "Please load a CSV file first!")
            return
        selected_columns = self.get_selected_columns()
        if not selected_columns:
            messagebox.showwarning("No Columns", "Please select one or more columns.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Save Deduplicated File")
        if not save_path:
            return

        try:
            df_cleaned = self.df.drop_duplicates(subset=selected_columns)
            df_cleaned.to_csv(save_path, index=False)
            messagebox.showinfo("Saved", f"Saved deduplicated file: {save_path}")
            self.df = df_cleaned.copy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def filter_bad_data(self):
        if self.df is None:
            messagebox.showwarning("No File", "Please load a CSV file first!")
            return

        mobile_col = self.mobile_column_var.get()
        if mobile_col == "Select Mobile Column (Optional)":
            messagebox.showwarning("Column Missing", "Select a mobile number column.")
            return

        clean_path = filedialog.asksaveasfilename(title="Save Clean Data As", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not clean_path:
            return

        bad_path = filedialog.asksaveasfilename(title="Save Bad Data As", defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not bad_path:
            return

        try:
            is_bad = self.df[mobile_col].astype(str).str.len() > 14
            is_bad = is_bad | ~self.df[mobile_col].astype(str).str.match(r'^\+?\d+$')
            bad_data = self.df[is_bad].copy()
            clean_data = self.df[~is_bad]

            clean_data.to_csv(clean_path, index=False)
            bad_data.to_csv(bad_path, index=False)

            messagebox.showinfo("Saved", f"Saved clean data to: {clean_path}\nSaved bad data to: {bad_path}")
            self.df = clean_data.copy()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def setup_salesforce_tab(self):
        frame = tk.Frame(self.salesforce_frame)
        frame.pack(pady=10)

        tk.Label(frame, text="Salesforce Username").grid(row=0, column=0, sticky="e")
        tk.Label(frame, text="Password").grid(row=1, column=0, sticky="e")
        tk.Label(frame, text="Security Token").grid(row=2, column=0, sticky="e")
        tk.Label(frame, text="Domain (login/sandbox)").grid(row=3, column=0, sticky="e")

        self.sf_user = tk.Entry(frame, width=40)
        self.sf_pass = tk.Entry(frame, show='*', width=40)
        self.sf_token = tk.Entry(frame, width=40)
        self.sf_domain = tk.Entry(frame, width=40)

        self.sf_user.grid(row=0, column=1)
        self.sf_pass.grid(row=1, column=1)
        self.sf_token.grid(row=2, column=1)
        self.sf_domain.grid(row=3, column=1)

        tk.Button(frame, text="Login to Salesforce", command=self.login_salesforce, bg="#2980b9", fg="white").grid(row=4, columnspan=2, pady=10)
        self.sf_status = tk.Label(frame, text="", fg="green")
        self.sf_status.grid(row=5, columnspan=2)

        self.sf_object_menu = ttk.Combobox(frame, textvariable=self.selected_object, state='readonly', width=37)
        self.sf_object_menu.grid(row=6, column=1, pady=5)
        tk.Label(frame, text="Select Object").grid(row=6, column=0, sticky="e")

        tk.Button(frame, text="Export to CSV", command=self.export_salesforce_data, bg="#27ae60", fg="white").grid(row=7, columnspan=2, pady=5)
        tk.Button(frame, text="Import from CSV", command=self.import_salesforce_data, bg="#c0392b", fg="white").grid(row=8, columnspan=2, pady=5)

    def login_salesforce(self):
        try:
            username = self.sf_user.get()
            password = self.sf_pass.get()
            token = self.sf_token.get()
            domain = self.sf_domain.get()

            self.sf = Salesforce(username=username, password=password, security_token=token, domain=domain)
            self.sf_objects = sorted(self.sf.describe()['sobjects'], key=lambda o: o['name'])
            object_names = [obj['name'] for obj in self.sf_objects if obj['createable'] and obj['queryable']]
            self.sf_object_menu['values'] = object_names
            self.selected_object.set(object_names[0] if object_names else '')
            self.sf_status.config(text="✅ Connected to Salesforce")
        except Exception as e:
            self.sf_status.config(text=f"❌ Failed: {e}", fg="red")

    def export_salesforce_data(self):
        if not self.sf:
            messagebox.showwarning("Salesforce", "Please login first.")
            return

        object_name = self.selected_object.get()
        if not object_name:
            messagebox.showwarning("Select Object", "Please select a Salesforce object.")
            return

        try:
            query_desc = self.sf.__getattr__(object_name).describe()
            fields = [f['name'] for f in query_desc['fields']]
            query = f"SELECT {', '.join(fields)} FROM {object_name}"
            result = self.sf.query_all(query)
            records = result['records']
            for r in records:
                r.pop('attributes', None)

            df = pd.DataFrame(records)
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Save Exported CSV")
            if file_path:
                df.to_csv(file_path, index=False)
                messagebox.showinfo("Success", f"Exported data to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def import_salesforce_data(self):
        if not self.sf:
            messagebox.showwarning("Salesforce", "Please login first.")
            return

        object_name = self.selected_object.get()
        if not object_name:
            messagebox.showwarning("Select Object", "Please select a Salesforce object.")
            return

        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not file_path:
            return

        try:
            df = pd.read_csv(file_path)
            inserted = 0
            for i, record in df.iterrows():
                data = record.dropna().to_dict()
                self.sf.__getattr__(object_name).create(data)
                inserted += 1
            messagebox.showinfo("Success", f"Inserted {inserted} records into {object_name}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVDeDuplicatorApp(root)
    root.mainloop()
