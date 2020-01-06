#!/usr/bin/env python
# coding: utf-8
import os
import numpy as np
import pandas as pd
from tqdm import tqdm
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def unit_vector(vector):
    return vector / np.linalg.norm(vector)


def get_angle(vec1, vec2):
    unit_vec1 = unit_vector(vec1)
    unit_vec2 = unit_vector(vec2)
    return np.arccos(np.clip(np.dot(unit_vec1, unit_vec2), -1.0, 1.0))


class ETL:

    def __init__(self, data_path):
        self.DATA_PATH = data_path
        self.cima = {}
        self.angles = {
            "V1": ["upper_chest", "nose", "right_wrist"],
            "V2": ["upper_chest", "nose", "left_wrist"],
            "V3": ["upper_chest", "hip_center", "right_wrist"],
            "V4": ["upper_chest", "hip_center", "left_wrist"],
            "V5": ["hip_center", "upper_chest", "right_ankle"],
            "V6": ["hip_center", "upper_chest", "left_ankle"],
        }

    def get_cima(self):
        return self.cima

    def load_metadata(self, dataset):
        meta_path = os.path.join(self.DATA_PATH, dataset, "metadata.csv")
        self.metadata = pd.read_csv(meta_path)


    def load(self, dataset, tiny=False):
        cima_files = []
        missing_metadata = []
        cima_path = os.path.join(self.DATA_PATH, dataset)

        self.load_metadata(dataset)

        cima_path = os.path.join(cima_path, "data") if os.path.exists(os.path.join(cima_path, "data")) else cima_path

        for root, dirs, files in os.walk(cima_path):
            for filename in files:
                if filename[-4:] == ".csv":
                    cima_files.append(os.path.join(root, filename))

        if tiny:
            cima_files = cima_files[:5]

        print("\n\n----------------")
        print(" Loading CIMA ")
        print("----------------\n")

        for file in tqdm(cima_files):
            file_name = file.split(os.sep)[-1].split(".")[0]
            file_id = file_name[:3] if file_name[0].isnumeric() else file_name[:7]
            meta_row = self.metadata.loc[self.metadata["ID"] == file_id]
            if meta_row.empty:
                missing_metadata.append(file_id)
                continue
            data = pd.read_csv(file)
            data = data.drop(columns=["Unnamed: 0"], errors="ignore")
            self.cima[file_id] = {"data": data, "label": meta_row.iloc[0]["CP"], "fps": meta_row.iloc[0]["FPS"]}

    def create_angles(self):
        cima_angles = {}
        print("\n\n----------------")
        print(" Creating angles ")
        print("----------------\n")
        for key, item in tqdm(self.cima.items()):
            data = item["data"]
            angles = {key: [] for key in self.angles.keys()}
            for row in data.iterrows():
                row_data = row[1]
                for angle_key, points in self.angles.items():
                    p0 = [row_data[points[0] + "_x"], row_data[points[0] + "_y"]]
                    p1 = [row_data[points[1] + "_x"], row_data[points[1] + "_y"]]
                    p2 = [row_data[points[2] + "_x"], row_data[points[2] + "_y"]]
                    vec1 = np.array(p0) - np.array(p1)
                    vec2 = np.array(p2) - np.array(p1)
                    angle = np.abs(np.math.atan2(np.linalg.det([vec1,vec2]),np.dot(vec1,vec2)))
                    angles[angle_key].append(angle)
            for new_key, angles_list in angles.items():
                data[new_key] = pd.Series(angles_list)
            self.cima[key]["data"] = data

    def save(self, name="CIMA_Transformed"):
        save_path = os.path.join(self.DATA_PATH, name)
        if not os.path.exists(save_path):
            os.makedirs(save_path)
        metadata_path = os.path.join(save_path, "metadata.csv")
        self.metadata.to_csv(metadata_path)
        save_data_path = os.path.join(save_path, "data")
        if not os.path.exists(save_data_path):
            os.makedirs(save_data_path)
        for key, data in self.cima.items():
            path = os.path.join(save_data_path, key + ".csv")
            data["data"].to_csv(path)


if __name__ == "__main__":
    etl = ETL("/home/login/Dataset/")
    etl.load("CIMA")
    etl.create_angles()
    #etl.save(name="CIMA_angles")
