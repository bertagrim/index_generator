import re
from re import split
import pathlib
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
from config import part_limits
import pandas as pd

stop_words = stopwords.words("english")
lemmatizer = WordNetLemmatizer()


def compose(fs):
    def composition(x):
        for f in fs:
            x = f(x)
        return x
    return composition


def remove_blank_pages(data_frame):
    data_frame = data_frame[
        ~data_frame.content.str.match(
            "This page intentionally left blank", na=False
        )
    ]
    data_frame = data_frame[
        ~data_frame.content.str.match(
            "This page was intentionally left blank", na=False
        )
    ]
    return data_frame


def drop_na(data_frame):
    data_frame.content.dropna(inplace=True)
    return data_frame


def remove_non_alphabetic(data_frame):
    return data_frame[~data_frame.content.str.match("^[^a-zA-Z]*\d+[^a-zA-Z]*$")]


def remove_empty_lines(data_frame):
    return data_frame[~data_frame.content.str.match("^$")]


def remove_non_alphanumeric(data_frame):
    return data_frame[~data_frame.content.str.match("^[^\w]+$")]


def reset_index(data_frame):
    data_frame.reset_index(drop=True, inplace=True)
    return data_frame


def fill_sections_na(data_frame):
    data_frame.section_level_1.fillna("", inplace=True)
    data_frame.section_level_2.fillna("", inplace=True)
    data_frame.section_level_3.fillna("", inplace=True)
    return data_frame


def get_toc(file_name, data_frame):
    fill_sections_na(data_frame)

    base_name = pathlib.Path(file_name).stem
    toc = None
    if 'toc' in part_limits[base_name]:
        [start, end] = part_limits[base_name]['toc']
        toc = data_frame[
            (data_frame.page_number >= start) & (data_frame.page_number <= end)
        ]
    else:
        toc = data_frame[
            data_frame.section_level_1.str.match(
                "CONTENTS|Contents|contents|Table of Contents|Table of contents"
            ) |
            data_frame.section_level_2.str.match(
                "CONTENTS|Contents|contents|Table of Contents|Table of contents"
            ) |
            data_frame.section_level_3.str.match(
                "CONTENTS|Contents|contents|Table of Contents|Table of contents"
            )
        ]

    toc.reset_index(drop=True, inplace=True)
    return toc


def get_body(file_name, data_frame):
    base_name = pathlib.Path(file_name).stem
    [start, end] = part_limits[base_name]['body']
    # pd.to_numeric(data_frame.page_number)
    # print(data_frame.page_number)

    body = data_frame[
        (data_frame.page_number >= start) & (data_frame.page_number <= end)
    ]
    body.reset_index(drop=True, inplace=True)
    return body


def get_index(file_name, data_frame):
    fill_sections_na(data_frame)

    base_name = pathlib.Path(file_name).stem
    index = None
    if 'index' in part_limits[base_name]:
        [start, end] = part_limits[base_name]['index']
        index = data_frame[
            (data_frame.page_number >= start) & (data_frame.page_number <= end)
        ]
    else:
        index = data_frame[
            data_frame.section_level_1.str.match(
                "INDEX|index|Index|Subject Index|Name Index|Language Index|Citation Index|General Index|Author Index|Indicies"
            ) |
            data_frame.section_level_2.str.match(
                "INDEX|index|Index|Subject Index|Name Index|Language Index|Citation Index|General Index|Author Index|Indicies"
            ) |
            data_frame.section_level_3.str.match(
                "INDEX|index|Index|Subject Index|Name Index|Language Index|Citation Index|General Index|Author Index|Indicies"
            )
        ]
    index.reset_index(drop=True, inplace=True)
    return index


def get_biblio(file_name, data_frame):
    fill_sections_na(data_frame)

    base_name = pathlib.Path(file_name).stem
    biblio = None

    if 'biblio' in part_limits[base_name]:
        [start, end] = part_limits[base_name]['biblio']
        biblio = data_frame[
            (data_frame.page_number >= start) & (data_frame.page_number <= end)
        ]
    else:
        biblio = data_frame[
            data_frame.section_level_1.str.match(
                "REFERENCES|References|references|Bibliography|bibliography|Works cited|Selected HistoricalWorks on Linear Algebra"
            ) |
            data_frame.section_level_2.str.match(
                "REFERENCES|References|references|Bibliography|bibliography|Works cited|Selected HistoricalWorks on Linear Algebra"
            ) |
            data_frame.section_level_3.str.match(
                "REFERENCES|References|references|Bibliography|bibliography|Works cited|Selected HistoricalWorks on Linear Algebra"
            )
        ]
    biblio.reset_index(drop=True, inplace=True)
    return biblio


def clean_initial_indexes(line_and_page_indexes):
    apply_initial_cleaning_steps = compose([
        remove_blank_pages,
        drop_na,
        remove_non_alphabetic,
        remove_empty_lines,
        remove_non_alphanumeric,
        reset_index,
        fill_sections_na,
    ])
    line_and_page_indexes['by_page'] = apply_initial_cleaning_steps(
        line_and_page_indexes['by_page']
    )
    line_and_page_indexes['by_line'] = apply_initial_cleaning_steps(
        line_and_page_indexes['by_line']
    )
    return line_and_page_indexes


def clean_text(text_data):
    tokens = word_tokenize(text_data)
    no_weird_dash = [w.replace('—', '-') for w in tokens]
    no_weird_dash2 = [w.replace('-', '-') for w in no_weird_dash]
    no_slash = sum([w.split('/') for w in no_weird_dash2], [])
    lowercased = [w.lower() for w in no_slash]
    no_punct = [
        word for word in lowercased if (
            word.isalpha() or re.match("[a-z]+-[a-z]+", word)
        )
    ]
    no_sw = [w for w in no_punct if w not in stop_words]
    clean_tokens = [lemmatizer.lemmatize(word) for word in no_sw]

    #no_tw=[w for w in clean_tokens if w not in textbook_words]
    # long_words=[w for w in no_tw if len(w)>2]#try it with larger than 1 as well

    return (" ").join(clean_tokens)


def split_data(file_name, data_frame):
    toc = get_toc(file_name, data_frame)
    body = get_body(file_name, data_frame)
    index = get_index(file_name, data_frame)
    biblio = get_biblio(file_name, data_frame)

    toc['clean_content'] = toc['content'].apply(clean_text)
    body['clean_content'] = body['content'].apply(clean_text)

    return {
        'toc': toc,
        'body': body,
        'index': index,
        'biblio': biblio
    }


def add_split_data(file_path, line_and_page_indexes):
    file_name = pathlib.Path(file_path).name
    by_line_split_data = split_data(
        file_name=file_name,
        data_frame=line_and_page_indexes['by_line']
    )
    by_page_split_data = split_data(
        file_name=file_name,
        data_frame=line_and_page_indexes['by_page']
    )
    return {
        **line_and_page_indexes,
        'by_line_toc': by_line_split_data['toc'],
        'by_line_body': by_line_split_data['body'],
        'by_line_index': by_line_split_data['index'],
        'by_line_biblio': by_line_split_data['biblio'],
        'by_page_toc': by_page_split_data['toc'],
        'by_page_body': by_page_split_data['body'],
        'by_page_index': by_page_split_data['index'],
        'by_page_biblio': by_page_split_data['biblio'],
    }
