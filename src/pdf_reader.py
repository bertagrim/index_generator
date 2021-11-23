
import re
import pandas as pd
import pdftotext
import fitz
from sentence_splitter import SentenceSplitter

pd.options.mode.chained_assignment = None
pd.set_option('display.max_rows', None)
pd.set_option('display.max_colwidth', None)

splitter = SentenceSplitter(language="en")


def get_page_count(filepath):
    # WARNING! One page can have multiple bookmarks!
    with fitz.open(filepath) as doc:
        num_pages = doc.page_count  # [[lvl, title, page, …], …]
    return num_pages


def num2roman(num):
    num_map = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'),
               (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]

    roman = ''
    while num > 0:
        for i, r in num_map:
            while num >= i:
                roman = roman + r
                num = num - i
    return roman


def get_dict_pages(filepath):
    dict_pages = {}
    with fitz.open(filepath) as doc:
        page_labels = doc.get_page_labels()
    for item in page_labels:
        abs_page = item['startpage']
        if item['prefix'] != '':
            real_page = item['prefix']
        else:
            if item['style'] == 'r':
                # transform to arabic numeral
                real_page = [item['firstpagenum'], 'r']
            elif item['style'] == 'D':
                real_page = [item['firstpagenum'], 'd']
        dict_pages[abs_page] = real_page
    return dict_pages


def translate(filepath):
    num_pages = get_page_count(filepath)
    dict_pages = get_dict_pages(filepath)

    trans_dict = {}
    real_num = 0
    abs_num = 0
    is_roman = False

    while abs_num < num_pages:
        if abs_num not in dict_pages.keys():
            if is_roman:
                trans_dict[abs_num] = num2roman(real_num)
            else:
                trans_dict[abs_num] = real_num
            abs_num += 1
            real_num += 1
        else:
            if type(dict_pages[abs_num]) == str:
                trans_dict[abs_num] = dict_pages[abs_num]
                real_num += 1
                abs_num += 1
            else:
                if dict_pages[abs_num][1] == 'r':
                    is_roman = True
                    trans_dict[abs_num] = num2roman(dict_pages[abs_num][0])
                else:
                    trans_dict[abs_num] = dict_pages[abs_num][0]
                    is_roman = False
                real_num = dict_pages[abs_num][0]+1
                abs_num += 1

    return trans_dict


def get_number_translator(filepath):
    trans_dict = None

    try:
        trans_dict = translate(filepath)
    except:
        pass

    def translate_number(x):
        if trans_dict is None:
            return x
        else:
            return trans_dict[x]

    return translate_number


def get_bookmarks(filepath):
    bookmarks = {}
    with fitz.open(filepath) as doc:
        toc = doc.get_toc()
        for level, title, page in toc:
            if page-1 not in bookmarks:
                bookmarks[page-1] = [[level, title]]
            else:
                bookmarks[page-1] += [[level, title]]
    return bookmarks


def get_all_sections(filepath):
    num_pages = get_page_count(filepath)
    dict_sections = get_bookmarks(filepath)
    complete_sections_dict = {}
    sect1 = ''
    sect2 = ''
    sect3 = ''
    for page in dict_sections:
        if len(dict_sections[page]) == 1:
            for item in dict_sections[page]:
                if item[0] == 1:
                    sect1 = item[1]
                    sect2 = ''
                    sect3 = ''
                elif item[0] == 2:
                    sect2 = item[1]
                    sect3 = ''
                elif item[0] == 3:
                    sect3 = item[1]
            complete_sections_dict[page] = [[1, sect1], [2, sect2], [3, sect3]]
        elif len(dict_sections[page]) == 2:
            for item in dict_sections[page]:
                if item[0] == 1:
                    sect1 = item[1]
                    sect2 = ''
                    sect3 = ''
                elif item[0] == 2:
                    sect2 = item[1]
                    sect3 = ''
                elif item[0] == 3:
                    sect3 = item[1]
            complete_sections_dict[page] = [[1, sect1], [2, sect2], [3, sect3]]

        elif len(dict_sections[page]) == 3:
            for item in dict_sections[page]:
                if item[0] == 1:
                    sect1 = item[1]
                    sect2 = ''
                    sect3 = ''
                elif item[0] == 2:
                    sect2 = item[1]
                    sect3 = ''
                elif item[0] == 3:
                    sect3 = item[1]
            complete_sections_dict[page] = [[1, sect1], [2, sect2], [3, sect3]]
        else:
            continue

    page = list(dict_sections.keys())[0]
    while page < num_pages:
        if page in complete_sections_dict:
            current_values = complete_sections_dict[page]
            page += 1
        else:
            complete_sections_dict[page] = current_values
            page += 1

    for page in range(num_pages):
        if page < num_pages and page not in complete_sections_dict:
            complete_sections_dict[page] = [
                [1, 'Out of toc'], [2, 'Out of toc'], [3, 'Out of toc']]
            page += 1

    complete_sections_dict = dict(
        sorted(complete_sections_dict.items(), key=lambda x: x[0]))
    return complete_sections_dict


def process_pages(file_path):
    """
    returns a list of lists that have as first element the content of one page and 
    as the second element its page number (starting from 0)
    """
    file = open(file_path, 'rb')
    content_per_page = pdftotext.PDF(file)
    file.close()

    list_pages = []
    page_count = 0
    for page in content_per_page:
        content = page

        # recover hyphen-splitter sentences
        pattern_line_break_1 = re.compile(r"-\n")
        pattern_line_break_2 = re.compile(r"(?<![.?¿!¡º])\s*\n(?=\s*[a-z])")

        content_processed = pattern_line_break_1.sub("", content)
        content_processed = pattern_line_break_2.sub(" ", content_processed)

        # Split lines
        splitter = SentenceSplitter(language="en")
        split_file = splitter.split(text=content_processed)
        page_content = "\n".join(split_file)

        list_pages.append([page_content, page_count])
        page_count += 1

    return list_pages


def dictionary_per_level_1(filepath):
    dict_level_1 = {}
    complete_sections_dict = get_all_sections(filepath)

    for key in complete_sections_dict:
        dict_level_1[key] = complete_sections_dict[key][0][1]

    return dict_level_1


def dictionary_per_level_2(filepath):
    dict_level_2 = {}
    complete_sections_dict = get_all_sections(filepath)

    for key in complete_sections_dict:
        dict_level_2[key] = complete_sections_dict[key][1][1]

    return dict_level_2


def dictionary_per_level_3(filepath):
    dict_level_3 = {}
    complete_sections_dict = get_all_sections(filepath)

    for key in complete_sections_dict:
        dict_level_3[key] = complete_sections_dict[key][2][1]

    return dict_level_3


def extend_pages_df(file_path, pages_df):
    dictionary1 = dictionary_per_level_1(file_path)
    dictionary2 = dictionary_per_level_2(file_path)
    dictionary3 = dictionary_per_level_3(file_path)
    pages_df['real_page_num'] = pages_df['page_number'].apply(
        get_number_translator(file_path)
    )
    pages_df['section_level_1'] = pages_df['page_number'].apply(
        lambda x: dictionary1[x]
    )
    pages_df['section_level_2'] = pages_df['page_number'].apply(
        lambda x: dictionary2[x]
    )
    pages_df['section_level_3'] = pages_df['page_number'].apply(
        lambda x: dictionary3[x]
    )
    return pages_df


def list_lines(pages_df):
    pages_list = pages_df.values.tolist()
    lines_list = []
    for item in pages_list:
        if type(item[0]) == str:
            split_file = splitter.split(text=item[0])
            for line in split_file:
                lines_list.append(
                    [line, item[1], item[2], item[3], item[4], item[5]])
        else:
            lines_list.append([item[0], item[1], item[2],
                              item[3], item[4], item[5]])
    return lines_list


def parse_pdf(file_path):
    """
    file_path: Relative path to PDF file.
    returns: Dictionary with dataframes for the indexed lines and pages.
    """
    file_name = file_path.split("/")[-1]
    page_list = process_pages(file_path)
    pages_df = extend_pages_df(
        file_path,
        pd.DataFrame(page_list, columns=['content', 'page_number'])
    )
    lines_df = pd.DataFrame(list_lines(pages_df), columns=pages_df.columns)

    return {
        'file_name': file_name,
        'by_page': pages_df,
        'by_line': lines_df
    }
