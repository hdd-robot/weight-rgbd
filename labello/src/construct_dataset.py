from db_manager import db_manager  # Gestionnaire de base de données
import os
import json
from datetime import datetime
import pandas as pd
import open3d  as o3d
import re

import json
import os
import pandas as pd
from datetime import datetime

def create_metadat_file():
    # Fonction pour sérialiser les objets datetime
    class CustomJSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, datetime):
                return obj.isoformat()  # Convertir datetime en chaîne ISO 8601
            return super().default(obj)

    # Création du répertoire d'exportation s'il n'existe pas
    os.makedirs('dataset_export', exist_ok=True)
    print(" --- Create_dataset ---")
    try:
        # Instanciation du gestionnaire de base de données
        db_manager_instance = db_manager()  # Supposant que db_manager est défini ailleurs
        # Récupération des données en JSON
        data = db_manager_instance.get_all_data()
        
        # Vérification si les données sont vides
        if not data:  # Vérifie si l'objet `data` est vide ({} ou [])
            print("Aucune donnée trouvée à exporter.")
        else:
            # Conversion des données en DataFrame
            df = pd.DataFrame(data)

            # Vérification et suppression de la colonne "img_specto_data"
            if "img_specto_data" in df.columns:
                df = df.drop(columns=["img_specto_data", "img_specto_position", "img_specto_spectr_rgb", "img_specto_graph_rgb"])
                print("Colonne 'img_specto_data' supprimée.")

            # Conversion du DataFrame en dictionnaire
            data_dict = df.to_dict(orient='records')

            # Sérialisation en JSON avec l'encodeur personnalisé
            json_data = json.dumps(data_dict, indent=4, cls=CustomJSONEncoder)

            # Chemin du fichier de sortie
            output_path = 'dataset_export/metadata.json'
            # Écriture dans un fichier JSON
            with open(output_path, 'w') as f:
                f.write(json_data)
                print(f"Dataset exporté avec succès dans : {output_path}")
    except Exception as e:
        # Gestion des erreurs
        print(f"Erreur lors de l'exportation du dataset : {e}")





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
        #df = df.iloc[12:]

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
                pcd_path = f"dataset_export/images_pcd/{pcd_file_name}.pcd"
                ply_path = f"dataset_export/images_ply/{pcd_file_name}.ply"

                # Vérification des fichiers
                if not os.path.exists(rgb_path):
                    print(f"Fichier RGB manquant : {rgb_path}")
                    continue
                if not os.path.exists(gry_path):
                    print(f"Fichier de profondeur manquant : {gry_path}")
                    continue

                # Chargement des images
                print(f"Traitement de : {rgb_path} et {gry_path}")
                color_raw = o3d.io.read_image(rgb_path)
                depth_raw = o3d.io.read_image(gry_path)

                intrinsic_params = parse_intrinsec_string(intrinsec_params_str)

                # Création de l'objet PinholeCameraIntrinsic
                intrinsic = o3d.camera.PinholeCameraIntrinsic(
                    width=intrinsic_params["width"],
                    height=intrinsic_params["height"],
                    fx=intrinsic_params["fx"],
                    fy=intrinsic_params["fy"],
                    cx=intrinsic_params["cx"],
                    cy=intrinsic_params["cy"]
                )

                # Création de l'image RGBD
                rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                    color_raw, depth_raw, convert_rgb_to_intensity=False
                )

                # Création du nuage de points
                pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
                    rgbd_image, intrinsic
                )

                # Transformation (si nécessaire)
                pcd.transform([[1, 0, 0, 0], 
                               [0, -1, 0, 0], 
                               [0, 0, -1, 0], 
                               [0, 0, 0, 1]])

                # Sauvegarde des nuages de points
                o3d.io.write_point_cloud(pcd_path, pcd)
                o3d.io.write_point_cloud(ply_path, pcd)

            except Exception as e:
                print(f"Erreur lors du traitement de la ligne {index} : {e}")
    except Exception as e:
        print(f"Erreur lors du chargement des métadonnées ou du traitement : {e}")


if __name__ == '__main__':
    create_metadat_file()
    create_pcd_from_gray_and_rgbd()
