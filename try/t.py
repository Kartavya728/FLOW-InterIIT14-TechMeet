import os

# Define the folder and file structure
structure = {
    "stock-anomaly-mcp": {
        "data": ["historical_prices.csv"],
        "": ["server.py", "stock_streamer.py", "anomaly_detector.py", "client.py", "requirements.txt"]
    }
}

# Function to create folders and files
def create_structure(base_path, structure):
    for folder, content in structure.items():
        folder_path = os.path.join(base_path, folder)
        os.makedirs(folder_path, exist_ok=True)
        for subfolder, files in content.items():
            subfolder_path = os.path.join(folder_path, subfolder)
            if subfolder:
                os.makedirs(subfolder_path, exist_ok=True)
            for file in files:
                file_path = os.path.join(subfolder_path, file)
                open(file_path, "a").close()  # Create empty file
                print(f"Created: {file_path}")

# Run the function
if __name__ == "__main__":
    create_structure(".", structure)
    print("\n✅ Project structure created successfully.")
