from typing import Dict, Any
from pathlib import Path
import yaml
from utils.settings import S3Settings, MainSettings, Settings

class SettingsHandler():
    """
    Class for reading and writing setting files
    """
    def __init__(self, 
                 main_settings: MainSettings = MainSettings(), 
                 s3_settings: S3Settings = S3Settings()):
        self.main_settings: MainSettings = main_settings
        self.s3_settings: S3Settings = s3_settings
    
    def read_settings(self, 
                      path_main_settings=Path(__file__).parent.parent.resolve() / 'data' / 'TEST' / 'settings.yaml',
                      path_s3_settings=Path(__file__).parent.parent.resolve() / 'data' / 's3_settings.yaml'):

        try:
            with (open(str(path_main_settings)) as file_main_settings,
                  open(str(path_s3_settings)) as file_settings_3):
                
                self.main_settings = yaml.safe_load(file_main_settings)
                self.s3_settings = yaml.safe_load(file_s3_settings)
        except:
            pass

    @staticmethod
    def _read_setting_file(path: Path) -> Settings:
        with open(path, mode='r') as file_settings:
            loaded_settings: dict = yaml.safe_load(file_settings)
        settings: Settings = SettingsHandler._settings_factory(loaded_settings)
        return settings(**loaded_settings)
    
    @staticmethod
    def _settings_factory(settings: dict) -> Settings:
        if 'main_bucket' in settings:
            return S3Settings
        else:
            return MainSettings
    
    def write_settings(self):
        pass
    