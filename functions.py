from lib2to3.pgen2 import token
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
MAX_NUMBER_OF_PHRASES = 100
PHRASES_TO_USE = 10


def remove_duplicates(list_of_phrases):
    """ Remove duplicates from a list """
    seen = set()
    clean_list_of_phrases = []
    for item in list_of_phrases:
        if item not in seen:
            seen.add(item)
            clean_list_of_phrases.append(item)
    return clean_list_of_phrases


def getTitleOfthePaper(paper_url):
    """ 
    Returns the title of the paper from the arxiv page """
    r = requests.get(paper_url)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("title").string
    return title


def getPaper(paper_url):
    """
    Downloads a paper from it's arxiv page and returns
    the filename
    """
    filename = paper_url.split(
        '/')[-1]  # get the last part of the url, i.e. the numbers
    if not os.path.exists('papers'):
        os.makedirs('papers')
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

    texfiles = []
    for subdir, dirs, files in os.walk(filename):
        for file in files:
            if file.endswith(".tex"):
                texfilename = os.path.join(subdir, file)
                texfiles.append(texfilename)
                print('Tex file found:', texfilename)
    # TODO: handle multiple tex files
    return texfiles  # return the texfiles


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



# def find_next(s, pos, c):
#     i = s.find(c, pos + 1)  # find the next occurrence of c after pos
#     if i == -1:
#         return None
#     return i


# def find_prev(s, pos, c):
#     i = s.rfind(c, 0, pos)  # find the previous occurrence of c before pos
#     if i == -1:
#         return None
#     return i


def extract_phrases(keyword, text, api_key, number_of_phrases):
    """ Extract the phrases that match the keyword from the text """
    max_number_of_phrases = MAX_NUMBER_OF_PHRASES
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
    elif len([m.start() for m in re.finditer(r"\\section{" + keyword, text)]) > 0:  # if the keyword of type \section{keyword}
        print('keyword of latex-type \\section{' + keyword + '}')
        positions = [m.start()
                     for m in re.finditer(r"\\section{" + keyword, text)]
        searchstart = False
        delimiter_end = '\\section' # or '\\subsection'
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
        sentence = text[start + 1:end].replace('\n', ' ')
        keyword_filter = ['section','%' , 'bibname'] # keywords that should not be included in the phrases
        if searchstart and  any(x in sentence for x in keyword_filter) : continue

        # TODO: find a smarter way to do this below
        if len(sentence) >= max_lenght_phrases:
            print('A sentence is too long:', sentence)
        elif number_of_phrases >= max_number_of_phrases:
            stop_signal = True
            print('Enought sentences added:', len(phrases),' out of  ',len(positions),' sentences found')
            return phrases, stop_signal, number_of_phrases
        else:
            phrases.append(sentence)
            number_of_phrases += 1
            
    phrases = remove_duplicates(phrases)  # remove duplicate phrases from the list
    # clean the phrases from \cite
    #phrases = promptcleanLatex(phrases, api_key)
 
    return phrases, stop_signal, number_of_phrases  # return the phrases and the stop signal triggered by the number of phrases

def check_relevance(list_of_phrases, question, api_key, askGPT=True):
    """ Check the relevance of the phrases to the question """
    seen = set()
    clean_list_of_phrases = []
    phrases_with_relevance = []
    # for item in list_of_phrases:
    #         if item not in seen:
    #             if 'bibname' not in item:
    #                 seen.add(item)
    #                 clean_list_of_phrases.append(item)
    #         else:
    #             clean_list_of_phrases.remove(item)
    #             clean_list_of_phrases.insert(0, item)
    clean_list_of_phrases = Counter(list_of_phrases).most_common()  # order phrases by most common
    total_tokens = 0
    model = None
    for phrase in clean_list_of_phrases[0:PHRASES_TO_USE]:
        if askGPT:
            result, tokens, model = promptText_relevance(question, phrase[0], api_key)
            total_tokens += tokens
            if 'Yes' in result:
                phrases_with_relevance.append(phrase)
        else:
            phrases_with_relevance.append(phrase)
    return phrases_with_relevance, total_tokens, model

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
        engine="text-davinci-002",
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


def promptText_keywords(question, api_key):
    """ Prompt the question to gpt and return the keywords """
    preshot = "Question:What is the aim of the VQE?\n\nExtract keywords from the question: \n aim, VQE \n\n"

    
    keywords_tag = "\n\nExtract many keywords from the question:\n\n Keywords:"
    # prompt = preshot + "Question:"+ question + keywords_tag
    prompt = "Question:"+ question + keywords_tag
    # openai.organization = 'Default'
    openai.api_key = api_key
    # engine_list = openai.Engine.list() # calling the engines available from the openai api
    print('INPUT:\n', prompt)
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0,
        max_tokens=340,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n", "."]
    )
    print('\nOUTPUT:', response['choices'][0]['text'])
    return response['choices'][0]['text'], response['usage']['total_tokens'], response['model']


def promptText_question(question, inputtext, header, api_key):

    openai.api_key = api_key
    # if the question doesn't end with a question mark, then is likely a command, add a period
    if question[:-1] != '?':
        question += '.'
    # PROMPT HERE
    prompt = header +\
        "\n\n Phrases:\n" +\
        inputtext +\
        "\n\n Prompt:From the Phrases above, give an answer to the question: " +\
        question + "\n If you are not sure say 'I am not sure but I think' and then try to answer:'\n"

    print('INPUT:\n', prompt)
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0.1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        # stop=["\n"]
    )
    print('\nOUTPUT:', response['choices'][0]['text'])
    return response['choices'][0]['text'] , response['usage']['total_tokens'], response['model']

# OBSOLETE FUNCTIONS


def get_sections(texfile):
    """ Extract the sections from the tex file """
    with open(texfile, 'r') as f:
        lines = f.readlines()
    sections = []
    for line in lines:
        if line.startswith('\\section{'):
            sections.append(line)
        elif line.startswith('\\subsection{'):
            sections.append(line)
            # sections.append(line.strip('\\section{').split("}", 1)[0])
    return sections


def extract_section_and_subsections(keywords, texfile):
    """ Extract the sections and subsections from the tex file """
    texfile = open(texfile).read()
    extracted_text = []
    for i in range(len(keywords) - 1):
        # add len so that the index start after the code
        start = texfile.find(keywords[i]) + len(keywords[i])
        end = texfile.find(keywords[i + 1])
        extracted_text.append(texfile[start:end])
    return extracted_text



#UTILITIES for INTERFACE

def custom_paste(event):
        try:
            event.widget.delete("sel.first", "sel.last")
        except:
            pass
        event.widget.insert("insert", event.widget.clipboard_get())
        return "break"