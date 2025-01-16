import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
from scipy.spatial import ConvexHull
from sklearn.decomposition import PCA
import joblib  # Pour la sauvegarde du modèle et du scaler
import  json
import open3d as o3d
import os

# Fonction pour extraire des caractéristiques des nuages de points
def extract_point_cloud_features(point_cloud):
    """
    Extrait des caractéristiques d'un nuage de points 3D.
    :param point_cloud: ndarray (N, 3), où N est le nombre de points.
    :return: Dictionnaire avec les caractéristiques.
    """
    # Dimensions principales via PCA
    pca = PCA(n_components=3)
    pca.fit(point_cloud)
    dimensions = np.sqrt(pca.explained_variance_)

    # Enveloppe convexe pour le volume
    try:
        hull = ConvexHull(point_cloud)
        volume = hull.volume
    except:
        volume = 0  # Cas particulier : pas assez de points pour former un volume

    # Centre de gravité et densité
    centroid = np.mean(point_cloud, axis=0)
    distances = np.linalg.norm(point_cloud - centroid, axis=1)
    density = len(point_cloud) / volume if volume > 0 else 0

    # Moments statistiques des distances
    mean_distance = np.mean(distances)
    std_distance = np.std(distances)

    return {
        'pca_dim1': dimensions[0],
        'pca_dim2': dimensions[1],
        'pca_dim3': dimensions[2],
        'volume': volume,
        'density': density,
        'mean_distance': mean_distance,
        'std_distance': std_distance
    }

# Exemple de préparation des données
# df contient des colonnes: ['hauteur', 'longueur', 'largeur', 'poids', 'nuage_de_points']
with open('dataset_export/metadata.json') as f:
        data = json.load(f)

df = pd.DataFrame(data)
print("Aperçu des métadonnées :")
print(df.head())

# Supprimer les 20 premières lignes
df = df.iloc[22:]

features = []
poids = []
for key, row in df.iterrows():
    rgb_file_name = row["img_rgb_name"]
    pcd_file_name = rgb_file_name[4:-4]
    pcd_file_name = "dataset_export/img_decoupe/"+"pcd_" + pcd_file_name + ".pcd"
    if not os.path.exists(pcd_file_name):
        print(f"Fichier manquant : {pcd_file_name}")
        continue
    #get 3D pointcloud en format ndarray (N, 3) from binary pcd file 
    point_cloud = o3d.io.read_point_cloud(pcd_file_name)
    point_cloud_np = np.asarray(point_cloud.points)
    cloud_features = extract_point_cloud_features(point_cloud_np)

    combined_features = {
        'hauteur': row['obj_size_height_z'],
        'longueur': row['obj_size_length_x'],
        'largeur': row['obj_size_width_y'],
        **cloud_features
    }
    features.append(combined_features)
    poids.append(row['obj_weight'])
# Conversion en DataFrame
features_df = pd.DataFrame(features)
X = features_df
y = poids

# Normalisation des données
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Division en ensembles d'entraînement et de test
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Entraînement du modèle SVM
svr = SVR(kernel='linear')  # Vous pouvez essayer d'autres kernels
svr.fit(X_train, y_train)

# Sauvegarde du modèle et du scaler
joblib.dump(svr, "models/book_modele_svr.pkl")
joblib.dump(scaler, "models/book_scaler.pkl")
print("Modèle et scaler sauvegardés avec succès.")

# Prédictions et évaluation
y_pred = svr.predict(X_test)
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
print(f"MAE: {mae}")
print(f"MSE: {mse}")

# Test sur de nouvelles données
nouveau_nuage = np.random.rand(100, 3)  # Exemple de nouveau nuage de points
nouveau_features = extract_point_cloud_features(nouveau_nuage)

nouveau_livre = pd.DataFrame([{
    'hauteur': 15.0, 
    'longueur': 20.0, 
    'largeur': 5.0,
    'pca_dim1': nouveau_features['pca_dim1'],
    'pca_dim2': nouveau_features['pca_dim2'],
    'pca_dim3': nouveau_features['pca_dim3'],
    'volume': nouveau_features['volume'],
    'density': nouveau_features['density'],
    'mean_distance': nouveau_features['mean_distance'],
    'std_distance': nouveau_features['std_distance']
}])
nouveau_livre_scaled = scaler.transform(nouveau_livre)
# Prédire le poids
poids_prevu = svr.predict(nouveau_livre_scaled)
print(f"Poids prévu pour le nouveau livre: {poids_prevu[0]:.2f} kg")

# Charger le modèle et le scaler pour vérifier leur fonctionnement
svr_loaded = joblib.load("models/book_modele_svr.pkl")
scaler_loaded = joblib.load("models/book_scaler.pkl")
print("Modèle et scaler chargés avec succès.")

