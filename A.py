import tkinter as tk

class CheckBoxApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CheckBox App")
        
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)
        
        self.checkbuttons = []
        self.vars = []
        self.labels = ["Option 1", "Option 2", "Option 3", "Option 4"]
        
        self.create_checkbuttons()
        
        self.button = tk.Button(root, text="Get Checked Values", command=self.get_checked_values)
        self.button.pack(pady=10)
    
    def create_checkbuttons(self):
        for label in self.labels:
            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.frame, text=label, variable=var)
            cb.pack(anchor='w')
            self.checkbuttons.append(cb)
            self.vars.append(var)
    
    def get_checked_values(self):
        try:
            checked_values = [label for label, var in zip(self.labels, self.vars) if var.get()]
            print("Checked values:", checked_values)
            return checked_values
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

if __name__ == "__main__":
    root = tk.Tk()
    app = CheckBoxApp(root)
    root.mainloop()
