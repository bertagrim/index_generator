import re
import pandas as pd
import numpy as np
from collections import Counter

from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.util import ngrams
from nltk.corpus import stopwords
import spacy

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import scipy

lemmatizer = WordNetLemmatizer()

nlp = spacy.load('en_core_web_sm')


# 1. Get candidates plus frequencies

def create_candidates_list(bigrams_contexts):
    candidates=[]
    dismiss=['-','i','d','m','the','is','—', 'elementsâ•', '…', 'distributiveâ•', 'elementâ•', 's', '/', 'he', '.', 'viz', 'tr-1', 'tr-2', 'tr-3', 'tr-50', 'r-1a', 'r-1', 'efficient-']
    for item in bigrams_contexts:
        doc=nlp((' ').join(item[1]))
        for word in item[1]:
            word=word.replace('—','-')
            if re.match("[a-z]+-[a-z]+(-[a-z])*", word):
                candidates.append([word, item[1], item[2], 'NOUN'])
                dismiss+=word.split('-')
        for w in doc:
            if not(str(w) in dismiss):
                candidates.append([str(w), item[1], item[2], w.pos_])
        for w in item[0]:
            candidates.append([w, item[1], item[2], 'CHUNK'])
    return candidates 


def get_raw_sentences(raw_sent):
    tokens = word_tokenize(raw_sent)
    no_weird_dash=[w.replace('—','-') for w in tokens]
    no_slash=sum([w.split('/') for w in no_weird_dash],[])
    lowercased = [w.lower() for w in no_slash]
    no_punct = [word for word in lowercased if (
        word.isalpha() or re.match("[a-z]+-[a-z]+(-[a-z])*", word))]
    clean_raw_words = [lemmatizer.lemmatize(w) for w in no_punct]
    return (" ").join(clean_raw_words)


def get_candidates_and_frequencies(split_data):
    by_line_body_content = split_data['by_line_body']

    # print(list(by_line_body_content))

    sentences = [
        sentence.split() for sentence in by_line_body_content['clean_content']
    ]

    whole_text = ''
    for sentence in by_line_body_content['clean_content']:
        whole_text += ' '
        whole_text += sentence

    freq_bigrams_tuples = dict(
        Counter(
            ngrams(whole_text.split(), 2)
        )
    )
    freq_bigrams = {}

    for item in freq_bigrams_tuples.items():
        pair = item[0]
        pair_string = pair[0]+' '+pair[1]
        freq_bigrams[pair_string] = item[1]

    freq_unigrams = dict(Counter(whole_text.split()))

    freq_ngrams = dict(freq_unigrams, **freq_bigrams)

    list_bigrams_lines = [
        list(ngrams(sentence.split(), 2))
        for sentence in by_line_body_content['clean_content']
    ]

    list_bigrams_str = []
    for item in list_bigrams_lines:
        sublist = []
        for pair in item:
            string = pair[0]+' '+pair[1]
            sublist.append(string)
        list_bigrams_str.append(sublist)
    list_bigrams_str

    raw_sent = []
    for sent in by_line_body_content['content']:
        raw_sent.append(get_raw_sentences(sent))

    bigrams_and_contexts = list(
        zip(list_bigrams_str, sentences, raw_sent)
    )

    candidates_list = create_candidates_list(bigrams_and_contexts)

    candidates_df = pd.DataFrame(
        candidates_list,
        columns=[
            'candidate_keyword',
            'clean_context',
            'raw_context',
            'POS'
        ]
    )

    return (candidates_df, freq_ngrams)


# 2. Column frequencies


def get_book_length(by_ages_body_df):
    all_clean_content = []
    for page in by_ages_body_df['content']:
        all_clean_content += page.split(' ')
    return len(all_clean_content)


def get_frequency_calculator(book_length, freq_ngrams):
    def assign_frequency(candidate_keyword):
        count = freq_ngrams.get(candidate_keyword)
        if candidate_keyword not in freq_ngrams:
            #print(dismiss)
            print(candidate_keyword + " is not in freq_ngrams!!")
            return 0
        else:
            return count / book_length
    return assign_frequency


def add_frequencies_column(by_pages_body_df, candidates_df, freq_ngrams):
    book_length = get_book_length(by_pages_body_df)
    candidates_df['freq'] = candidates_df.candidate_keyword.apply(
        get_frequency_calculator(
            book_length=book_length, freq_ngrams=freq_ngrams
        )
    )
    return candidates_df


# 3. Column: is in toc


def clean_toc(text_data):
    tokens = word_tokenize(text_data)

    lowercased = [w.lower() for w in tokens]

    no_punct = [word for word in lowercased if (
        word.isalpha() or re.match("[a-z]+-[a-z]+", word))]

    clean_tokens = [lemmatizer.lemmatize(word) for word in no_punct]

    return (" ").join(clean_tokens)


def get_is_in_toc(words_toc):
    def is_in_toc(x):
        if "_" in x:
            if x.split("_")[0] in words_toc and x.split("_")[1] in words_toc:
                return 1
            else:
                return 0
        else:
            if x in words_toc:
                return 1
            else:
                return 0
    return is_in_toc


def add_is_in_toc(candidates_df, by_line_toc):
    words_toc = []
    cleaned_toc = by_line_toc.content.apply(clean_toc)
    for line in cleaned_toc:
        words_toc += line.split()

    candidates_df['is_in_toc'] = candidates_df.candidate_keyword.apply(
        get_is_in_toc(words_toc)
    )
    return candidates_df


# 4. Column: Importance

def form_sentence(x):
    return (' ').join(x)


def get_assign_similarities(similarities):
    def assign_similarities(x):
        return similarities[x]
    return assign_similarities


def add_importance(candidates_df):
    candidates_df.clean_context = candidates_df.clean_context.apply(
        form_sentence
    )

    doc = (' ').join(candidates_df.clean_context.unique())
    contexts = candidates_df.clean_context.unique()

    model = SentenceTransformer('distilbert-base-nli-mean-tokens')
    doc_embedding = model.encode([doc])
    context_embeddings = model.encode(contexts)

    distances = cosine_similarity(doc_embedding, context_embeddings)
    similarities = dict(
        zip(candidates_df.clean_context.unique(), list(distances[0]))
    )

    candidates_df['importance'] = candidates_df.clean_context.apply(
        get_assign_similarities(similarities)
    )

    return candidates_df


# 5. Column: position in sentence


def return_position_in_context(row):
    list_words = row['raw_context'].split(' ')
    list_words=sum([w.split('/') for w in list_words],[])
        
    word = row['candidate_keyword']
    #if word not in list_words:
       #print(word, row['raw_context'])
    if len(list_words) == 1:
        return 0
    else:
        if len(word) > 1:
            word = word.split(' ')[0]
            return list_words.index(word)/(len(list_words)-1)
        else:
            return list_words.index(word)/(len(list_words)-1)


def add_position_in_context(candidates_df):
    candidates_df['position_in_context'] = candidates_df.apply(
        return_position_in_context, axis=1
    )
    return candidates_df


# 6. Column: is a named entity

def clean_list_names(x):
    tokens = word_tokenize(x)
    lowercased = [w.lower() for w in tokens]
    no_punct = [
        word for word in lowercased if (
            word.isalpha() or re.match("[a-z]+-[a-z]+", word)
        )
    ]
    clean_tokens = [w for w in no_punct if len(w) > 2]
    return (" ").join(clean_tokens)


def find_named_entities(df_pages_body):
    named_entities = []
    for page in df_pages_body.content:
        page_named_entities = re.findall('(?<=[a-zA-Z] )[A-Z]+[a-z]+[A-Z]*[a-z]*', page)
        for item in page_named_entities:
            named_entities.append(clean_list_names(item))
    return named_entities


def add_is_named_entity(candidates_df, df_pages_body):
    named_entities = find_named_entities(df_pages_body)

    def is_named_entity(x):
        if x in named_entities:
            return 1
        else:
            return 0

    candidates_df['is_named_entity'] = candidates_df.candidate_keyword.apply(
        is_named_entity
    )

    return candidates_df


# 7. Column: length of word

def add_length_of_word(candidates_df):
    len_dict = {}
    for keyword in candidates_df.candidate_keyword.unique():
        len_dict[keyword] = len(keyword)

    def assign_len(x):
        return len_dict[x]

    candidates_df['length'] = candidates_df.candidate_keyword.apply(assign_len)

    return candidates_df


# 8. Column: is a named author


def find_authors_in_biblio(df_pages_biblio):
    def clean_name_candidate(x):
        tokens = word_tokenize(x)
        lowercased = [w.lower() for w in tokens]
        no_punct = [word for word in lowercased if word.isalpha()]
        clean_tokens = [w for w in no_punct if len(w) > 2]
        return (" ").join(clean_tokens)

    clean_list_authors = []
    for page in df_pages_biblio.content:
        name_candidates = re.findall(
            '[A-Z]\.\s[A-Za-z]+|[A-Za-z]+\,\s*[A-Z]\.', page
        )
        for name_candidate in name_candidates:
            if clean_name_candidate(name_candidate) != 'and' and clean_name_candidate(name_candidate) != '&':
                if clean_name_candidate(name_candidate) != '':
                    clean_list_authors.append(
                        clean_name_candidate(name_candidate)
                    )
    return clean_list_authors


def add_is_named_author(candidates_df, df_pages_biblio):
    unique_authors = set(find_authors_in_biblio(df_pages_biblio))

    def is_named_author(x, unique_authors):
        if x in unique_authors:
            return 1
        else:
            return 0

    candidates_df['is_named_author'] = candidates_df.candidate_keyword.apply(
        lambda candidate_keyword: is_named_author(
            candidate_keyword, unique_authors
        )
    )

    return candidates_df


# 9. Column: tf-idf score


def add_tfidf(candidates_df, df_pages_body):
    grouped_by_sections = df_pages_body.groupby(
        ['section_level_1', 'section_level_2', 'section_level_3']
    )['clean_content'].apply(' '.join).reset_index()

    tfdif_vectorizer = TfidfVectorizer(
        vocabulary=candidates_df.candidate_keyword.unique()
    )
    tfidf = tfdif_vectorizer.fit_transform(
        grouped_by_sections["clean_content"]
    )
    feature_names = tfdif_vectorizer.get_feature_names()

    df = pd.DataFrame(tfidf.T.todense(), index=feature_names)
    df = pd.DataFrame(df.max(axis=1), columns=['max_tfidf'])
    dict_tfidf = df.max_tfidf.to_dict()

    def assign_tfidf_score(x):
        return dict_tfidf[x]

    candidates_df['tfidf'] = candidates_df.candidate_keyword.apply(
        assign_tfidf_score
    )

    return candidates_df


# 10. Target column: is in index

index_words = ['page', 'see', 'also', 'index', 'bold']


def find_ngrams_index(text_data):
    list_bigrams = []
    for ngram in re.findall('[a-zA-z]+\s[a-zA-z]+\s[a-zA-z]+|[a-zA-z]+\s[a-zA-z]+|[a-zA-Z]+', text_data):
        list_bigrams.append(ngram)
    for hw in re.findall("[a-z]+-[a-z]+", text_data):
        list_bigrams.append(hw)
    return list_bigrams


def get_raw_indexes_list(df_cann_lines_index):
    df_cann_lines_index['ngrams'] = df_cann_lines_index.content.apply(
        find_ngrams_index
    )
    stop_words = stopwords.words("english")

    def clean_index(list_ngrams):
        clean_list_ngrams = []
        for ngram in list_ngrams:
            clean_ngram = []
            for w in ngram.split():
                clean_w = w.lower()
                clean_w = lemmatizer.lemmatize(clean_w)
                if clean_w not in stop_words and clean_w not in index_words:
                    clean_ngram.append(clean_w)
            clean_list_ngrams.append((' ').join(clean_ngram))
        return clean_list_ngrams

    df_cann_lines_index.ngrams = df_cann_lines_index.ngrams.apply(clean_index)

    raw_list_indexes = df_cann_lines_index.ngrams.tolist()

    return (raw_list_indexes, df_cann_lines_index)


def get_final_indexes(indexes_txt):
    cann_clean_indexes_nosep = []
    for item in indexes_txt:
        item = item.strip('\n')
        item = item.split(",")
        cann_clean_indexes_nosep.append(item)
    final_indexes = [
        (item, 1) for sublist in cann_clean_indexes_nosep for item in sublist if item != '']
    return dict((set(final_indexes)))


def add_is_in_index(candidates_df, indexes_list):
    dict_indexes = get_final_indexes(indexes_list)

    def add_target_col(x):
        if x in dict_indexes:
            return dict_indexes[x]
        else:
            return 0

    candidates_df['is_in_index'] = candidates_df.candidate_keyword.apply(
        add_target_col
    )

    return candidates_df


# 11. Aggregate lines with duplicated candidate_keyword

def aggregate_by_candidate(candidates_df):
    candidates_df=candidates_df.drop(
        columns=['clean_context', 'raw_context'], errors='ignore'
    )
    candidates_df=candidates_df.groupby(
        [
            'candidate_keyword',
            'length',
            'is_named_entity',
            'is_named_author',
            'is_in_toc',
            'freq',
            'is_in_index',
            'tfidf'
        ], as_index=False
    ).agg({'importance': np.mean, 'position_in_context': np.mean, 'POS':lambda x: scipy.stats.mode(x)[0]})
    return candidates_df
