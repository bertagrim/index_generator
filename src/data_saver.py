import pathlib


def get_or_create_file_folder_path(processed_data_dir_path, data_frame):
    file_name = data_frame['file_name']
    file_base_name = ".".join(file_name.split(".")[:-1])
    file_folder_path = pathlib.Path(
        processed_data_dir_path + file_base_name + "/"
    ).resolve()
    file_folder_path.mkdir(exist_ok=True)
    return file_folder_path


def save_page_and_line_indexes(processed_data_dir_path, line_and_page_indexes):
    file_folder_path = get_or_create_file_folder_path(
        processed_data_dir_path,
        line_and_page_indexes
    )
    raw_by_lines_file_path = file_folder_path / "raw_by_line.csv"
    raw_by_pages_file_path = file_folder_path / "raw_by_page.csv"
    line_and_page_indexes['by_line'].to_csv(
        raw_by_lines_file_path, encoding="utf8", mode='w+'
    )
    line_and_page_indexes['by_page'].to_csv(
        raw_by_pages_file_path, encoding="utf8",  mode='w+'
    )


def save_split_data(processed_data_dir_path, split_data):
    file_folder_path = get_or_create_file_folder_path(
        processed_data_dir_path,
        split_data
    )
    by_line_index_file_path = file_folder_path / "by_line_index.csv"
    by_page_biblio_file_path = file_folder_path / "by_page_biblio.csv"
    by_line_body_file_path = file_folder_path / "by_line_body.csv"
    by_line_toc_file_path = file_folder_path / "by_line_toc.csv"
    by_page_body_file_path = file_folder_path / "by_page_body.csv"
    split_data['by_line_index'].to_csv(
        by_line_index_file_path, encoding="utf8", mode='w+'
    )
    split_data['by_page_biblio'].to_csv(
        by_page_biblio_file_path, encoding="utf8", mode='w+'
    )
    split_data['by_line_body'].to_csv(
        by_line_body_file_path, encoding="utf8", mode='w+'
    )
    split_data['by_line_toc'].to_csv(
        by_line_toc_file_path, encoding="utf8", mode='w+'
    )
    split_data['by_page_body'].to_csv(
        by_page_body_file_path, encoding="utf8", mode='w+'
    )


def save_raw_indexes_list(processed_data_dir_path, pdf_filepath, raw_indexes_list):
    file_base_name = pathlib.Path(pdf_filepath).stem
    file_folder_path = pathlib.Path(
        processed_data_dir_path + file_base_name + "/"
    ).resolve()
    file_path = file_folder_path / "raw_indexes.txt"
    f = open(file_path, 'w+')
    lines = [(",").join(sublist)+"\n" for sublist in raw_indexes_list]
    f.writelines(lines)
    f.close()
