from typing import Any
import shutil
import os
import glob
import pandas as pd
from utils.paths import path_file_running
import pickle
from utils.s3_communication import S3Communication
from pathlib import Path
from utils.paths import ProjectPaths
from utils.settings import MainSettings, S3Settings


class Merger():
    def __init__(self,
                 main_settings: MainSettings,
                 s3_settings: S3Settings,
                 project_paths: ProjectPaths) -> None:
        
        self.main_settings: MainSettings = main_settings
        self.s3_settings: S3Settings = s3_settings
        self.project_paths: ProjectPaths = project_paths
        self.s3_communication_main: S3Communication | None = None
        self.s3_communication_interim: S3Communication | None = None

    def _setup_s3_usage(self) -> None:
        if self.main_settings.general.s3_usage:
            self.s3_communication_main = self._return_s3_communication_main()
            self.s3_communication_interim = self._return_s3_communication_interim()

    def _return_s3_communication_main(self) -> S3Communication:
        return S3Communication(
            s3_endpoint_url=os.getenv(self.s3_settings.main_bucket.s3_endpoint),
            aws_access_key_id=os.getenv(self.s3_settings.main_bucket.s3_access_key),
            aws_secret_access_key=os.getenv(self.s3_settings.main_bucket.s3_secret_key),
            s3_bucket=os.getenv(self.s3_settings.main_bucket.s3_bucket_name),
        )
    
    def _return_s3_communication_interim(self) -> S3Communication:
        return S3Communication(
            s3_endpoint_url=os.getenv(self.s3_settings.interim_bucket.s3_endpoint),
            aws_access_key_id=os.getenv(self.s3_settings.interim_bucket.s3_access_key),
            aws_secret_access_key=os.getenv(self.s3_settings.interim_bucket.s3_secret_key),
            s3_bucket=os.getenv(self.s3_settings.interim_bucket.s3_bucket_name),
        )
    
    def _download_inference_related_files_from_s3(self) -> None:
        path_file_related_s3: Path = Path(self.s3_settings.prefix) / self.project_paths.string_project_name / 'data' / 'output' / 'RELEVANCE' / 'Text'
        self.s3_communication_main.download_files_in_prefix_to_dir(str(path_file_related_s3), 
                                                                   str(self.project_paths.path_folder_relevance))
        


def generate_text_3434(project_name: str,
                       s3_usage: bool,
                       s3_settings: S3Settings, 
                       project_paths: ProjectPaths):
    """
    This function merges all infer relevance outputs into one large file, which is then 
    used to train the kpi extraction model.
    
    :param project_name: str, representing the project we currently work on
    :param s3_usage: boolean, if we use s3 as we then have to upload the new csv file to s3
    :param s3_settings: dictionary, containing information in case of s3 usage
    return None
    """
    if s3_usage:
        s3c_main = S3Communication(
            s3_endpoint_url=os.getenv(s3_settings.main_bucket.s3_endpoint),
            aws_access_key_id=os.getenv(s3_settings.main_bucket.s3_access_key),
            aws_secret_access_key=os.getenv(s3_settings.main_bucket.s3_secret_key),
            s3_bucket=os.getenv(s3_settings.main_bucket.s3_bucket_name),
        )
        # Download infer relevance files
        prefix_rel_infer = str(Path(s3_settings.prefix) / project_name / 'data' / 'output' / 'RELEVANCE' / 'Text')
        s3c_main.download_files_in_prefix_to_dir(prefix_rel_infer, str(project_paths.path_folder_relevance))
        
    with open(str(project_paths.path_folder_text_3434) + r"/text_3434.csv", "w") as file_out:
        very_first = True
        rel_inf_list = list(glob.iglob(str(project_paths.path_folder_relevance) + r'/*.csv'))
        if len(rel_inf_list) == 0:
            print("No relevance inference results found.")
            return False
        else:
            try:
                for filepath in rel_inf_list: 
                    print(filepath)
                    with open(filepath) as file_in:
                        first = True
                        for l in file_in:
                            if(very_first or not first):
                                file_out.write(l)
                            first = False
                        very_first = False
            except Exception:
                return False
    
    if s3_usage:
        s3c_interim = S3Communication(
            s3_endpoint_url=os.getenv(s3_settings.interim_bucket.s3_endpoint),
            aws_access_key_id=os.getenv(s3_settings.interim_bucket.s3_access_key),
            aws_secret_access_key=os.getenv(s3_settings.interim_bucket.s3_secret_key),
            s3_bucket=os.getenv(s3_settings.interim_bucket.s3_bucket_name),
        )
        project_prefix_text3434 = str(Path(s3_settings.prefix) / project_name / 'data' / 'interim' / 'ml')
        s3c_interim.upload_file_to_s3(filepath=str(project_paths.path_folder_text_3434) + r"/text_3434.csv", s3_prefix=project_prefix_text3434, s3_key='text_3434.csv')
    
    return True