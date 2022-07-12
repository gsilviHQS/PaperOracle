import itertools
import openai
# import wget
# import pathlib
import urllib.request
import tarfile
import os
import re
import requests
from bs4 import BeautifulSoup
from collections import Counter

MAX_LENGHT_PHRASE = 2000
MAX_PHRASES_TO_SEARCH = 200
MAX_PHRASES_TO_USE = 7
MAX_DISTANCE_BETWEEN_PHRASES = 3

BEST_ENGINE = "text-davinci-002"
MODERATE_ENGINE = "text-curie-001"
SIMPLE_ENGINE = "text-babbage-001"
WORST_ENGINE ="text-ada-001"

####################### arXiv related functions ##############################
def getTitleOfthePaper(paper_url):
    """Returns the title of the paper from the arxiv page """
    r = requests.get(paper_url)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("title").string
    return title

def getPaper(paper_url):
    """
    Downloads a paper from it's arxiv page, download the tar file, extract the tex file, and return the text
    Search also for tex in bibtex file
    """
    filename = paper_url.split(
        '/')[-1]  # get the last part of the url, i.e. the numbers
    filename = 'papers/' + filename
    if not os.path.exists(filename):  # if the directory doesn't exist
        os.mkdir(filename)  # create a directory
        # downloadedPaper = wget.download(paper_url, filename + '.pdf')  # download the paper pdf
        # downloadedPaperFilePath = pathlib.Path(downloadedPaper) # get the path to the downloaded file
        urllib.request.urlretrieve(paper_url.replace(
            'abs', 'e-print'), filename + ".tar.gz")  # download the tar file

        tar = tarfile.open(filename + ".tar.gz", "r:gz")  # open the tar file
        tar.extractall(path=filename)  # extract the tar file
        tar.close()  # close the tar file
        os.remove(filename + ".tar.gz")  # remove the tar file

    texfiles = []
    bibfiles = []
    for subdir, dirs, files in os.walk(filename):
        for file in files:
            if file.endswith(".tex"):
                texfilename = os.path.join(subdir, file)
                texfiles.append(texfilename)
            elif file.endswith(".bib") or file.endswith(".bbl"):
                bibfilename = os.path.join(subdir, file)
                bibfiles.append(bibfilename)
    return texfiles, bibfiles  # return the texfiles


####################### TEXT-related functions ##############################


def extract_all_text(texfiles):
    """ Extract all the text from the tex file """
    text = ''
    for texfile in texfiles:
        with open(texfile, 'r') as f:
            lines = f.readlines()
        for line in lines:
            text += line
    return text

def find_next(string, pos, list_of_substrings):
    """ Find the (min) next position of a list of substring in a string """
    list_of_positions = list(map(lambda x: string.find(x,pos+1), list_of_substrings))
    positive_positions = [pos for pos in list_of_positions if pos > 0] # remove -1, which means no match
    if len(positive_positions)==0:
        return None
    else:
        return min(positive_positions)


def find_prev(string, pos, list_of_substrings):
    """ Find the (max) previous position of a list of substring in a string """
    list_of_positions = list(map(lambda x: string.rfind(x, 0, pos), list_of_substrings))
    positive_positions = [pos for pos in list_of_positions if pos > 0] # remove -1, which means no match
    if len(positive_positions)==0:
        return None
    else:
        return max(positive_positions)

def get_sections(texfiles):
    """ Extract the sections and subsections from the tex file """
    sections = []
    for texfile in texfiles:
        with open(texfile, 'r') as f:
            lines = f.readlines()
        for line in lines:
            if line.startswith('\\begin{abstract}'):
                sections.append('abstract'+'\n')
            #TODO: improve matching parenthesis in nested cases
            if line.startswith('\\section{'):
                # extract the section name in between keywords \\section{ and }
                section = line.split('section{')[1].split('}')[0]
                sections.append(section+'\n')
            elif line.startswith('\\section*{'):
                # extract the section name in between keywords \\section*{ and }
                section = line.split('section*{')[1].split('}')[0]
                sections.append(section+'\n')
            elif line.startswith('\\subsection{'):
                # subsection = line.split('subsection{')[1].split('}')[0]
                subsection = line.split('subsection{')[1].split('}')[0]
                sections.append('\t'+subsection+'\n')
    return sections

def remove_duplicates(list_of_phrases, simplecase=False):
    """ Remove duplicates from a list """
    seen = set()
    clean_list_of_phrases = []
    if simplecase:
        for item in list_of_phrases:
            if item not in seen:
                seen.add(item)
                clean_list_of_phrases.append(item)
    else:
        for item,start,end in list_of_phrases:
            if item not in seen:
                seen.add(item)
                clean_list_of_phrases.append((item,start,end))
    return clean_list_of_phrases


def extract_phrases(keyword, text, api_key, number_of_phrases):
    """ Extract the phrases that match the keyword from the text """
    max_number_of_phrases = MAX_PHRASES_TO_SEARCH
    max_lenght_phrases = MAX_LENGHT_PHRASE
    searchstart = True
    if '\\'in keyword:
        print(keyword)
        keyword = keyword.replace('\\', '\\\\')
        print(keyword)

    if len([m.start() for m in re.finditer(r"\\" + keyword, text)]) > 0:  # if the keyword of type \keyword
        print('keyword of latex-type \\' + keyword)
        positions = [m.start() for m in re.finditer(r"\\" + keyword, text)]
        # delimiter_start = '\n'
        searchstart = False
        delimiter_end = ['}'] 
    elif len([m.start() for m in re.finditer(r"\\begin{" + keyword, text)]) > 0:  # if the keyword of type \begin{keyword}
        print('keyword of latex-type \\begin{' + keyword + '}')
        positions = [m.start()
                     for m in re.finditer(r"\\begin{" + keyword, text)]
        searchstart = False
        delimiter_end = ['end{' + keyword + '}']
    elif len([m.start() for m in re.finditer(r"section{" + keyword, text)]) > 0:  # if the keyword of type \section{keyword} TODO: merge with one below
        print('keyword of latex-type \\section{' + keyword + '}')
        positions = [m.start()+5 # 5 is the length of 'ection', +1 later on
                     for m in re.finditer(r"section{" + keyword, text)]
        searchstart = False
        delimiter_end = ['\\section','\\subsection'] 
        max_lenght_phrases = 12000  # exception for the section keyword
        max_number_of_phrases = 1 # exception for the section keyword
    elif len([m.start() for m in re.finditer(r"section\*{" + keyword, text)]) > 0:  # if the keyword of type \section{keyword} 
        print('keyword of latex-type \\section{' + keyword + '}')
        positions = [m.start()+6 # 5 is the length of 'ection', +1 later on
                     for m in re.finditer(r"section\*{" + keyword, text)]
        searchstart = False
        delimiter_end = ['\\section','\\subsection'] 
        max_lenght_phrases = 12000  # exception for the section keyword
        max_number_of_phrases = 1 # exception for the section keyword
    else:
        print('normal type keyword:' + keyword)
        #positions = [m.start() for m in re.finditer(r'\b' + keyword, text)] #to have  space ahead of the keyword
        positions = [m.start() for m in re.finditer(keyword, text)]
        delimiter_start = ['. ','\n']
        delimiter_end = ['. ','.\n']

    print("Positions found:", positions)
    stop_signal = False
    phrases = []
    for position in positions:
        start = position
        if searchstart:
            start = find_prev(text, position, delimiter_start)
        if start is None:
            continue
        end = find_next(text, position, delimiter_end)
        if end is None:
            continue
        sentence = text[start + 1:end + 1].replace('\n', ' ')
        keyword_filter = ['%' , 'bibname'] # keywords that should not be included in the phrases
        if searchstart and  any(x in sentence for x in keyword_filter) : continue

        # TODO: find a smarter way to do this below
        if len(sentence) >= max_lenght_phrases:
            print('A sentence is too long, lenght=', len(sentence))
        elif number_of_phrases >= max_number_of_phrases:
            stop_signal = True
            print('Enought sentences added:', len(phrases),' out of  ',len(positions),' sentences found')
            return phrases, stop_signal, number_of_phrases
        else:
            phrases.append((sentence, start, end))
            number_of_phrases += 1
            
    phrases = remove_duplicates(phrases)  # remove duplicate phrases from the list
 
    return phrases, stop_signal, number_of_phrases  # return the phrases and the stop signal triggered by the number of phrases

def connect_adjacent_phrases(list_of_phrases):
    """ Connect the adjacent phrases """
    # sort the phrases by start position x[1]
    list_of_phrases = sorted(list_of_phrases, key=lambda x: x[1])
    # connect the phrases
    new_phrases = []
    for i in range(len(list_of_phrases)):
        if i == 0:
            new_phrases.append(list_of_phrases[i])
        else:
            if abs(list_of_phrases[i][1] - list_of_phrases[i-1][2]) <= MAX_DISTANCE_BETWEEN_PHRASES:
                new_phrases[-1] = (new_phrases[-1][0] + ' ' + list_of_phrases[i][0], new_phrases[-1][1], list_of_phrases[i][2])
                new_phrases.append(new_phrases[-1]) #TODO: in case we connect more than 2 phrases this will undercount the number of phrases
            else:
                new_phrases.append(list_of_phrases[i])
    return [ele[0] for ele in new_phrases] # remove info about positions

def most_common_phrases(list_of_phrases, use_more_phrase=False):
    """ Order the phrases by most common """
    if use_more_phrase:
        max_phrases =MAX_PHRASES_TO_SEARCH
    else:
        max_phrases = MAX_PHRASES_TO_USE
    most_common_phrases = Counter(list_of_phrases).most_common(max_phrases)  # order phrases by most common, and limit to MAX_PHRASES_TO_USE
    return most_common_phrases

def get_hyperlink(phrases, full_text):
    """Find arxiv hyperlinks in the Bibitem"""
    newphrases = []
    all_hyperlinks = []
    for phrase in phrases:
        citations = list(itertools.chain(*[ele.split(',') for ele in re.findall(pattern=r'\\cite{(.*?)}', string=phrase)])) # list of citations inside \cite{} for a give phrase
        #print("citations:", citations)
        for cit in citations:
            hyperlink = link_patter_finder(cit, full_text) # find the arXiv hyperlink for a given citation
            if hyperlink is not None:
                all_hyperlinks.append(hyperlink)
                phrase = phrase.replace(cit, hyperlink)
        newphrases.append(phrase)
    return newphrases, all_hyperlinks

def link_patter_finder(cit, text):
    """Find the bibitem pattern for the citation"""
    raw_text = r"{}".format(text)
    # List of possible bibitem patterns, this may need to be updated if the bibitem is not in the text
    patterns = [('\]\{'+cit+'\}(.*?)BibitemShut', re.DOTALL,'{https://arxiv.org/abs/(.*?)}'),
                ('\]\{'+cit+'\}(.*?)BibitemShut', re.DOTALL,'{http://arxiv.org/abs/(.*?)}'),
                ('bibitem\{'+cit+'\}(.*)', 0, 'arXiv:(....\......)'),
                ]
    hyperlink = None
    # Loop over the patterns and find the bibitem pattern, once it is found, return the hyperlink
    for pattern in patterns:
        res = re.search(pattern[0], raw_text, flags=pattern[1])
        if res is not None:
            # print('Match:',res.group(),res.group(1))
            link = re.search(pattern[2], res.group(1), flags=pattern[1])
            if link is not None:
                print('Link',link.group(1))
                hyperlink = 'https://arxiv.org/abs/'+link.group(1)
                break
    return hyperlink
    
    
####################### GPT-3 functions #######################


def promptText_keywords(question, api_key):
    """ Prompt the question to gpt and return the keywords """
    preshot = "Question 1: What is the aim of the VQE?\nKeywords from question 1: \n Keywords:VQE, aim, purpose.\n\n"
    preshot += "Question 2: What is a local Hamiltonian? Give an example. \nKeywords from question 2: \n Keywords: local, Hamiltonian, example.\n\n"
    preshot += "Question 2: What is a qubit? \nKeywords from question 2: \n Keywords: qubit.\n\n"
    keywords_tag = "\nKeywords from the question 3:\n Keywords:"
    prompt = preshot + "Question:"+ question + keywords_tag
    #prompt = "Question 3:"+ question + keywords_tag
    # openai.organization = 'Default'
    openai.api_key = api_key
    # engine_list = openai.Engine.list() # calling the engines available from the openai api
    print('INPUT:\n', prompt)
    response = openai.Completion.create(
        engine=SIMPLE_ENGINE,
        prompt=prompt,
        temperature=0,
        max_tokens=340,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n","."]
    )
    print('\nOUTPUT:', response['choices'][0]['text'])
    return response['choices'][0]['text'], response['usage']['total_tokens'], response['model']


def promptText_question(question, inputtext, header, api_key):
    inputtext =  '-'+'\n-'.join(inputtext)
    openai.api_key = api_key
    # if the question doesn't end with a question mark, then is likely a command, add a period
    if question[:-1] != '?':
        question += '.'
    # PROMPT HERE
    prompt = header +\
        "\n\n Phrases:\n" +\
        inputtext +\
        "\n\n Prompt:From the Phrases above, provide a detailed answer to the question: " +\
        question + "\n If you are not sure say 'I am not sure but I think' and then try to answer:'\n"

    print('INPUT:\n', prompt)
    response = openai.Completion.create(
        engine=BEST_ENGINE,
        prompt=prompt,
        temperature=0.1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        # stop=["\n"]
    )
    print('\nOUTPUT:', response['choices'][0]['text'])
    return response

def promptText_question2(question, inputtext, header, api_key):

    openai.api_key = api_key
    print('INPUT:\n', inputtext,question)
    response = openai.Answer.create(
        model=BEST_ENGINE,
        search_model = "ada",
        documents = inputtext,
        question=question,
        temperature=0.1,
        max_tokens=1000,
        max_rerank=MAX_PHRASES_TO_USE,
        examples_context = "In 2017, U.S. life expectancy was 78.6 years.",
        examples = [["What is human life expectancy in the United States?","78 years."]],
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0,
        # stop=["\n"]
    )
    print('\nOUTPUT:', response['answers'])
    print(response)
    print([(doc["score"],doc["text"]) for doc in response["selected_documents"]])
    return response










####################### OBSOLETE FUNCTIONS #######################


def promptText_relevance(question, phrase, api_key):
    """ Prompt the question to gpt and return the keywords """

    header = "Question: : " + question + "\n"
    body = "Possible answer:" + phrase + "\n"
    prompt = header + body + "Is the Possible answer relevant to the Question? Yes or No:"
    # openai.organization = 'Default'
    openai.api_key = api_key
    # engine_list = openai.Engine.list() # calling the engines available from the openai api
    print('INPUT:\n', prompt)
    response = openai.Completion.create(
        engine=BEST_ENGINE,
        prompt=prompt,
        temperature=0,
        max_tokens=3,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        # stop=["\n"]
    )
    print('\nOUTPUT:', response['choices'][0]['text'])
    return response['choices'][0]['text'], response['usage']['total_tokens'], response['model']

def promptcleanLatex(phrases, api_key):
    """ Loop over phrases and prompt them to gpt to remove \cite() """
    clean_phrases = []
    openai.api_key = api_key
    for phrase in phrases:
        if "\cite" in phrase:
            response = openai.Completion.create(
                model="text-babbage-001",
                prompt="Remove latex citations, e.g. \\cite:\nInput: We use the VQE algorithm with the unitary coupled-clusters (UCC) ansatz~\\cite{Bartlett:1989, Taube:2006, Peruzzo:2014, OMalley:2016,   Hempel:2018} to find the ground state in the active space reduced to two qubits.\n\n \
                Output:  We use the VQE algorithm with the unitary coupled-clusters (UCC) ansatz~ to find the ground state in the active space reduced to two qubits.\n\nInput:  \n"+phrase + " \n\nOutput:  \n",
                temperature=0.0,
                max_tokens=1048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            phrase = response['choices'][0]['text']
        clean_phrases.append(phrase)
    return clean_phrases, response['usage']['total_tokens']
