def calculate_a1c(average_glucose: float) -> float:
    # Formula for estimated A1C:
    # A1C = (average_glucose + 46.7) / 28.7
    return (average_glucose + 46.7) / 28.7

def main():
    print("A1C Calculator")
    try:
        avg_glucose = float(input("Enter your average blood glucose (mg/dL): "))
        estimated_a1c = calculate_a1c(avg_glucose)
        print(f"\nYour estimated A1C is approximately {estimated_a1c:.2f}%")
    except ValueError:
        print("Invalid input. Please enter a numeric value.")

if __name__ == "__main__":
    main()
