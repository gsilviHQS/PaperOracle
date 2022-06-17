import openai
# import wget
# import pathlib
import urllib.request
import tarfile
import os
import re
import requests
from bs4 import BeautifulSoup


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


def extract_phrases(keyword, text, api_key):
    """ Extract the phrases that match the keyword from the text """

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
        delimiter_start = '\n'
        delimiter_end = '\end{' + keyword + '}'
    else:
        print('normal type keyword')
        positions = [m.start() for m in re.finditer(r'\b' + keyword, text)]
        delimiter_start = '.'
        delimiter_end = '.'

    print("Positions found:", positions)
    phrases = []
    for position in positions:
        start = find_prev(text, position, delimiter_start)
        if start is None:
            return
        end = find_next(text, position, delimiter_end)
        if end is None:
            return
        sentence = text[start + 1:end].replace('\n', ' ')
        if len(sentence) < 1000:  # TODO: decide on max length of sentence
            phrases.append(sentence)
    phrases = list(set(phrases))  # set remove duplicate phrases from the list
    # clean the phrases from \cite
    phrases = promptcleanLatex(phrases, api_key)
    return phrases


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


def promptText_keywords(question, api_key):
    """ Prompt the question to gpt and return the keywords """

    # keywords_tag = "Extract keywords from this phrase:\n\n "
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
        "\n\n Text:\n" +\
        inputtext +\
        "\n\n Prompt:In the text above, " +\
        question + " If you are not sure about the answer say 'I am not sure but I think' and then try to answer:'\n"

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
