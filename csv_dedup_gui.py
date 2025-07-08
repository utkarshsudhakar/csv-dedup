import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, MULTIPLE, Listbox, Scrollbar
import os

class CSVDeDuplicatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CSV De-Duplicator")
        self.root.geometry("500x400")
        self.root.resizable(False, False)

        self.selected_file = None
        self.df = None

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
            for col in self.df.columns:
                self.column_listbox.insert(tk.END, col)
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

        output_filename = simpledialog.askstring("Save As", "Enter name for output CSV (no extension):")
        if not output_filename:
            return

        try:
            df_cleaned = self.df.drop_duplicates(subset=selected_columns)
            output_path = os.path.join(
                os.path.dirname(self.selected_file),
                f"{output_filename}.csv"
            )
            df_cleaned.to_csv(output_path, index=False)
            removed = len(self.df) - len(df_cleaned)
            messagebox.showinfo("Success", f"✅ Saved to: {output_path}\n🧹 {removed} duplicates removed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CSVDeDuplicatorApp(root)
    root.mainloop()

