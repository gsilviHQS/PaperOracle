from openai.embeddings_utils import get_embedding, cosine_similarity
from transformers import GPT2TokenizerFast
import os
import numpy as np

def texStripper(complete_text):
    complete_text2 = complete_text.split('\n')
    possible_keywords = ["\\title", "\\author", "\\email", "\\thanks","\\affiliation","\\date","\\input"]
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

    def extract_begin_to_end(complete_text,l, keyword):
        #add lines from complete_text, starting from l+1 until you find a line starting with \end{
        #code:
        if complete_text[l+1].startswith(keyword):
            return ''
        elif complete_text[l+1].startswith('%'):
            return extract_begin_to_end(complete_text,l+1,keyword)
        else:
            return complete_text[l+1]+extract_begin_to_end(complete_text,l+1,keyword)

    def loop_over(segments, opening, closing):
        if closing in segments[0]:
            return segments[0].split(closing)[0]
        else:
            return segments[0] +opening+ segments[1] + loop_over(segments[2:],opening, closing)


    text_sections = {}
    text_sections['pre_section'] = []
    text_keys = {}
    text_keys['plain text'] = []
    in_document = False
    in_section = False

    for l,line in enumerate(complete_text2):
            
        
        if line.startswith(possible_keywords):
                first_division = line.split('{')
                keyword = first_division[0].replace('\\','')
                content = content_in_pharentesis(first_division[1],complete_text2,l)
                if keyword not in text_keys:
                    text_keys[keyword] = [content]
                else:
                    text_keys[keyword].append(content)
        elif line.startswith("\\begin{document"):
            continue # the continue keyword is used to skip the current iteration of the loop
        elif line.startswith("\\begin{"):
            in_document = True
            first_division = line.split('{')
            second_division = first_division[1].split('}')
            keyword = second_division[0]
            content = extract_begin_to_end(complete_text2,l,'\end{'+keyword)
            if keyword not in text_keys:
                text_keys[keyword] = [content]
            else:
                text_keys[keyword].append(content)
        #print(r"{}".format(line))
        if line.startswith(("\\section","\\subsection","\t\\section","\t\\subsection")):
            in_section = True
            sections_started = True
            # get the name and content of the section
            first_division = line.split('{')
            keyword = loop_over(segments=first_division[1:], opening='{', closing= '}' )
            #get all the lines until the next \section or \subsection
            content = extract_begin_to_end(complete_text2,l,("\\section","\\subsection","\\begin{thebibliography}","\\end{document}"))
            keyword = r"{}".format(keyword)
            text_sections[keyword] = content
            
        if line.startswith("\\end{document}"):
            in_document = False
            in_section = False

        if in_document and not line.startswith(("\\","\t","%"," "*2," "*3," "*4," "*5)):
            if line != '':
                text_keys['plain text'].append(line)
                if not in_section:
                    text_sections['pre_section'].append(line)

    text_sections['pre_section'] = '\n'.join(text_sections['pre_section'])
    print(text_sections.keys())

    final_text = {}
    final_text['sections'] = list(text_sections.keys())
    final_text['complete'] =[]
    final_text['full'] = []
    # append general info
    for key in text_keys:
        if key in ['title','author','email','thanks','affiliation']:
            #append on top of the list,code: final_text['complete'].insert(0,text_keys[key][0])
            final_text['complete'].append(key+": "+",".join(text_keys[key]))
    # append abstract (if exists)
    if 'abstract' in text_keys.keys():
        final_text['complete'].append('abstract: '+ " ".join(text_keys['abstract' ]))
    # append sections
    for sec in text_sections.keys():
        if sec !='pre_section':
            print(sec)
            for phrase in text_sections[sec].split('. '):
                if phrase !='':
                    final_text['complete'].append(phrase)
    
    #looop over fainal_text['complete'] and check length of each phrase
    tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

    for phrase in final_text['complete']:
        if len(tokenizer.encode(phrase))>2000:
            phrase = phrase.split('.')
            if len(phrase)>1:
                for p in phrase:
                    final_text['full'].append(p)

        else:
            final_text['full'].append(phrase)


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


def save_embedding(df,filename,std_folder, engine_sim = 'text-similarity-babbage-001', engine_search = 'text-search-babbage-doc-001'):
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
    
    complete_filename = std_folder+'/'+filename+'/'+engine_search+'.csv'
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
            df.loc[index_before, 'Phrase'] = ''
            #delete the row at index_before
            df.drop(index_before, inplace=True)
            # df.loc[i, 'Unnamed: 0'] = ''
        else:
            continue
    return df

def search_phrases(df, question, how_many_std=2, engine_search_query ='text-search-babbage-query-001' ,pprint=True, connect_adj=True):
    """
    Search the phrases relevant for the question"""
    embedding_question = get_embedding(question, engine=engine_search_query)
    df['query_doc_similarities'] = df.search.apply(lambda x: cosine_similarity(x, embedding_question))

    mean = df.query_doc_similarities.mean()
    std = df.query_doc_similarities.std()
    filter_to_use = mean + how_many_std*std #select the filter to use, which means keep the phrase with similarity greater than the filter
    # sort the dataframe by similarity, and keep all with similarity greater than the filter
    #TODO: switch the two lines below
    newres = df[df.query_doc_similarities > filter_to_use]
    newres = newres.sort_values(by='query_doc_similarities', ascending=False)
    
    # if there are no phrases with similarity greater than the filter, return the phrase with the highest similarity
    if len(newres) == 0:
        max_value = df.query_doc_similarities.max()
        newres = df[df.query_doc_similarities == max_value]
    print('Mean',mean,'1 std',mean+std,'2 std',mean+2*std ,'Filter similarity:', filter_to_use)
    #res = df.sort_values('query_doc_similarities', ascending=False).head(n)
    #call to function paused for now:
    if connect_adj and len(newres)>1:
        newres = connect_adjacents_phrases(newres)
    #newres = expand_knowledge(df, newres, embedding_question, 1, pprint=False)
    
    
    
    if pprint:
        # loop over Phrase and query_doc_similarities columns
        for i, row in newres.iterrows():
            print(row.Phrase, row.query_doc_similarities)
            print()
    return df,newres