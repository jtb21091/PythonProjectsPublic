import tkinter as tk
from tkinter import messagebox

# Sample percentile data for illustration
percentile_data = {
    1600: 99,
    1550: 99,
    1500: 98,
    1450: 97,
    1400: 95,
    1350: 92,
    1300: 88,
    1250: 82,
    1200: 74,
    1150: 65,
    1100: 55,
    1050: 45,
    1000: 35,
    950: 25,
    900: 15,
    850: 10,
    800: 5,
    750: 2,
    700: 1
}

def find_percentile(score):
    for s in sorted(percentile_data.keys(), reverse=True):
        if score >= s:
            return percentile_data[s]
    return 0  # If score is below the lowest score in the dataset

def submit():
    try:
        score = int(entry.get())
        if 0 <= score <= 1600:
            percentile = find_percentile(score)
            result_label.config(text=f"Percentile Rank: {percentile}th percentile")
        else:
            messagebox.showerror("Invalid Score", "Please enter a score between 0 and 1600.")
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid numerical score.")

# GUI setup
root = tk.Tk()
root.title("SAT Percentile Finder")

frame = tk.Frame(root, padx=20, pady=20)
frame.pack(padx=10, pady=10)

label = tk.Label(frame, text="Enter your SAT score:")
label.grid(row=0, column=0, padx=5, pady=5)

entry = tk.Entry(frame)
entry.grid(row=0, column=1, padx=5, pady=5)

button = tk.Button(frame, text="Find Percentile", command=submit)
button.grid(row=1, columnspan=2, pady=10)

result_label = tk.Label(frame, text="")
result_label.grid(row=2, columnspan=2, pady=5)

root.mainloop()
