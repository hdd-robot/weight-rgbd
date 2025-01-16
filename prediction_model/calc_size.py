import traceback
import sys
import os
import json
from datetime import datetime
import pandas as pd
import open3d  as o3d
import re
import cv2
import numpy as np


def calc_size():
    # Chargement des métadonnées
    with open('dataset_export/metadata.json') as f:
        data = json.load(f)

    df = pd.DataFrame(data)
    print("Aperçu des métadonnées :")
    print(df.head())

    # Supprimer les 20 premières lignes
    df = df.iloc[22:]

    for index, row in df.iterrows():
        # Récupération des noms de fichiers
        rgb_file_name = row["img_rgb_name"]
        pcd_file_name = rgb_file_name[4:-4]
        pcd_file_name = "pcd_" + pcd_file_name + ".pcd"
        print("rgb_file_name : ", rgb_file_name)

        path_croped_pcd = "dataset_export/img_decoupe/" + pcd_file_name

        if not os.path.exists(path_croped_pcd):
            print(f"Fichier manquant : {path_croped_pcd}")
            continue

        pcd = o3d.io.read_point_cloud(path_croped_pcd)

        min_z = np.min(np.asarray(pcd.points)[:, 2])
        pcd.translate((0, 0, -min_z))

        pcd = pcd.voxel_down_sample(voxel_size=0.0001)


        ##### Sup sol

        plane_model, inliers = pcd.segment_plane(distance_threshold=0.5,  # Tolérance (m)
                                         ransac_n=5,               # Nombre de points pour RANSAC
                                         num_iterations=100)      # Nombre d'itérations

        # Séparer les points du sol et les autres
        inlier_cloud = pcd.select_by_index(inliers)  # Points du plan (sol)
        outlier_cloud = pcd.select_by_index(inliers, invert=False)  # Points hors du plan (objet)

        
        #exit()
        points = np.asarray(pcd.points)

        # Trouver les limites du nuage de points
        x_min, y_min, z_min = points.min(axis=0)
        x_max, y_max, z_max = points.max(axis=0)

        # Calculer les dimensions
        length = x_max - x_min  # Longueur
        width = y_max - y_min   # Largeur
        height = z_max - z_min  # Hauteur

        
        print(f"Longueur: {length:.2f} m, Largeur: {width:.2f} m, Hauteur: {height:.2f} m")

        # Créer une boîte englobante
        bbox = pcd.get_axis_aligned_bounding_box()
        # Colorer la boîte
        bbox.color = (1, 0, 0)  # Rouge
        # Afficher le nuage de points et la boîte
        o3d.visualization.draw_geometries([pcd, bbox])


        obb = pcd.get_oriented_bounding_box()
        obb.color = (0, 1, 0)  # Vert
        o3d.visualization.draw_geometries([pcd, obb])




        #### RANSAC

        pcd_cleaned = pcd.remove_statistical_outlier(nb_neighbors=20, std_ratio=2.0)[0]

        # Appliquer DBSCAN
        labels = np.array(pcd_cleaned.cluster_dbscan(eps=0.05, min_points=5, print_progress=True))

        # Vérifier si des clusters sont détectés
        if len(labels) == 0 or (labels >= 0).sum() == 0:
            print("No clusters detected.")
        else:
            # Trouver le plus grand cluster
            valid_labels = labels[labels >= 0]
            largest_cluster_idx = np.argmax(np.bincount(valid_labels))

            # Isoler le plus grand cluster
            cluster_points = np.asarray(pcd_cleaned.points)[labels == largest_cluster_idx]
            cluster_pcd = o3d.geometry.PointCloud()
            cluster_pcd.points = o3d.utility.Vector3dVector(cluster_points)

            # Afficher
            o3d.visualization.draw_geometries([cluster_pcd])

        

if __name__ == "__main__":
    try:
        calc_size()
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)

