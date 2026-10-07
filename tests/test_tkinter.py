import tkinter as tk
print("Testing Tkinter...")

root = tk.Tk()
root.title("Tkinter Test")
label = tk.Label(root, text="✅ Tkinter is working!")
label.pack(padx=50, pady=50)
root.after(2000, root.quit)  # Close after 2 seconds
root.mainloop()
print("Tkinter test passed!")