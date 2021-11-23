import pathlib
from glob import glob
import pandas as pd
from sentence_splitter import SentenceSplitter
from pdf_reader import process_pages, get_number_translator

pd.options.mode.chained_assignment = None
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)

splitter = SentenceSplitter(language="en")


def get_pdf_filepaths(folder_path):
    absolute_folder_path = pathlib.Path(folder_path).resolve()
    pattern = str(absolute_folder_path / "*.pdf")
    return glob(pattern)

def get_agg_dfs_filepaths(folder_path):
    absolute_folder_path = pathlib.Path(folder_path).resolve()
    pattern = str(absolute_folder_path / '**/aggregated.csv')
    return glob(pattern)

def get_agg_dfs_filepaths_philosophy(folder_path):
    absolute_folder_path = pathlib.Path(folder_path).resolve()
    pattern = str(absolute_folder_path / 'philosophy/**/aggregated.csv')
    return glob(pattern)



def list_lines(pages_df):
    pages_list = pages_df.values.tolist()
    lines_list = []

    for item in pages_list:
        if type(item[0]) == str:
            split_file = splitter.split(text=item[0])
            for line in split_file:
                lines_list.append(
                    [line, item[1], item[2], item[3], item[4], item[5]]
                )
        else:
            lines_list.append(
                [item[0], item[1], item[2], item[3], item[4], item[5]]
            )
    return lines_list


def load_page_and_line_indexes(processed_data_dir_path, pdf_filepath):
    file_base_name = pathlib.Path(pdf_filepath).stem
    file_folder_path = pathlib.Path(
        processed_data_dir_path + file_base_name + "/"
    ).resolve()
    raw_by_line_file_path = file_folder_path / "raw_by_line.csv"
    raw_by_page_file_path = file_folder_path / "raw_by_page.csv"
    return {
        'file_name': file_base_name + ".pdf",
        'by_line': pd.read_csv(raw_by_line_file_path, index_col=0),
        'by_page': pd.read_csv(raw_by_page_file_path, index_col=0)
    }


def load_split_data(processed_data_dir_path, pdf_filepath):
    file_base_name = pathlib.Path(pdf_filepath).stem
    file_folder_path = pathlib.Path(
        processed_data_dir_path + file_base_name + "/"
    ).resolve()
    by_line_index_file_path = file_folder_path / "by_line_index.csv"
    by_page_biblio_file_path = file_folder_path / "by_page_biblio.csv"
    by_line_body_file_path = file_folder_path / "by_line_body.csv"
    by_line_toc_file_path = file_folder_path / "by_line_toc.csv"
    by_page_body_file_path = file_folder_path / "by_page_body.csv"

    by_line_index = pd.read_csv(by_line_index_file_path, index_col=0)
    by_page_biblio = pd.read_csv(by_page_biblio_file_path, index_col=0)
    by_line_body = pd.read_csv(by_line_body_file_path, index_col=0)
    by_line_toc = pd.read_csv(by_line_toc_file_path, index_col=0)
    by_page_body = pd.read_csv(by_page_body_file_path, index_col=0)

    by_line_body = by_line_body.fillna('')
    by_page_body = by_page_body.fillna('')
    by_line_toc = by_line_toc.fillna('')
    by_line_index = by_line_index.fillna('')

    return {
        'file_name': file_base_name + ".pdf",
        'by_line_index': by_line_index,
        'by_page_biblio': by_page_biblio,
        'by_line_body': by_line_body,
        'by_line_toc': by_line_toc,
        'by_page_body': by_page_body,
    }


def load_raw_indexes_list(processed_data_dir_path, pdf_filepath):
    file_base_name = pathlib.Path(pdf_filepath).stem
    file_folder_path = pathlib.Path(
        processed_data_dir_path + file_base_name + "/"
    ).resolve()
    file_path = file_folder_path / "raw_indexes.txt"
    file = open(file_path, 'r')
    clean_raw_indexes = file.readlines()
    file.close()
    return clean_raw_indexes
