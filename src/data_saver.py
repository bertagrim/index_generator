import pathlib


def get_or_create_file_folder_path(processed_data_dir_path, file_name):
    file_base_name = ".".join(file_name.split(".")[:-1])
    file_folder_path = pathlib.Path(
        processed_data_dir_path + file_base_name + "/"
    ).resolve()
    file_folder_path.mkdir(exist_ok=True)
    return file_folder_path


def save_page_and_line_indexes(processed_data_dir_path, line_and_page_indexes):
    file_folder_path = get_or_create_file_folder_path(
        processed_data_dir_path,
        line_and_page_indexes['file_name']
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
        split_data['file_name']
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


def save_aggregated_data(processed_data_dir_path, agg_df, file_name):
    file_folder_path = get_or_create_file_folder_path(
        processed_data_dir_path,
        file_name
    )
    aggregated_file_path = file_folder_path / "aggregated.csv"
    agg_df.to_csv(
        aggregated_file_path, encoding="utf8", mode='w+'
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


def get_line_numbers_concat(line_nums):
    seq = []
    final = []
    last = 0

    for index, val in enumerate(line_nums):

        if last + 1 == val or last + 2 == val or index == 0:
            seq.append(val)
            last = val
        else:
            if len(seq) > 1:
                final.append(str(seq[0]) + '-' + str(seq[len(seq)-1]))
            else:
                final.append(str(seq[0]))
            seq = []
            seq.append(val)
            last = val

        if index == len(line_nums) - 1:
            if len(seq) > 1:
                final.append(str(seq[0]) + '-' + str(seq[len(seq)-1]))
            else:
                final.append(str(seq[0]))

    final_str = ', '.join(map(str, final))
    return final_str


def get_markdown_index(candidates_dataframe, pages_body_dataframe):
    keywords = candidates_dataframe[
        candidates_dataframe.is_in_index == 1
    ]['candidate_keyword'].tolist()
    dict_pagination = {}
    for kw in keywords:
        pages_kw = pages_body_dataframe[pages_body_dataframe['clean_content'].str.contains(
            kw)]
        pages = pages_kw['real_page_num'].tolist()
        dict_pagination[kw] = get_line_numbers_concat(pages)
    md_string = '## Index\n'
    last_unigram = ''
    for word in dict_pagination:
        if len(word.split(' ')) == 1:
            md_string += '- '+word+' '+dict_pagination[word]+'\n'
            last_unigram = word
        else:
            if last_unigram in word.split(' '):
                md_string += '    - '+word+' '+dict_pagination[word]+'\n'
            else:
                md_string += '- '+word+' '+dict_pagination[word]+'\n'
    return md_string


def get_txt_index(candidates_dataframe, pages_body_dataframe):
    keywords = candidates_dataframe[
        candidates_dataframe.is_in_index == 1
    ]['candidate_keyword'].tolist()
    dict_pagination = {}
    for kw in keywords:
        pages_kw = pages_body_dataframe[pages_body_dataframe['clean_content'].str.contains(
            kw)]
        pages = pages_kw['real_page_num'].tolist()
        dict_pagination[kw] = get_line_numbers_concat(pages)
    txt_string = 'Index\n\n'
    last_unigram = ''
    for word in dict_pagination:
        if len(word.split(' ')) == 1:
            txt_string += '- '+word+' '+dict_pagination[word]+'\n\n'
            last_unigram = word
        else:
            if last_unigram in word.split(' '):
                txt_string += '    - '+word+' '+dict_pagination[word]+'\n\n'
            else:
                txt_string += '- '+word+' '+dict_pagination[word]+'\n\n'
    return txt_string
