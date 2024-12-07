import pandas as pd

# Load the dataset
file_path = '2022-2023.csv'  # Ensure this CSV file is in the same directory as this script
data = pd.read_csv(file_path)

def display_headers():
    print("Available headers:")
    for idx, col in enumerate(data.columns[1:], start=1):
        print(f"{idx}: {col}")

def filter_data():
    while True:
        print("\nEnter the school name(s) (comma-separated) you want to search for, or 'exit' to quit:")
        user_input = input().strip()
        if user_input.lower() == 'exit':
            break
        
        school_names = [name.strip() for name in user_input.split(',')]
        filtered_data = data[data['instnm'].isin(school_names)]
        
        if filtered_data.empty:
            print("No matching schools found.")
        else:
            print("\nSelect a cost header to display:")
            display_headers()
            
            try:
                header_index = int(input("Enter the header index: "))
                selected_header = data.columns[header_index]
                print(f"\nResults for '{selected_header}':")
                print(filtered_data[['instnm', selected_header]])
            except (ValueError, IndexError):
                print("Invalid selection. Please try again.")

if __name__ == "__main__":
    print("Welcome to the School Cost Filter Tool!")
    filter_data()
    print("Goodbye!")
