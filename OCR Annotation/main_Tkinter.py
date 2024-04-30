import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import pandas as pd
import os

# Define global variables
csv_file_path = ""         # Initialize with empty string
image_folder_path = ""     # Initialize with empty string

df = pd.DataFrame()        # Empty DataFrame to store annotations
image_references = {}      # Dictionary to hold references to images

def display_image_and_annotation(image_path, annotation):
    image = Image.open(image_path)
    image.thumbnail((500, 500))  # Adjust size as needed
    photo = ImageTk.PhotoImage(image)
    image_label.config(image=photo)
    image_label.image = photo
    annotation_entry.delete(0, tk.END)
    annotation_entry.insert(0, annotation)

def update_annotation(file_name, new_annotation):
    global df
    df.loc[df['filename'] == file_name, 'words'] = new_annotation
    df.to_csv(csv_file_path, index=False)

def delete_image_and_annotation(file_name):
    global df, tree
    try:
        os.remove(os.path.join(image_folder_path, file_name))
        df.drop(df[df['filename'] == file_name].index, inplace=True)
        df.to_csv(csv_file_path, index=False)
        for item in tree.get_children():
            if tree.item(item, 'text') == file_name:
                tree.delete(item)
                break
    except Exception as e:
        messagebox.showerror("Error", f"Error deleting file: {str(e)}")

def update_previous_annotations(current_file_name):
    global previous_canvas, previous_annotations_frame
    
    # Clear previous annotations
    for widget in previous_annotations_frame.winfo_children():
        widget.destroy()

    # Get index of current selected file
    current_index = df[df['filename'] == current_file_name].index[0]

    # Create a canvas widget to hold annotations with a vertical scrollbar
    previous_canvas = tk.Canvas(previous_annotations_frame, bg="lightgrey")
    previous_canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)

    # Attach mousewheel event to canvas for scrolling
    previous_canvas.bind_all("<MouseWheel>", on_mouse_wheel)

    # Create a frame inside the canvas to contain annotations
    previous_annotations_frame_inner = tk.Frame(previous_canvas, bg="lightgrey")
    previous_canvas.create_window((0, 0), window=previous_annotations_frame_inner, anchor=tk.NW)

    # Display annotations of previous files
    for i in range(current_index):
        filename = df.loc[i, 'filename']
        annotation = df.loc[i, 'words']

        # Create a frame to hold the annotation and copy button
        prev_annotation_frame = tk.Frame(previous_annotations_frame_inner, bg="lightgrey")
        prev_annotation_frame.pack(fill=tk.X, padx=10, pady=2)

        # Display filename and annotation in a label
        prev_annotation_label = tk.Label(prev_annotation_frame, text=f"{filename}: {annotation}", bg="lightgrey")
        prev_annotation_label.pack(side=tk.LEFT)

        # Create a copy button to copy the annotation
        copy_button = tk.Button(prev_annotation_frame, text="Copy", command=lambda ann=annotation: copy_annotation(ann))
        copy_button.pack(side=tk.RIGHT)

    # Add scrollbar to the canvas
    scrollbar = tk.Scrollbar(previous_annotations_frame, orient=tk.VERTICAL, command=previous_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    previous_canvas.configure(yscrollcommand=scrollbar.set)

    # Update the scroll region after widgets are added
    previous_annotations_frame_inner.update_idletasks()
    previous_canvas.configure(scrollregion=previous_canvas.bbox("all"))

def copy_annotation(annotation_text):
    annotation_entry.delete(0, tk.END)
    annotation_entry.insert(0, annotation_text)

def on_mouse_wheel(event):
    previous_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

def show_check_mark():
    check_mark_label.pack()  # Show the label
    root.after(500, hide_check_mark)  # Hide the label after 0.5 seconds

def hide_check_mark():
    check_mark_label.pack_forget()  # Hide the label

def on_select(event):
    global tree_selection
    item = tree.focus()
    if item:
        tree_selection = item
        selected_file_name = tree.item(item, 'text')
        selected_row = df[df['filename'] == selected_file_name]
        selected_annotation = selected_row['words'].values[0]
        selected_image_path = f"{image_folder_path}/{selected_file_name}"
        display_image_and_annotation(selected_image_path, selected_annotation)
        update_previous_annotations(selected_file_name)

def update_annotation_command():
    if tree_selection:
        new_annotation = annotation_entry.get()
        selected_file_name = tree.item(tree_selection, 'text')
        update_annotation(selected_file_name, new_annotation)
        # success_label.config(text="Annotation Updated Successfully!")
        success_label.after(3000, clear_success_message)
        update_previous_annotations(selected_file_name)
        show_check_mark()  # Call the function to show the check mark
    else:
        messagebox.showerror("Error", "Please select a file.")

def delete_image_command():
    if tree_selection:
        selected_file_name = tree.item(tree_selection, 'text')
        delete_image_and_annotation(selected_file_name)
        success_label.config(text="Image and Annotation Deleted Successfully!")
        success_label.after(3000, clear_success_message)
        update_previous_annotations(selected_file_name)
    else:
        messagebox.showerror("Error", "Please select a file.")

def clear_success_message():
    success_label.config(text="")

def select_folder():
    global image_folder_path
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        image_folder_path = folder_selected
        refresh_treeview()

def select_csv_file():
    global csv_file_path
    file_selected = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
    if file_selected:
        csv_file_path = file_selected
        refresh_treeview()

def refresh_treeview():
    global tree, df
    tree.delete(*tree.get_children())
    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path)
        for filename in df['filename']:
            image_path = f"{image_folder_path}/{filename}"
            annotation = df[df['filename'] == filename]['words'].values[0]
            item = tree.insert("", "end", text=filename, values=(image_path, annotation, ""))

def main():
    global root, tree, tree_selection, image_label, annotation_entry, previous_annotations_frame, check_mark_label
    root = tk.Tk()
    root.title("Annotation Recheck App")
    root.configure(bg="lightgrey")  # Set background color

    # Frame for files list
    files_frame = tk.Frame(root, bg="lightgrey")
    files_frame.pack(side=tk.LEFT, fill=tk.Y)

    # Upload buttons
    select_folder_button = tk.Button(files_frame, text="Select Image Folder", command=select_folder)
    select_folder_button.pack(pady=10)

    select_csv_button = tk.Button(files_frame, text="Select CSV File", command=select_csv_file)
    select_csv_button.pack(pady=10)

    # Treeview for displaying filenames
    tree = ttk.Treeview(files_frame, columns=("Image", "Annotation", "Edit"), show="headings", selectmode="browse")
    tree.heading("Image", text="Image")
    tree.heading("Annotation", text="Annotation")
    tree.heading("Edit", text="Edit")
    tree.pack(side=tk.LEFT, fill=tk.Y)

    # Bind event for selecting a row
    tree.bind("<<TreeviewSelect>>", on_select)

    # Frame for image display and annotation editing
    image_frame = tk.Frame(root, bg="lightgrey")
    image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Display image and annotation
    image_label = tk.Label(image_frame)
    image_label.pack(pady=10)
    annotation_entry = tk.Entry(image_frame, width=50)
    annotation_entry.pack(pady=10)

    # Frame for previous annotations
    previous_annotations_frame = tk.Frame(root, bd=2, relief=tk.RIDGE, bg="lightgrey")
    previous_annotations_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

    # Update button
    update_button = tk.Button(image_frame, text="Update Annotation", command=update_annotation_command)
    update_button.pack(pady=10)

    # Delete button
    delete_button = tk.Button(image_frame, text="Delete Image", command=delete_image_command)
    delete_button.pack(pady=10)

    # Success message label
    global success_label
    success_label = tk.Label(root, fg="green", bg="lightgrey")
    success_label.pack()

    # Load check mark image
    check_mark_image = Image.open("Checkmark.jpg")
    check_mark_image.thumbnail((100, 100))  # Adjust size as needed
    check_mark_image = ImageTk.PhotoImage(check_mark_image)

    # Create a label to display the check mark
    check_mark_label = tk.Label(image_frame, image=check_mark_image, bg="lightgrey")
    check_mark_label.pack()  # Initially hide the label

    root.mainloop()

if __name__ == "__main__":
    main()
