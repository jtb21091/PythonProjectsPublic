import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import norm

def calculate_dpmo(defects, opportunities):
    """
    Calculate Defects Per Million Opportunities (DPMO).

    :param defects: Total number of defects.
    :param opportunities: Total number of opportunities.
    :return: DPMO value.
    """
    return (defects / opportunities) * 1_000_000

def calculate_yield(units, defects):
    """
    Calculate process yield.

    :param units: Total number of units.
    :param defects: Total number of defects.
    :return: Yield as a percentage.
    """
    return ((units - defects) / units) * 100

def calculate_sigma_level(dpmo):
    """
    Estimate Sigma Level based on DPMO.

    :param dpmo: Defects Per Million Opportunities.
    :return: Approximate Sigma Level.
    """
    # Approximation of Sigma Level from DPMO
    if dpmo == 0:
        return 6.0  # Perfect process

    import scipy.stats as stats
    z_score = stats.norm.ppf(1 - dpmo / 1_000_000)
    return round(z_score, 2)

def calculate_copq(defects, defect_cost):
    """
    Calculate Cost of Poor Quality (COPQ).

    :param defects: Total number of defects.
    :param defect_cost: Average cost per defect.
    :return: COPQ value in monetary terms.
    """
    return defects * defect_cost

def plot_bell_curve_with_z(z_score):
    """
    Plot a bell curve with the Z-score highlighted.

    :param z_score: Z-score to highlight.
    """
    x = np.linspace(-4, 4, 1000)
    y = norm.pdf(x)

    plt.figure(figsize=(10, 6))
    plt.plot(x, y, label="Normal Distribution", color="blue")
    plt.fill_between(x, 0, y, where=(x <= z_score), color="orange", alpha=0.5, label=f"Area below Z={z_score}")

    plt.title("Bell Curve with Highlighted Z-score")
    plt.xlabel("Z-score")
    plt.ylabel("Probability Density")
    plt.axvline(x=z_score, color="red", linestyle="--", label=f"Z={z_score}")
    plt.legend()
    plt.grid()
    plt.show()

# Example usage
if __name__ == "__main__":
    # Input data
    total_units = 10000  # Total units produced
    defects = 150        # Total number of defects
    opportunities_per_unit = 5
    defect_cost = 50        # Average cost per defect in dollars

    # Calculations
    total_opportunities = total_units * opportunities_per_unit
    dpmo = calculate_dpmo(defects, total_opportunities)
    yield_percentage = calculate_yield(total_units, defects)
    sigma_level = calculate_sigma_level(dpmo)
    copq = calculate_copq(defects, defect_cost)

    # Display results
    print("Lean Six Sigma Metrics:")
    print(f"DPMO: {dpmo:.2f}")
    print(f"Yield: {yield_percentage:.2f}%")
    print(f"Sigma Level: {sigma_level}")
    print(f"COPQ: ${copq:.2f}")

    # Plot the bell curve with Z-score
    plot_bell_curve_with_z(sigma_level)
