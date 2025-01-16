
import numpy as np
import traceback
import sys

import os
import json
from datetime import datetime
import pandas as pd
import open3d  as o3d
import re

from ultralytics import YOLO
import cv2


model = YOLO('yolov8n.pt')  # Vous pouvez utiliser 'yolov8s.pt', 'yolov8m.pt', etc.


def parse_intrinsec_string(intrinsec_str):
    """
    Analyser une chaîne intrinsèque et extraire les paramètres de la caméra.
    """
    try:
        # Extraire les dimensions (width x height)
        dimensions = re.search(r'(\d+)x(\d+)', intrinsec_str)
        if not dimensions:
            raise ValueError(f"Dimensions introuvables dans : {intrinsec_str}")
        width = int(dimensions.group(1))
        height = int(dimensions.group(2))

        # Extraire les coordonnées du point principal (cx, cy)
        principal_point = re.search(r'p\[(\d+\.?\d*)\s+(\d+\.?\d*)\]', intrinsec_str)
        if not principal_point:
            raise ValueError(f"Point principal introuvable dans : {intrinsec_str}")
        cx = float(principal_point.group(1))
        cy = float(principal_point.group(2))

        # Extraire les longueurs focales (fx, fy)
        focal_lengths = re.search(r'f\[(\d+\.?\d*)\s+(\d+\.?\d*)\]', intrinsec_str)
        if not focal_lengths:
            raise ValueError(f"Longueurs focales introuvables dans : {intrinsec_str}")
        fx = float(focal_lengths.group(1))
        fy = float(focal_lengths.group(2))

        return {
            "width": width,
            "height": height,
            "fx": fx,
            "fy": fy,
            "cx": cx,
            "cy": cy
        }
    except Exception as e:
        print(f"Erreur lors de l'analyse de la chaîne intrinsèque : {e}")
        raise


def create_pcd_from_gray_and_rgbd():
    try:
        # Chargement des métadonnées
        with open('dataset_export/metadata.json') as f:
            data = json.load(f)

        df = pd.DataFrame(data)
        print("Aperçu des métadonnées :")
        print(df.head())

        # Supprimer les 20 premières lignes
        df = df.iloc[22:]

        for index, row in df.iterrows():
            try:
                # Récupération des noms de fichiers
                rgb_file_name = row["img_rgb_name"]
                img_depth_name = row["img_depth_name"]
                pcd_file_name = rgb_file_name[4:-4]
                pcd_file_name = "pcd_" + pcd_file_name

                intrinsec_params_str = row["img_depth_intrinsec"]

                # Génération des chemins complets
                rgb_path = f"dataset_export/images_rgb/{rgb_file_name}"
                gry_path = f"dataset_export/images_gray/{img_depth_name}"

                pcd_path = f"dataset_export/img_decoupe/{pcd_file_name}.pcd"
                ply_path = f"dataset_export/img_decoupe/{pcd_file_name}.ply"

                # Vérification des fichiers
                if not os.path.exists(rgb_path):
                    print(f"Fichier RGB manquant : {rgb_path}")
                    continue
                if not os.path.exists(gry_path):
                    print(f"Fichier de profondeur manquant : {gry_path}")
                    continue

                ## detect
                results = model.predict(str(rgb_path), save=True, save_txt=True)
                detection_info = []
                for result in results:
                    for box in result.boxes:
                        detection_info.append({
                            "xmin": float(box.xyxy[0][0]),  # Coordonnée x minimale
                            "ymin": float(box.xyxy[0][1]),  # Coordonnée y minimale
                            "xmax": float(box.xyxy[0][2]),  # Coordonnée x maximale
                            "ymax": float(box.xyxy[0][3]),  # Coordonnée y maximale
                            "confidence": float(box.conf[0]),  # Confiance de la détection
                            "class": int(box.cls[0]),  # Classe prédite
                            "class_name" : model.names[int(box.cls[0])] # Nom de la classe prédite
                        })

                for detection in detection_info:
                    x_min, y_min, x_max, y_max = int(detection["xmin"]), int(detection["ymin"]), int(detection["xmax"]), int(detection["ymax"])
                    width_img = x_max - x_min
                    height_img = y_max - y_min

                    confidence = detection["confidence"]
                    class_id = detection["class"]
                    class_name = detection["class_name"]

                    if class_name != "book":
                        continue;

                    rgb_image = cv2.imread(str(rgb_path), cv2.COLOR_BGR2RGB)  
                    depth_image = cv2.imread(str(gry_path), cv2.IMREAD_UNCHANGED)

                    roi_rgb = rgb_image[y_min:y_max, x_min:x_max]
                    roi_depth = depth_image[y_min:y_max, x_min:x_max]

                    intrinsic_params = parse_intrinsec_string(intrinsec_params_str)
                    fx=intrinsic_params["fx"]
                    fy=intrinsic_params["fy"]
                    cx=intrinsic_params["cx"]
                    cy=intrinsic_params["cy"]

                    points = []
                    colors = []
                    for v in range(int(height_img)):
                        for u in range(int(width_img)):
                            z = roi_depth[v, u] / 1000.0  # Profondeur en millimètres
                            if z > 0:  # Ignorer les pixels sans profondeur valide
                                x = (u - cx) * z / fx
                                y = (v - cy) * z / fy
                                points.append((x, y, z))  # Ajouter couleur
                                colors.append(roi_rgb[v, u])  # Ajouter couleur



                    # Sauvegarder au format PCD
                    point_cloud = o3d.geometry.PointCloud()
                    point_cloud.points = o3d.utility.Vector3dVector(points)
                    point_cloud.colors = o3d.utility.Vector3dVector(colors)


                    # point_cloud.transform([[1, 0, 0, 0],
                    #                        [0, -1, 0, 0],
                    #                        [0, 0, -1, 0],
                    #                        [0, 0, 0, 1]])

                    # Définir les angles en degrés
                    angle_x = -45  # Rotation autour de l'axe X en degrés
                    angle_y = -45  # Rotation autour de l'axe Y en degrés
                    angle_z = 180  # Rotation autour de l'axe Z en degrés

                    # Convertir les angles en radians
                    theta_x = np.radians(angle_x)
                    theta_y = np.radians(angle_y)
                    theta_z = np.radians(angle_z)

                    # Matrice de rotation autour de X
                    rotation_x = np.array([
                        [1, 0, 0, 0],
                        [0, np.cos(theta_x), -np.sin(theta_x), 0],
                        [0, np.sin(theta_x),  np.cos(theta_x), 0],
                        [0, 0, 0, 1]
                    ])

                    # Matrice de rotation autour de Y
                    rotation_y = np.array([
                        [np.cos(theta_y), 0, np.sin(theta_y), 0],
                        [0, 1, 0, 0],
                        [-np.sin(theta_y), 0, np.cos(theta_y), 0],
                        [0, 0, 0, 1]
                    ])

                    # Matrice de rotation autour de Z
                    rotation_z = np.array([
                        [np.cos(theta_z), -np.sin(theta_z), 0, 0],
                        [np.sin(theta_z),  np.cos(theta_z), 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]
                    ])

                    # Combiner les rotations : X, puis Y, puis Z
                    combined_rotation = np.dot(rotation_z, np.dot(rotation_y, rotation_x))

                    # Appliquer la transformation au nuage de points
                    point_cloud.transform(combined_rotation)


                    # point_cloud.transform([[-1, 0, 0, 0],
                    #                        [0, -0.5, 0, 0],
                    #                        [0, 0, 1, 0],
                    #                        [0, 0, 0, 1]])

                    o3d.io.write_point_cloud(pcd_path, point_cloud)

                    #exit()
            except Exception as e:
                traceback.print_exc()
                exit()
                print(f"Erreur lors du traitement de la ligne {index} : {e}")
    except Exception as e:
        print(f"Erreur lors du chargement des métadonnées ou du traitement : {e}")
                

if __name__ == '__main__':
    create_pcd_from_gray_and_rgbd()
