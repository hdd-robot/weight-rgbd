import pyrealsense2 as rs
import numpy as np
import cv2
from ultralytics import YOLO
from sklearn.decomposition import PCA
from scipy.spatial import ConvexHull
import joblib

# Chargement des modèles avec joblib
scaler = joblib.load('models/book_scaler.pkl')
model = joblib.load('models/book_modele_svr.pkl')

# Initialisation de la caméra RealSense
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)
config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)
profile = pipeline.start(config)

# Récupération des paramètres intrinsèques
color_intrinsics = profile.get_stream(rs.stream.color).as_video_stream_profile().get_intrinsics()
depth_scale = profile.get_device().first_depth_sensor().get_depth_scale()
print("Depth Scale is: ", depth_scale)

align_to = rs.stream.color
align = rs.align(align_to)

# Chargement du modèle YOLOv8
model_yolo = YOLO('yolov8n.pt')  # Assurez-vous que le fichier du modèle est disponible

def generate_point_cloud(rgb_image, depth_image, intrinsics):
    """Génère un nuage de points à partir des images RGB et Depth."""
    height, width = depth_image.shape
    fx, fy = intrinsics.fx, intrinsics.fy
    cx, cy = intrinsics.ppx, intrinsics.ppy

    points = []

    for y in range(height):
        for x in range(width):
            depth = depth_image[y, x] * depth_scale
            if depth <= 0 or depth > 2.0:  # Filtrage des valeurs de profondeur
                continue
            z = depth
            x3d = (x - cx) * z / fx
            y3d = (y - cy) * z / fy
            points.append((x3d, y3d, z))

    return np.array(points)

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
        'hauteur': dimensions[0], 
        'longueur': dimensions[1], 
        'largeur': dimensions[2],
        'pca_dim1': dimensions[0],
        'pca_dim2': dimensions[1],
        'pca_dim3': dimensions[2],
        'volume': volume,
        'density': density,
        'mean_distance': mean_distance,
        'std_distance': std_distance
    }

try:
    while True:
        # Capture des frames alignées
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()

        if not aligned_depth_frame or not color_frame:
            continue

        # Conversion des frames en matrices NumPy
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())


        annotated_image = color_image.copy()
        # Application de YOLOv8 sur l'image RGB
        results = model_yolo(color_image)

        # Annoter les prédictions sur l'image
        ### annotated_image = results[0].plot()


        # Extraction d'une détection spécifique (exemple : "book")
        for result in results[0].boxes:
            class_id = int(result.cls)
            label = model_yolo.names[class_id]
            if label == "book":
                x_min, y_min, x_max, y_max = map(int, result.xyxy[0].tolist())
                depth_roi = depth_image[y_min:y_max, x_min:x_max]
                rgb_roi = color_image[y_min:y_max, x_min:x_max]

                # Génération du nuage de points pour la région détectée
                point_cloud = generate_point_cloud(rgb_roi, depth_roi, color_intrinsics)

                # Extraction des caractéristiques
                features = extract_point_cloud_features(point_cloud)

                # Normalisation des caractéristiques
                feature_vector = np.array([features[key] for key in sorted(features.keys())]).reshape(1, -1)
                normalized_features = scaler.transform(feature_vector)

                # Prédiction avec le modèle SVR
                prediction = model.predict(normalized_features)
                prediction_text = f"Estimation: {prediction[0]:.2f}"

                # Dessiner la boîte avec la prédiction
                cv2.rectangle(annotated_image, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)
                cv2.putText(
                    annotated_image, prediction_text, (x_min, y_min - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
                )

        # Affichage de l'image annotée
        #cv2.imshow('YOLOv8 + Predictions', color_image )
        cv2.imshow('YOLOv8 + Predictions', annotated_image)

        key = cv2.waitKey(1)
        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()


