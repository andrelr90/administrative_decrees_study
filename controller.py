import sqlite3
import pandas as pd
import numpy as np
import json

import nltk
import gensim
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('rslp')

import spacy
nlp = spacy.load('pt_core_news_sm')

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from string import punctuation

def load_senado_decrees(senado_files_dir, db_dir):
    base_dir = senado_files_dir
    years = [i for i in range(2000,2020)]
    dataframes = []
    for year in years:
        direct = base_dir+str(year)+".csv"
        dataframes.append(pd.read_csv(direct, sep=';'))

    dataframes = pd.concat(dataframes)
    dataframes
    categoria_serie = dataframes['categoria']

    i=0
    for row in categoria_serie:
        row = row.strip('[').strip(']').split(", ")
        row = [ro.strip('\'') for ro in row]
        dataframes.iat[i, 1] = row
        i+=1
    dataframes.set_index('Numero', inplace=True)

    conn = sqlite3.connect(db_dir)
    c = conn.cursor()
    c.execute("SELECT num_ato, ementa, full_text FROM Decretos")
    decretos = c.fetchall()
    numbers = np.zeros(len(decretos)).astype(int)
    for i in range(len(decretos)):
        numbers[i] = decretos[i][0].replace(".",'')

    decretos_aux = []
    for i in range(len(decretos)):
        c = []
        try:
            c = dataframes.loc[numbers[i]]['categoria']
        except:
            print(numbers[i], "is not classified by Senado.")
        d = [numbers[i], str(decretos[i][1]) + " " + str(decretos[i][2]), c]
        #d = [numbers[i], str(decretos[i][2]), c]    #full text only
        decretos_aux.append(d)

    conn.close()
    decretos = decretos_aux

    return decretos



def get_df_senado(decretos):
    decretos_df = pd.DataFrame(decretos)
    decretos_df.columns = ['numero ato', 'full_text', 'classificação senado']
    return decretos_df



def load_ministerio_decrees(db_dir):
    conn = sqlite3.connect(db_dir)
    c = conn.cursor()
    c.execute("SELECT cod_ident_ato, ementa, full_text, referenda FROM Decretos")
    decretos = c.fetchall()
    decretos = [(decreto[0], str(decreto[1]) + " " + str(decreto[2]), decreto[3]) for decreto in decretos]
    conn.close()
    for i in range(len(decretos)):
        referenda_aux = [ref.strip() for ref in decretos[i][2].split(";")]
        decretos[i] = list(decretos[i])
        decretos[i][2] = referenda_aux
        decretos[i] = tuple(decretos[i])
    return decretos



def get_df_ministerio(decretos):
    decretos_df = pd.DataFrame(decretos)
    decretos_df.columns = ['cod_ident_ato', 'full_text', 'referenda']
    return decretos_df



def get_classes(classes_file):
    classes=[]
    arq = open(classes_file, 'r', encoding='utf-8')
    line = arq.readline().rstrip('\n')
    count=0

    while line:
        if line == "$":
            classes.append([arq.readline().rstrip('\n')])
            line = arq.readline().rstrip('\n')
            while line != "$" and line:
                classes[count].append(line)
                line = arq.readline().rstrip('\n')
            count = count + 1
    arq.close()
    return classes



def multilabel_classify_decrees(decretos, classes):
    decretos_classify = []
    for decreto in decretos:
        referenda = decreto[2]
        category = []
        
        for ref in referenda:
            for i in range(len(classes)):
                if ref in classes[i] and i not in category:
                    category.append(i)
        
        if(category == []):
            category.append(len(classes))
        
        oh_category = []
        for i in range(len(classes) + 1):
            if i in category:
                oh_category.append(1)
            else:
                oh_category.append(0)
        dec = (decreto[0], decreto[1], oh_category)
        decretos_classify.append(dec)
    return decretos_classify    



def preprocess(text, counter, size=4519):
    print("preprocessing doc", counter, "/", size)
    result = ""
    commom_roman = ["i", "ii", "iii", "iv", "v", "vi", "vii", "viii", "ix", "x", "xi", "xii", "xiii", "xiv", "xv", "xvi", "xvii", "xviii", "xix", "xx"]
    stop_words = set(stopwords.words('portuguese') + list(punctuation) + commom_roman)
    
    trimmed =  False
    if(len(text.split(" ")) >= 10000):
        #decreto nº 6759 (counter 3423) era muito grande e travava
        print("decreto", counter, "é muito grande. Serão consideradas apenas as primeiras 10.000 palavras")
        text = " ".join(text.split(" ")[:10000])
        trimmed = True

    for token in nlp(text):
        token_text = token.text.lower()
        if(token_text not in stop_words and not str.isdigit(token_text) and token_text.isalpha()):
            result = result+" "+token.lemma_.lower()
    
    signature = len(result)
    if(result.rfind(" república") != -1):
        if not trimmed:
            signature = result.rfind(" república")
            if signature < len(result)/2:   #se remover a assinatura significar remover mais que metade do texto... para identificar casos em que a palavra república não encerra o documento.
                signature = len(result)     #não remove assinatura
                print("Signature kept.")
                print(result[0:signature])
    else:
        print("Signature not found using traditional methods.")
        print(result[0:signature])
    return result[0:signature]



def load_preprocess_from_cache(cache_file):
    f = open(cache_file)
    f.close()
    print(cache_file+" exists, loading data. Data loaded to variable.")
    
    with open(cache_file) as f:
        processed_docs = json.load(f)
    return processed_docs



def preprocess_docs(decretos_classify, cache_file):
    i=1
    processed_docs = []
    for decreto in decretos_classify:
        processed_docs.append(preprocess(decreto[1], i, len(decretos_classify)))
        i+=1
    
    with open(cache_file, 'w') as f:
        json.dump(processed_docs, f)
    return processed_docs



def print_itens_per_class(classes, labels):
    counters = np.zeros(len(classes)+1)
    for label in labels:
        for i in range(len(label)):
            if(label[i] == 1):
                counters[i]+=1
    print("Número de itens por classe:")
    retorno = []
    for i in range(len(classes)):
        retorno.append([classes[i][0], counters[i]])
        print(classes[i][0]+":"+str(counters[i]))
    print("Outras:"+str(int(counters[len(classes)])))
    return retorno


def get_class_weights(classes, labels):
    counters = np.zeros(len(classes)+1)
    for label in labels:
        for i in range(len(label)):
            if(label[i] == 1):
                counters[i]+=1
    greater_class = counters[np.argmax(counters)]
    weights = []
    for i in range(len(classes)):
        weights.append(greater_class/counters[i])
    weights.append(greater_class/counters[len(classes)])
    return weights



def remove_others_category(docs, labels, classes):
    labels_without_others = []
    docs_without_others = []
    for i in range(len(labels)):
        if labels[i][len(classes)] != 1:
            labels_without_others.append(labels[i])
            docs_without_others.append(docs[i])
    return docs_without_others, labels_without_others 



def remove_others_label(labels):
    filtered_labels = []
    for label in labels:
        label = label[:-1]
        filtered_labels.append(label)
    return filtered_labels



def remove_frequency_stopwords(stopwords_file, docs):
    words=pd.read_csv(stopwords_file, sep=';')
    words_list=words.values.tolist()
    
    list_stopwords=[]
    for stop_w in words_list:
        if stop_w[3]==1:
            list_stopwords.append(stop_w[0])

    words_filtered = []
    for doc in docs:
        aux_frequency = ""
        for word in doc.split(" "):
            if word not in list_stopwords:
                aux_frequency+=(word+" ")
        words_filtered.append(aux_frequency)
    return words_filtered

