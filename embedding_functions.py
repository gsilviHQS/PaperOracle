from openai.embeddings_utils import get_embedding, cosine_similarity
from transformers import GPT2TokenizerFast
import os
import numpy as np
import re

def texStripper(complete_text, title, abstract):
    complete_text2 = complete_text.split('\n')
    possible_keywords = ["\\title","\\author", "\\email", "\\thanks","\\affiliation","\\date","\\input"]
    temp_possible_keywords = possible_keywords.copy()
    #add \t to each possible_keywords
    for keyword in possible_keywords:
        temp_possible_keywords.append('\t'+keyword)
    possible_keywords = tuple(temp_possible_keywords)


    def content_in_pharentesis(first_division,complete_text,l):
        second_division = first_division.split('}')
        if len(second_division)==1:
            return second_division[0] + content_in_pharentesis(complete_text[l+1],complete_text,l+1)
        else:
            return second_division[0]

    def extract_begin_to_end(complete_text,l, endkeyword):
        #add lines from complete_text, starting from l+1 until you find a line starting with \end{

        # in case of begin and end in the same line
        if type(endkeyword) == str: 
            if endkeyword in complete_text[l]:
                return complete_text[l]


        if complete_text[l+1].startswith(endkeyword): #if the next line starts with the endkeyword
            return '' 
        elif complete_text[l+1].startswith('%'): #if the next line starts with a comment
            return extract_begin_to_end(complete_text,l+1,endkeyword)
        else:                                  #if the next line does not start with the endkeyword  or comment, add it to the text   
            return complete_text[l+1]+' '+extract_begin_to_end(complete_text,l+1,endkeyword)

    def loop_over(segments, opening, closing):
        if closing in segments[0]:
            return segments[0].split(closing)[0]
        else:
            return segments[0] +opening+ segments[1] + loop_over(segments[2:],opening, closing)


    text_sections = {}
    text_keys = {}
    # text_keys['plain text'] = []

    in_document = False
    in_section = False

    for l,line in enumerate(complete_text2): #loop over lines
            
        if line.startswith(possible_keywords):
                first_division = line.split('{')
                keyword = first_division[0].replace('\\','')
                content = content_in_pharentesis(first_division[1],complete_text2,l)
                if keyword not in text_keys.keys():
                    text_keys[keyword] = [content]
                else:
                    text_keys[keyword].append(content)
        
        elif line.startswith("\\begin{document"):
            in_document = True
            continue 

        elif line.startswith("\\end{document"):
            in_document = False
            in_section = False
            continue
    
        elif line.startswith("\\begin{") and in_document:
            first_division = line.split('{')
            second_division = first_division[1].split('}')
            keyword = second_division[0]
            
            content = extract_begin_to_end(complete_text2,l,'\\end{'+keyword)
            if keyword not in text_keys.keys():
                text_keys[keyword] = [content]
            else:
                text_keys[keyword].append(content)
        #print(r"{}".format(line))
        if line.startswith(("\\section","\\subsection","\t\\section","\t\\subsection","\\paragraph","\t\\paragraph")):
            in_section = True
            line = re.sub(r"\\label{(.*?)}", "", line)
            # print(line)
            if '}' not in line:
                #append the next line to the current line
                line = line + complete_text2[l+1]
            first_division = line.split('{')
            keyword = loop_over(segments=first_division[1:], opening='{', closing= '}' )
            keyword = r"{}".format(keyword)
            #get all the lines until the next \section or \subsection
            text_sections[keyword] = extract_begin_to_end(complete_text2,l,("\\section","\\subsection","\t\\section","\t\\subsection","\\paragraph","\t\\paragraph","\\begin{thebibliography}","\\end{document}"))
            

        if in_document and not line.startswith(("\\","\t","%"," "*2," "*3," "*4," "*5)):
            if line != '':
                # text_keys['plain text'].append(line) #may be useless
                if not in_section:
                    if '-' not in text_sections.keys():
                        text_sections['-'] = line
                    else:
                        text_sections['-'] +=' '+line

    # if '-' in text_sections.keys():
    #     text_sections['-'] = ' '.join(text_sections['-'])

    if 'title' not in text_keys.keys() and title is not None:
        text_keys['title'] = [title]
    if 'abstract' not in text_keys.keys()and abstract is not None:
        text_keys['abstract'] = [abstract]

    print('KEYS:',text_keys.keys())
    print('SECTIONS:',text_sections.keys())

    final_text = {}
    temp_list_phrases =[]
    final_text['sections'] = list(text_sections.keys())
    final_text['full'] = []
    final_text['tokens'] = 0
    # append general info
    
    for key in text_keys.keys():
        if key in ['title','abstract','author','email','thanks','affiliation','date']: #TODO include 'equation' 'theorem','proof','lemma'
            #append on top of the list,code: temp_list_phrases.insert(0,text_keys[key][0])
            print(key,text_keys[key])
            temp_list_phrases.append(key+": "+" ".join(text_keys[key]))
    
    # append sections
    print()
    for sec in text_sections.keys():
        #if sec !='-':
            print(sec)
            for phrase in text_sections[sec].split('. '): #split on .
                if phrase !='':
                    temp_list_phrases.append("["+sec+"]"+phrase)
    
    #looop over temp_list_phrases and check length of each phrase
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

    for phrase in temp_list_phrases:
        tokens = len(tokenizer.encode(phrase))
        if tokens>2000:
            phrase_split = phrase.split('.')
            print('Phrase too long:',phrase_split)
            if len(phrase_split)>1:
                for p in phrase_split:
                    final_text['full'].append(p)

        else:
            final_text['full'].append(phrase)
        final_text['tokens'] += tokens


    return final_text







def combine_similar_phrases(df): 
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    similarity_adj = []
    for i,phrase in df.iterrows():
        if i == 0:
            continue
        similarity_adj.append(cosine_similarity(phrase.similarity, df.iloc[i-1].similarity))

    overall_mean = np.mean(similarity_adj)
    # overall_std = np.std(similarity_adj)
    cases_to_drop = []
    for i,phrase in df.iterrows():
        if i == 0:
            continue
        if similarity_adj[i-1] > overall_mean:
            #combine two phrases and add to new dataframe
            new_phrase = df.loc[i-1].Phrase + '. ' + phrase.Phrase
            if len(tokenizer.encode(new_phrase))<2000:
                df.loc[i, "Phrase"] = new_phrase
                cases_to_drop.append(i-1)
    df.drop(cases_to_drop, inplace=True)
    df.reset_index(col_fill=0,inplace=True)
    df['n_tokens'] = df.Phrase.apply(lambda x: len(tokenizer.encode(x)))
    print('Max tokens',max(df.n_tokens))



# EMBEDDING FUNCTIONS


def compute_price_search_doc_embedding(tokens, embedding_model):
    if embedding_model == 'text-search-davinci-doc-001': #if the model is davinci
        dollars = tokens * (0.2/1000)
    elif embedding_model == 'text-search-curie-doc-001': #if the model is curie
        dollars = tokens * (0.02/1000)
    elif embedding_model == 'text-search-babbage-doc-001': #if the model is babbage
        dollars = tokens * (0.005/1000)
    elif embedding_model =='text-search-ada-doc-001': #if the model is ada
        dollars = tokens * (0.004/1000)
    else:
        dollars = 0
    return dollars

def compute_price_search_query_embedding(question, embedding_model):
    """
    Compute the price of a query given the embedding model
    and obtain the embedding of the query.
    """
    embedding_question = get_embedding(question, engine=embedding_model)
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
    tokens = len(tokenizer.encode(question))
    if embedding_model == 'text-search-davinci-query-001': #if the model is davinci
        dollars = tokens * (0.2/1000)
    elif embedding_model == 'text-search-curie-query-001': #if the model is curie
        dollars = tokens * (0.02/1000)
    elif embedding_model == 'text-search-babbage-query-001': #if the model is babbage
        dollars = tokens * (0.005/1000)
    elif embedding_model =='text-search-ada-query-001': #if the model is ada
        dollars = tokens * (0.004/1000)
    else:
        dollars = 0
    return embedding_question,tokens,dollars


def save_embedding(df,filename,std_folder,total_tokens=0, engine_sim = 'text-similarity-babbage-001', engine_search = 'text-search-babbage-doc-001', ):
    """
    Save the embedding of the phrases in a csv file
    """
    
    # complete_filename = std_folder+'/'+filename+'/'+engine_sim+'.csv'
    # print('Saving similarity embeddings to',complete_filename)
    # if not os.path.exists(complete_filename):

    #     df['similarity'] = df.Phrase.apply(lambda x: get_embedding(x, engine=engine_sim))
    #     df.to_csv(complete_filename) #first save the similarity alone
    # else:
    #     print('File:"'+complete_filename +'" already exists. To updated it erase the file and run again')
    
    complete_filename = std_folder+filename+'/'+engine_search+'.csv'
    print('Saving search embeddings to',complete_filename)

    if not os.path.exists(complete_filename):
        # combine_similar_phrases(df)
        df['search'] = df.Phrase.apply(lambda x: get_embedding(x, engine= engine_search))
        df.to_csv(complete_filename) #the savewith search embedding
    else:
        print('File:"'+complete_filename +'" already exists. To updated it erase the file and run again')

    return df
    




def connect_adjacents_phrases(df):
    """connect adjactent phrases in the dataframe"""
    df = df.sort_index(inplace=False) #inp
    list_of_indeces = df.index.to_list()
    print(list_of_indeces)
    # loop over the dataframe and connect the phrases
    for i in range(len(list_of_indeces)): # loop over the dataframe
        if i == 0: # if it is the first phrase
            continue
        else:
            index_here = list_of_indeces[i]
            index_before = list_of_indeces[i-1]
        if index_here == index_before+1:
            df.loc[index_here, "Phrase"] = df.loc[index_before].Phrase + '. ' + df.loc[index_here].Phrase
            # update here with query_doc_similarities from index_before
            df.loc[index_here, "query_doc_similarities"] = (df.loc[index_before].query_doc_similarities + df.loc[index_here].query_doc_similarities)/2
            df.loc[index_before, 'Phrase'] = ''
            #delete the row at index_before
            df.drop(index_before, inplace=True)
            # df.loc[i, 'Unnamed: 0'] = ''
        else:
            continue
    return df

def search_phrases(df, mean, std, how_many_std=2, pprint=False, connect_adj=True, minimum_one_phrase=True):
    """
    Search the phrases relevant for the question"""
    
    # Compute the similarity of the question with the phrases in the dataframe
    

    # mean = df.query_doc_similarities.mean()
    # std = df.query_doc_similarities.std()
    filter_to_use = mean + how_many_std*std #select the filter to use, which means keep the phrase with similarity greater than the filter
    # Filter the phrases with similarity greater than the filter
    newres = df[df.query_doc_similarities > filter_to_use]
    
    # if there are no phrases with similarity greater than the filter, return the phrase with the highest similarity
    if len(newres) == 0 and minimum_one_phrase:
        max_value = df.query_doc_similarities.max()
        newres = df[df.query_doc_similarities == max_value]


    if connect_adj and len(newres)>1:
        newres = connect_adjacents_phrases(newres)
    newres = newres.sort_values(by='query_doc_similarities', ascending=False)
    #newres = expand_knowledge(df, newres, embedding_question, 1, pprint=False)
    
    if pprint:
        print('Mean',mean,'1 std',mean+std,'2 std',mean+2*std ,'Filter similarity:', filter_to_use)
        # loop over Phrase and query_doc_similarities columns
        for i, row in newres.iterrows():
            print(row.Phrase, row.query_doc_similarities)
            print()
    return newres