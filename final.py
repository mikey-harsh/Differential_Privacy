import pandas as pd
from diffprivlib.mechanisms.laplace import Laplace
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk  # Import Pillow for image handling
import subprocess  # For opening local applications/files

# Load the cleaned dataset
cleaned_dataset_path = 'dataset.csv'
df = pd.read_csv(cleaned_dataset_path)

# Function to mask Aadhaar numbers, phone numbers, and email addresses
def mask_sensitive_data(data, column):
    if column == 'Aadhaar Number':
        return data.apply(lambda x: '************' + str(x)[-4:] if pd.notnull(x) and len(str(x)) >= 4 else x)
    elif column == 'Mobile Number':
        return data.apply(lambda x: str(x)[:2] + '******' + str(x)[-2:] if pd.notnull(x) and len(str(x)) >= 10 else x)
    elif column == 'Email Address':
        return data.apply(lambda x: '*********' + x.split('@')[0][-4:] + '@' + x.split('@')[-1] if pd.notnull(x) and '@' in str(x) else x)
    else:
        return data

# Apply differential privacy (Laplace mechanism) to numeric data only
def apply_dp(data, dp_type='laplace', epsilon=1.0, sensitivity=None):
    if dp_type == 'laplace' and pd.api.types.is_numeric_dtype(data):
        if sensitivity is None:
            sensitivity = data.max() - data.min()  # Sensitivity calculation for numeric data
        laplace_mechanism = Laplace(epsilon=epsilon, sensitivity=sensitivity)
        return data.apply(lambda x: laplace_mechanism.randomise(x) if pd.notnull(x) else x)
    return data  # Skip non-numeric data

# Ensure numeric columns are clean (convert and handle errors)
def clean_numeric_column(data):
    data = pd.to_numeric(data, errors='coerce')  # Convert to numeric, replace invalid with NaN
    data.fillna(0, inplace=True)  # Handle NaN values by replacing them with 0 (or another suitable value)
    return data

# Create DP CSV based on selected category
def create_dp_csv(category, dp_type='laplace', epsilon=1.0):
    # Define categories and the columns they contain
    categories = {
        'Identity and Contact Information': ['Aadhaar Number', 'Name', 'Gender', 'Date of Birth', 'Address', 'Mobile Number', 'Email Address'],
        'Geographical and Demographic Details': ['State', 'City', 'Origin State', 'Religion', 'Caste', 'Education Level', 'Occupation', 'Household Size', 'Income Bracket'],
        'Aadhaar Usage and Linkages': ['Date of Aadhaar Issuance', 'Date of Last Aadhaar Update', 'Verification Status', 'Number of Times Aadhaar Used', 'Linked Services Count', 'Linked Bank Accounts', 'Mobile Connections Linked', 'Preferred Authentication Method', 'Authentication Mode Used', 'Frequency of Usage', 'Access Location'],
        'Programs and Healthcare Details': ['Subsidies Claimed', 'Government Schemes Accessed', 'Program Name', 'Scheme Enrollment Status', 'Vaccination Status', 'Health Insurance Linked', 'Consent Given for Data Sharing', 'Data Breach Status', 'Breach Date']
    }

    # Select the relevant columns for the chosen category
    if category not in categories:
        print(f"Category '{category}' not found.")
        return

    selected_columns = categories[category]
    dp_data = df[selected_columns].copy()

    # Apply differential privacy or masking
    for col in dp_data.columns:
        if col in ['Aadhaar Number', 'Mobile Number', 'Email Address']:
            # Apply masking to sensitive data
            dp_data[col] = mask_sensitive_data(dp_data[col], col)
        elif col in ['Gender', 'Address', 'Name', 'Religion', 'Caste', 'Occupation', 'State', 'City', 'Program Name']:  # Skip text columns
            # Leave text columns unchanged
            continue
        elif pd.api.types.is_numeric_dtype(dp_data[col]):
            # Clean numeric columns before applying DP
            dp_data[col] = clean_numeric_column(dp_data[col])
            sensitivity = dp_data[col].max() - dp_data[col].min()  # Sensitivity calculation for numeric data
            dp_data[col] = apply_dp(dp_data[col], dp_type, epsilon, sensitivity)
        else:
            # Exclude other non-modified columns
            continue

    # Save the processed data to a new CSV file
    dp_data.to_csv(f"dp_{category.replace(' ', '_').lower()}.csv", index=False)
    print(f"DP data for category '{category}' saved to 'dp_{category.replace(' ', '_').lower()}.csv'.")
    messagebox.showinfo("Success", f"DP data for '{category}' saved successfully!")

# Function to open Power BI dashboard
# Function to open Power BI dashboard
def open_power_bi_dashboard(category):
    # Map categories to local Power BI dashboard files
    dashboards = {
        'Identity and Contact Information': r"H:\Differential Privacy\Identity and Contact Information.pbix",
        'Geographical and Demographic Details': r"H:\Differential Privacy\Geographical and Demographic Details.pbix",
        'Aadhaar Usage and Linkages': r"H:\Differential Privacy\Aadhaar Usage and Linkages.pbix",
    }

    # Path to Power BI Desktop executable (update this path to match your installation)
    power_bi_path = r"H:\POWER BI\bin\PBIDesktop.exe"

    if category in dashboards:
        dashboard_path = dashboards[category]
        try:
            # Use subprocess to open Power BI with the specified dashboard
            subprocess.Popen([power_bi_path, dashboard_path])
            print(f"Opening dashboard: {dashboard_path}")
        except Exception as e:
            print(f"Failed to open dashboard for category '{category}'. Error: {e}")
    else:
        print(f"No dashboard configured for category '{category}'.")


# GUI setup using Tkinter
def run_gui():
    # Create the main window
    root = tk.Tk()
    root.title("Differential Privacy Category Selector")

    # Set window size
    root.geometry("800x600")

    # Load the background image using Pillow
    background_image = Image.open("background.jpg")
    background_photo = ImageTk.PhotoImage(background_image)

    # Create a label to display the background image
    background_label = tk.Label(root)
    background_label.place(relwidth=1, relheight=1)

    # Function to dynamically resize the background image
    def update_background_image(event):
        resized_image = background_image.resize((event.width, event.height), Image.Resampling.LANCZOS)
        background_photo_resized = ImageTk.PhotoImage(resized_image)
        background_label.configure(image=background_photo_resized)
        background_label.image = background_photo_resized

    root.bind("<Configure>", update_background_image)

    # Add title above the dropdown menu
    title_label = tk.Label(
        root,
        text="SELECT CATEGORY BELOW",
        font=("Helvetica", 20, "bold"),
        bg="#2C2C2C",  # Adjust the background color to match your design
        fg="white"   # Text color
    )
    title_label.place(relx=0.5, rely=0.2, anchor="center")  # Position above the dropdown

    # Add dropdown menu for category selection
    categories = [
        "Identity and Contact Information",
        "Geographical and Demographic Details",
        "Aadhaar Usage and Linkages",
        "Programs and Healthcare Details"
    ]

    category_combobox = ttk.Combobox(root, values=categories, font=("Helvetica", 18), width=30, justify="center")
    category_combobox.set(categories[0])  # Set default value
    category_combobox.place(relx=0.5, rely=0.4, anchor="center")

    # Function to handle category selection
    def on_category_select():
        selected_category = category_combobox.get()
        create_dp_csv(selected_category, dp_type='laplace', epsilon=1.0)
        open_power_bi_dashboard(selected_category)  # Open the corresponding dashboard

    # Add button to apply differential privacy
    apply_button = tk.Button(root, text="Apply Differential Privacy", font=("Helvetica", 12, "bold"), bg="#4CAF50", fg="white", command=on_category_select)
    apply_button.place(relx=0.5, rely=0.55, anchor="center")

    # Keep references to avoid garbage collection
    root.background_photo = background_photo

    # Run the application
    root.mainloop()

# Run the GUI application
if __name__ == "__main__":
    run_gui()
