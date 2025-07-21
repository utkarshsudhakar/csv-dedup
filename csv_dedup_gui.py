import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, MULTIPLE, Listbox, Scrollbar
import os

class CSVDeDuplicatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Akarshans Edge CSV De-Duplicator")
        self.root.geometry("500x450")
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

        tk.Button(self.root, text="Preview Duplicates", command=self.preview_duplicates).pack(pady=10)
        tk.Button(self.root, text="Deduplicate and Save", command=self.deduplicate_and_save, bg="#4CAF50", fg="white").pack(pady=5)

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

            # Update dropdown
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

        output_filename = tk.simpledialog.askstring("Save As", "Enter name for CLEANED output CSV (no extension):")
        if not output_filename:
            return

        mobile_col = self.mobile_column_var.get()
        if mobile_col == "Select Mobile Column (Optional)":
            mobile_col = None

        try:
            df_cleaned = self.df.drop_duplicates(subset=selected_columns)

            bad_data = pd.DataFrame()
            if mobile_col and mobile_col in df_cleaned.columns:
                is_bad = df_cleaned[mobile_col].astype(str).str.len() > 14
                is_bad = is_bad | ~df_cleaned[mobile_col].astype(str).str.match(r'^\+?\d+$')
                bad_data = df_cleaned[is_bad].copy()
                df_cleaned = df_cleaned[~is_bad]

            if df_cleaned.empty:
                messagebox.showwarning("Empty Output", "All rows were filtered out. No valid data to save.")
                return

            output_path = os.path.join(os.path.dirname(self.selected_file), f"{output_filename}.csv")
            df_cleaned.to_csv(output_path, index=False)

            messages = [f"✅ Saved CLEANED file: {output_path}", f"🧹 {len(self.df) - len(df_cleaned)} duplicates removed."]

            if not bad_data.empty:
                bad_output_filename = tk.simpledialog.askstring("Save As", "Enter name for BAD DATA output CSV (no extension):")
                if bad_output_filename:
                    bad_path = os.path.join(os.path.dirname(self.selected_file), f"{bad_output_filename}.csv")
                    bad_data.to_csv(bad_path, index=False)
                    messages.append(f"⚠️ Saved BAD DATA file: {bad_path} ({len(bad_data)} rows)")

            self.df = df_cleaned.copy()
            messagebox.showinfo("Done", "\n".join(messages))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVDeDuplicatorApp(root)
    root.mainloop()
