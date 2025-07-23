import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, MULTIPLE, Listbox, Scrollbar
import os

class CSVDeDuplicatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Akarshans Edge CSV De-Duplicator and Cleaner")
        self.root.geometry("500x550")
        self.root.resizable(False, False)

        self.selected_file = None
        self.df = None
        self.mobile_column_var = tk.StringVar()
        self.mobile_column_var.set("Select Mobile Column (Optional)")

        # UI Components
        self.setup_widgets()

    def setup_widgets(self):
        tk.Label(self.root, text="Step 1: Select a CSV File").pack(pady=10)
        tk.Button(self.root, text="Browse CSV...", command=self.load_csv).pack()

        self.status_label = tk.Label(self.root, text="", fg="green")
        self.status_label.pack(pady=5)

        tk.Label(self.root, text="Step 2: Select Column(s) to Deduplicate On").pack(pady=(15, 5))

        frame = tk.Frame(self.root)
        frame.pack()

        self.column_listbox = Listbox(frame, selectmode=MULTIPLE, width=50, height=8)
        self.column_listbox.pack(side=tk.LEFT, padx=10)

        scrollbar = Scrollbar(frame, orient="vertical")
        scrollbar.config(command=self.column_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        self.column_listbox.config(yscrollcommand=scrollbar.set)

        tk.Label(self.root, text="Step 3: Select Mobile Number Column (Optional)").pack(pady=(10, 5))
        self.mobile_dropdown = tk.OptionMenu(self.root, self.mobile_column_var, "")
        self.mobile_dropdown.pack()

        tk.Label(self.root, text="Step 4: Output Filenames").pack(pady=(15, 5))
        self.clean_filename_entry = tk.Entry(self.root, width=40)
        self.clean_filename_entry.pack(pady=2)
        self.clean_filename_entry.insert(0, "cleaned_data")  # default name

        self.bad_filename_entry = tk.Entry(self.root, width=40)
        self.bad_filename_entry.pack(pady=2)
        self.bad_filename_entry.insert(0, "bad_data")  # default name

        # Action Buttons
        tk.Button(self.root, text="Preview Duplicates", command=self.preview_duplicates).pack(pady=10)
        tk.Button(self.root, text="CSV De-Dup", command=self.deduplicate_and_save, bg="#4CAF50", fg="white").pack(pady=5)
        tk.Button(self.root, text="Filter Bad Data", command=self.filter_bad_data, bg="#f44336", fg="white").pack(pady=5)

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

    def get_output_paths(self):
        base_dir = os.path.dirname(self.selected_file)
        clean_name = self.clean_filename_entry.get().strip()
        bad_name = self.bad_filename_entry.get().strip()
        clean_path = os.path.join(base_dir, f"{clean_name}.csv") if clean_name else None
        bad_path = os.path.join(base_dir, f"{bad_name}.csv") if bad_name else None
        return clean_path, bad_path

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

        clean_path, _ = self.get_output_paths()
        if not clean_path:
            messagebox.showwarning("Missing Filename", "Please provide a filename for the cleaned data.")
            return

        try:
            df_deduped = self.df.drop_duplicates(subset=selected_columns)
            if df_deduped.empty:
                messagebox.showwarning("Empty Output", "All rows were removed. No valid data to save.")
                return

            df_deduped.to_csv(clean_path, index=False)
            self.df = df_deduped.copy()
            messagebox.showinfo("Done", f"✅ Saved DEDUPLICATED file: {clean_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

    def filter_bad_data(self):
        if self.df is None:
            messagebox.showwarning("No File", "Please load a CSV file first!")
            return

        mobile_col = self.mobile_column_var.get()
        if mobile_col == "Select Mobile Column (Optional)":
            messagebox.showwarning("No Mobile Column", "Please select a mobile number column for filtering bad data.")
            return
        if mobile_col not in self.df.columns:
            messagebox.showerror("Error", f"Selected mobile column '{mobile_col}' not found in data.")
            return

        clean_path, bad_path = self.get_output_paths()
        if not clean_path or not bad_path:
            messagebox.showwarning("Missing Filenames", "Please provide filenames for both cleaned and bad data.")
            return

        try:
            is_bad = self.df[mobile_col].astype(str).str.len() > 14
            is_bad |= ~self.df[mobile_col].astype(str).str.match(r'^\+?\d+$')
            bad_data = self.df[is_bad].copy()
            filtered_data = self.df[~is_bad]

            if filtered_data.empty:
                messagebox.showwarning("Empty Output", "All rows were filtered out. No valid data to save.")
                return

            filtered_data.to_csv(clean_path, index=False)
            messages = [f"✅ Saved FILTERED file: {clean_path}", f"🚫 {len(bad_data)} bad rows filtered."]

            if not bad_data.empty:
                bad_data.to_csv(bad_path, index=False)
                messages.append(f"⚠️ Saved BAD DATA file: {bad_path} ({len(bad_data)} rows)")

            self.df = filtered_data.copy()
            messagebox.showinfo("Done", "\n".join(messages))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to filter data:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVDeDuplicatorApp(root)
    root.mainloop()
