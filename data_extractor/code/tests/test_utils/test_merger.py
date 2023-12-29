import pytest
from utils.merger import Merger
from utils.settings import MainSettings, S3Settings, MainBucketSettings, InterimBucketSettings
from utils.paths import ProjectPaths
from unittest.mock import patch, Mock
from utils.s3_communication import S3Communication
from pathlib import Path

@pytest.fixture
def merger(main_settings: MainSettings,
           s3_settings: S3Settings,
           project_paths: ProjectPaths):
    return Merger(main_settings, s3_settings, project_paths)

@pytest.mark.parametrize('s3_usage', [True, False])
def test_setup_s3_usage(merger: Merger,
                        s3_usage: bool):
    
    with patch.object(merger.main_settings.general, 's3_usage', s3_usage):
        merger._setup_s3_usage()

    if s3_usage:
        assert isinstance(merger.s3_communication_main, S3Communication)
        assert isinstance(merger.s3_communication_interim, S3Communication)
    else:
        assert merger.s3_communication_main is None
        assert merger.s3_communication_interim is None


@pytest.mark.parametrize('bucket_settings_object', 
                         [MainBucketSettings, InterimBucketSettings])
def test_return_s3_communication_main(merger: Merger,
                                      bucket_settings_object: MainBucketSettings | InterimBucketSettings):
    settings: dict = {
        's3_endpoint': 'LANDING_AWS_ENDPOINT',
        's3_access_key': 'LANDING_AWS_ACCESS_KEY',
        's3_secret_key': 'LANDING_AWS_SECRET_KEY',
        's3_bucket_name': 'LANDING_AWS_BUCKET_NAME'}
    

    with (patch('utils.merger.S3Communication') as mocked_s3_communication,
          patch('utils.merger.os.getenv', side_effect=lambda args: args),
          patch.object(merger.s3_settings, 'main_bucket', 
                       bucket_settings_object(**settings))):
        merger._return_s3_communication_main()

    mocked_s3_communication.assert_called_with(
        s3_endpoint_url=settings['s3_endpoint'],
        aws_access_key_id=settings['s3_access_key'],
        aws_secret_access_key=settings['s3_secret_key'],
        s3_bucket=settings['s3_bucket_name']
    )

def test_download_inference_related_files_from_s3(merger: Merger):
    string_path_from_s3: str = str(Path(merger.s3_settings.prefix) / merger.project_paths.string_project_name / 'data' / 'output' / 'RELEVANCE' / 'Text')
    string_path_local_folder: str = str(merger.project_paths.path_folder_relevance)

    with patch.object(merger, 's3_communication_main') as mocked_s3_communication:
        merger._download_inference_related_files_from_s3()

    mocked_s3_communication.download_files_in_prefix_to_dir.assert_called_with(
        string_path_from_s3,
        string_path_local_folder)

def test_upload_to_s3():
    pass

def test_write_output():
    pass