import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import euclidean, pdist, squareform
from scipy.stats import gaussian_kde
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Seed for reproducibility
np.random.seed(42)

# Generate synthetic datasets
def generate_datasets(n_samples=1000, n_features=30):
    """Generates synthetic datasets with different structures."""

    # High Viscosity (Structured): Two distinct clusters
    high_viscosity = np.vstack([
        np.random.normal(loc=0, scale=1, size=(n_samples // 2, n_features)),
        np.random.normal(loc=5, scale=1, size=(n_samples // 2, n_features))
    ])

    # Medium Viscosity (Embeddings): Random embeddings
    medium_viscosity = np.random.normal(loc=0, scale=1, size=(n_samples, n_features))

    # Low Viscosity (Noise): Uniformly distributed noise
    low_viscosity = np.random.uniform(low=-1, high=1, size=(n_samples, n_features))

    return {
        "High Viscosity (Structured)": high_viscosity,
        "Medium Viscosity (Embeddings)": medium_viscosity,
        "Low Viscosity (Noise)": low_viscosity
    }

# Compute entropy using Kernel Density Estimation (KDE)
def compute_entropy_kde(data):
    """Computes entropy using Kernel Density Estimation (KDE)."""
    kde = gaussian_kde(data.T)
    sample_points = kde.resample(size=1000)
    density_values = kde(sample_points)
    return -np.mean(np.log(density_values + 1e-9))

# Compute curvature using PCA explained variance
def compute_curvature(data, n_components=10):
    """Computes curvature using PCA explained variance."""
    pca = PCA(n_components=min(data.shape[1], n_components))
    pca.fit(data)
    return np.sum(pca.explained_variance_ratio_[:n_components])

# Compute deformation (using all pairwise distances)
def compute_deformation(original, compressed):
    """Computes deformation using all pairwise distances."""
    return np.mean(np.abs(pdist(original) - pdist(compressed)))

# Compute viscosity score
def compute_viscosity(initial_entropy, compressed_entropy, initial_curvature, deformation):
    """Computes the viscosity score."""
    return (initial_entropy - compressed_entropy) / (initial_entropy * (1 + deformation) * (1 + 0.1 * (2 - initial_curvature)))

# Run GEMINI analysis
def run_gemini_analysis(datasets, n_trials=5, perplexity_values=[5, 10, 30, 50, 100], pca_components=10):
    """Runs the GEMINI analysis with various experiments."""

    all_results = []

    for trial in range(n_trials):
        logging.info(f"Starting trial {trial + 1}/{n_trials}")
        np.random.seed(trial)

        for dataset_name, data in datasets.items():
            logging.info(f"Analyzing dataset: {dataset_name}")
            scaler = StandardScaler()
            data_scaled = scaler.fit_transform(data)

            # --- Shear Rate Dependence ---
            for perplexity in perplexity_values:
                tsne = TSNE(n_components=2, perplexity=perplexity, random_state=trial)
                compressed_data = tsne.fit_transform(data_scaled)

                initial_entropy = compute_entropy_kde(data_scaled)
                compressed_entropy = compute_entropy_kde(compressed_data)
                initial_curvature = compute_curvature(data_scaled, n_components=2)
                deformation = compute_deformation(data_scaled, compressed_data)
                viscosity = compute_viscosity(initial_entropy, compressed_entropy, initial_curvature, deformation)

                all_results.append({
                    "Trial": trial,
                    "Dataset": dataset_name,
                    "Experiment": "Shear Rate Dependence",
                    "Perplexity": perplexity,
                    "Viscosity Score": viscosity
                })

            # --- Hysteresis ---
            for i, perplexity in enumerate(perplexity_values + perplexity_values[::-1]):  # Forward & backward pass
                tsne = TSNE(n_components=2, perplexity=perplexity, random_state=trial)
                compressed_data = tsne.fit_transform(data_scaled)

                initial_entropy = compute_entropy_kde(data_scaled)
                compressed_entropy = compute_entropy_kde(compressed_data)
                initial_curvature = compute_curvature(data_scaled, n_components=2)
                deformation = compute_deformation(data_scaled, compressed_data)
                viscosity = compute_viscosity(initial_entropy, compressed_entropy, initial_curvature, deformation)

                all_results.append({
                    "Trial": trial,
                    "Dataset": dataset_name,
                    "Experiment": "Hysteresis",
                    "Step": i + 1,
                    "Perplexity": perplexity,
                    "Viscosity Score": viscosity
                })

            # --- Viscoelasticity ---
            pca = PCA(n_components=pca_components)
            compressed_data = pca.fit_transform(data_scaled)
            reconstructed_data = pca.inverse_transform(compressed_data)
            recovery = compute_deformation(data_scaled, reconstructed_data)

            all_results.append({
                "Trial": trial,
                "Dataset": dataset_name,
                "Experiment": "Viscoelasticity",
                "PCA Components": pca_components,
                "Recovery": recovery
            })

    return pd.DataFrame(all_results)

# --- Main Execution ---
if __name__ == "__main__":
    datasets = generate_datasets()
    results_df = run_gemini_analysis(datasets)

    # Print the raw results
    print(results_df)

    # Group and analyze results
    analysis = results_df.groupby(["Experiment", "Dataset"])["Viscosity Score"].agg(["mean", "std"])

    # Plot the results
    plt.figure(figsize=(12, 6))
    for experiment in results_df["Experiment"].unique():
        exp_data = results_df[results_df["Experiment"] == experiment]
        plt.scatter(exp_data["Perplexity"], exp_data["Viscosity Score"], label=experiment, alpha=0.7)

    plt.xlabel("Perplexity / PCA Components")
    plt.ylabel("Viscosity Score")
    plt.title("GEMINI Analysis: Viscosity vs. Shear, Hysteresis, and Viscoelasticity")
    plt.legend()
    plt.grid(True)
    plt.show()
