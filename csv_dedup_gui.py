import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, MULTIPLE, Listbox, Scrollbar, simpledialog
import os

class CSVDeDuplicatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Akarshans Edge CSV De-Duplicator and Cleaner")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        self.selected_file = None
        self.df = None
        self.mobile_column_var = tk.StringVar()
        self.mobile_column_var.set("Select Mobile Column (Optional)")

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

        filename = simpledialog.askstring("Save As", "Enter filename for DEDUPLICATED data (no extension):")
        if not filename:
            return
        output_path = os.path.join(os.path.dirname(self.selected_file), f"{filename}.csv")

        try:
            df_deduped = self.df.drop_duplicates(subset=selected_columns)
            if df_deduped.empty:
                messagebox.showwarning("Empty Output", "All rows were removed. No valid data to save.")
                return
            df_deduped.to_csv(output_path, index=False)
            self.df = df_deduped.copy()
            messagebox.showinfo("Done", f"✅ Saved DEDUPLICATED file: {output_path}")
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

        def on_submit():
            clean_name = clean_entry.get().strip()
            bad_name = bad_entry.get().strip()
            if not clean_name or not bad_name:
                messagebox.showerror("Missing Input", "Please provide both filenames.")
                return
            popup.destroy()
            clean_path = os.path.join(os.path.dirname(self.selected_file), f"{clean_name}.csv")
            bad_path = os.path.join(os.path.dirname(self.selected_file), f"{bad_name}.csv")

            try:
                is_bad = self.df[mobile_col].astype(str).str.len() > 14
                is_bad |= ~self.df[mobile_col].astype(str).str.match(r'^\+?\d+$')
                bad_data = self.df[is_bad].copy()
                filtered_data = self.df[~is_bad]

                if filtered_data.empty:
                    messagebox.showwarning("Empty Output", "All rows were filtered out. No valid data to save.")
                    return

                filtered_data.to_csv(clean_path, index=False)
                messages = [f"✅ Saved CLEANED file: {clean_path}", f"🚫 {len(bad_data)} bad rows filtered."]

                if not bad_data.empty:
                    bad_data.to_csv(bad_path, index=False)
                    messages.append(f"⚠️ Saved BAD DATA file: {bad_path} ({len(bad_data)} rows)")

                self.df = filtered_data.copy()
                messagebox.showinfo("Done", "\n".join(messages))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to filter data:\n{e}")

        # Custom popup window for both filenames
        popup = tk.Toplevel(self.root)
        popup.title("Enter Output Filenames")
        popup.geometry("350x180")
        popup.grab_set()

        tk.Label(popup, text="Cleaned Data Filename (no extension):").pack(pady=(10, 2))
        clean_entry = tk.Entry(popup, width=30)
        clean_entry.pack()

        tk.Label(popup, text="Bad Data Filename (no extension):").pack(pady=(10, 2))
        bad_entry = tk.Entry(popup, width=30)
        bad_entry.pack()

        tk.Button(popup, text="Submit", command=on_submit, bg="#4CAF50", fg="white").pack(pady=15)

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVDeDuplicatorApp(root)
    root.mainloop()
