import openai
# import wget
# import pathlib
import urllib.request
import tarfile
import os
import re
import requests
from bs4 import BeautifulSoup

MAX_LENGHT_PHRASE = 2000
MAX_NUMBER_OF_PHRASES = 10


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
    """ Extract the text from the tex file """
    text = ''
    for texfile in texfiles:
        with open(texfile, 'r') as f:
            lines = f.readlines()

        for line in lines:
            text += line
    return text


def find_next(s, pos, c):
    i = s.find(c, pos + 1)  # find the next occurrence of c after pos
    if i == -1:
        return None
    return i


def find_prev(s, pos, c):
    i = s.rfind(c, 0, pos)  # find the previous occurrence of c before pos
    if i == -1:
        return None
    return i


def extract_phrases(keyword, text, api_key, number_of_phrases):
    """ Extract the phrases that match the keyword from the text """
    searchstart = True
    if len([m.start() for m in re.finditer(r"\\" + keyword, text)]) > 0:  # if the keyword of type \keyword
        positions = [m.start() for m in re.finditer(r"\\" + keyword, text)]
        print('keyword of latex-type \\' + keyword)
        delimiter_start = '\n'
        delimiter_end = '}'
    # if the keyword of type \begin{keyword}
    elif len([m.start() for m in re.finditer(r"\\begin{" + keyword, text)]) > 0:
        positions = [m.start()
                     for m in re.finditer(r"\\begin{" + keyword, text)]
        print('keyword of latex-type \\begin{' + keyword + '}')
        searchstart = False
        delimiter_end = 'end{' + keyword + '}'
    else:
        print('normal type keyword:' + keyword)
        #positions = [m.start() for m in re.finditer(r'\b' + keyword, text)] #to have  space ahead of the keyword
        positions = [m.start() for m in re.finditer(keyword, text)]
        delimiter_start = '.'
        delimiter_end = '.'

    print("Positions found:", positions)
    stop_signal = False
    phrases = []
    for position in positions:
        if searchstart:
            start = find_prev(text, position, delimiter_start)
        else:
            start = position
        if start is None:
            continue
        end = find_next(text, position, delimiter_end)
        if end is None:
            continue
        sentence = text[start + 1:end].replace('\n', ' ')

        # TODO: find a smarter way to do this below
        if len(sentence) >= MAX_LENGHT_PHRASE:
            print('A sentence is too long:', sentence)
        elif number_of_phrases >= MAX_NUMBER_OF_PHRASES:
            stop_signal = True
            print('Enought sentences added:', len(phrases),' out of  ',len(positions),' sentences found')
            return phrases, stop_signal
        else:
            phrases.append(sentence)
            number_of_phrases += 1
            
    phrases = remove_duplicates(phrases)  # set remove duplicate phrases from the list
    # clean the phrases from \cite
    #phrases = promptcleanLatex(phrases, api_key)
 
    return phrases, stop_signal  # return the phrases and the stop signal triggered by the number of phrases


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
    return clean_phrases


def promptText_keywords(question, api_key, synonyms=False):
    """ Prompt the question to gpt and return the keywords """
    if synonyms is False:
        keywords_tag = "Extract keywords from this phrase:\n\n "
    else:
        keywords_tag = "Extract keywords and their synonims from this phrase :\n\n "
    prompt = keywords_tag + question
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
        # stop=["\n"]
    )
    print('\nOUTPUT:', response['choices'][0]['text'])
    return response['choices'][0]['text']


def promptText_question(question, inputtext, header, api_key):

    openai.api_key = api_key
    # if the question doesn't end with a question mark, then is likely a command, add a period
    if question[:-1] != '?':
        question += '.'
    # PROMPT HERE
    prompt = header +\
        "\n\n Phrases:\n" +\
        inputtext +\
        "\n\n Prompt:From the phrase above, give an answer to the question," +\
        question + "\n If you are not sure about the answer say 'I am not sure but I think' and then try to answer:'\n"

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
    return response

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
