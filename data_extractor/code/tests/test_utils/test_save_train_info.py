from pathlib import Path
from utils.utils import save_train_info
import pytest
from unittest.mock import patch, Mock
import shutil
import train_on_pdf
import pickle
from utils.paths import ProjectPaths
from utils.settings import Settings


@pytest.fixture
def project_paths(main_settings: Settings) -> ProjectPaths:
    return ProjectPaths('test_project', main_settings)


@pytest.fixture(autouse=True)
def prerequisites_save_train_info(path_folder_root_testing: Path,
                                  path_folder_temporary: Path) -> Path:
    """Defines a fixture for creating all prerequisites for save_train_info

    :param path_folder_root_testing: Requesting the root testing folder fixture
    :type path_folder_root_testing: Path
    :param path_folder_temporary: Requesting the path_folder_temporary fixture
    :type path_folder_temporary: Path
    :return: Returns path to pickled save_train_info file
    :rtype: Path
    :yield: Returns path to pickled save_train_info file
    :rtype: Iterator[Path]
    """
    mocked_project_settings = {
        'train_relevance': {
            'output_model_name': 'TEST_1'
            },
        'train_kpi':{
            'output_model_name': 'TEST_1'
        },
        's3_settings': {
            'prefix' : 'corporate_data_extraction_projects'
        }
    }

    path_source_pdf = path_folder_root_testing / 'input' / 'pdf' / 'training'
    path_source_annotation = path_folder_root_testing / 'input' / 'pdfs' / 'training'
    path_source_mapping = path_folder_root_testing / 'data' / 'TEST' / 'input' / 'kpi_mapping'
    path_project_model_dir = path_folder_temporary / 'models'
    path_project_model_dir.mkdir(parents=True, exist_ok=True)

    relevance_model = mocked_project_settings['train_relevance']['output_model_name']
    kpi_model = mocked_project_settings['train_kpi']['output_model_name']
    file_train_info = f'SUMMARY_REL_{relevance_model}_KPI_{kpi_model}.pickle'
    path_train_info = path_project_model_dir / file_train_info

    with (patch('train_on_pdf.project_settings', mocked_project_settings),
          patch('train_on_pdf.source_annotation', str(path_source_annotation)),
          patch('train_on_pdf.source_mapping', str(path_source_mapping)),
          patch('train_on_pdf.os.listdir', side_effect=lambda *args: 'test.pdf'),
          patch('train_on_pdf.source_mapping', str(path_folder_temporary / 'source_mapping')),
          patch('train_on_pdf.source_annotation', str(path_folder_temporary / 'source_annotation')),
          patch('train_on_pdf.source_pdf', str(path_folder_temporary / 'source_pdf')),
          patch('utils.utils.pd', Mock()) as mocked_pandas):
        # train_on_pdf.project_model_dir = str(path_project_model_dir)
        mocked_pandas.read_csv.return_value = {None}
        mocked_pandas.read_excel.return_value = {None}
        yield path_train_info
        
        # cleanup
        shutil.rmtree(path_folder_temporary)
        # del train_on_pdf.project_model_dir


def test_save_train_info_pickle(prerequisites_save_train_info: Path, project_paths: ProjectPaths,
                                s3_settings: Settings, main_settings: Settings):
    """Tests if the train info is pickle correctly

    :param prerequisites_save_train_info: Requesting the prerequisites_save_train_info fixture
    :type prerequisites_save_train_info: Path
    """
    project_name = 'TEST'
    mocked_s3 = Mock()
    path_train_info = prerequisites_save_train_info
    project_paths._path_project_model_folder = Path(prerequisites_save_train_info).parent
    
    save_train_info(project_name, s3_usage=False, s3c_main=mocked_s3, project_paths=project_paths, s3_settings=s3_settings, main_settings=main_settings)
    
    # we have to combine a pathlib and a string object...
    path_parent_train_info = path_train_info.parent
    path_file_pickle = path_train_info.name
    path_train_info = Path(str(path_parent_train_info) + f'/{path_file_pickle}')
    
    assert path_train_info.exists()
  
  
def test_save_train_info_entries(prerequisites_save_train_info: Path, project_paths: ProjectPaths,
                                 s3_settings: Settings, main_settings: Settings):
    """Tests if all the train infos exists in the pickled train info file

    :param prerequisites_save_train_info: Requesting the prerequisites_save_train_info fixture
    :type prerequisites_save_train_info: Path
    """
    project_name = 'TEST'
    mocked_s3 = Mock()
    path_train_info = prerequisites_save_train_info
    project_paths._path_project_model_folder = Path(prerequisites_save_train_info).parent
    
    save_train_info(project_name, s3_usage=False, s3c_main=mocked_s3, project_paths=project_paths, s3_settings=s3_settings, main_settings=main_settings)
    
    with open(str(path_train_info), 'rb') as file:
        train_info = pickle.load(file)
    
    expected_keys = [
        'project_name',
        'train_settings',
        'pdfs_used',
        'annotations',
        'kpis'
    ]
    # check that all keys exist in dict
    assert all(key in expected_keys for key in train_info.keys())

    
def test_save_tain_info_return_value(prerequisites_save_train_info: Path, project_paths: ProjectPaths,
                                     s3_settings: Settings, main_settings: Settings):
    project_name = 'TEST'
    mocked_s3 = Mock()
    path_train_info = prerequisites_save_train_info
    project_paths._path_project_model_folder = Path(prerequisites_save_train_info).parent
    
    assert save_train_info(project_name, s3_usage=False, s3c_main=mocked_s3, project_paths=project_paths, s3_settings=s3_settings, main_settings=main_settings) is None
    

def test_save_train_info_s3_usage(prerequisites_save_train_info: Path, project_paths: ProjectPaths,
                                  s3_settings: Settings, main_settings: Settings):
    """Tests if the s3_usage flag correctly works

    """
    project_name = 'TEST'
    s3_usage = True
    mocked_s3 = Mock()
    path_train_info = prerequisites_save_train_info
    project_paths._path_project_model_folder = Path(prerequisites_save_train_info).parent

    save_train_info(project_name, s3_usage, mocked_s3, project_paths=project_paths, s3_settings=s3_settings, main_settings=main_settings)
    
    assert mocked_s3.download_files_in_prefix_to_dir.call_count == 3
    assert mocked_s3.upload_file_to_s3.called_once()
        
