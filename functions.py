import openai
import wget
import pathlib
import urllib.request
import tarfile
import os
import re



def getPaper(paper_url):
    """
    Downloads a paper from it's arxiv page and returns
    the filename
    """
    filename= paper_url.split('/')[-1] # get the filename from the url
    if not os.path.exists('papers'):
        os.makedirs('papers')
    filename = 'papers/' + filename
    if not os.path.exists(filename): # if the tar file doesn't exist
        os.mkdir(filename) # create a directory for the tar file
        downloadedPaper = wget.download(paper_url, filename+'.pdf') # download the paper   
        downloadedPaperFilePath = pathlib.Path(downloadedPaper) # get the path to the downloaded file
        urllib.request.urlretrieve(paper_url.replace('abs','e-print'),filename+".tar.gz") # download the tar file
   
        tar = tarfile.open(filename+".tar.gz", "r:gz") # open the tar file
        tar.extractall(path=filename) # extract the tar file
        tar.close() # close the tar file

    for file in os.listdir(filename):
        if file.endswith(".tex"):
            texfilename = os.path.join(filename, file)
            print(texfilename)
    return texfilename # return the texfile name

def get_sections(texfile):
    with open(texfile, 'r') as f:
        lines = f.readlines()
    sections = []
    for line in lines:
        if line.startswith('\\section{'):
            sections.append(line)
        elif line.startswith('\\subsection{'):
            sections.append(line)
            #sections.append(line.strip('\\section{').split("}", 1)[0])
    return sections

def extract_section_and_subsections(keywords, texfile):
    texfile = open(texfile).read()
    extracted_text = []
    for i in range(len(keywords)-1):
        start = texfile.find(keywords[i])+len(keywords[i]) #add len so that the index start after the code
        end = texfile.find(keywords[i+1])
        extracted_text.append(texfile[start:end])
    return extracted_text

def extract_all_text(texfile):
    with open(texfile, 'r') as f:
        lines = f.readlines()
    text = ''
    for line in lines:#
        text += line
        
    return text

def find_next(s, pos, c): # Find next occurrence of c after pos 
    i = s.find(c, pos+1) 
    if i == -1: return None 
    return i 
def find_prev(s, pos, c): # Find previous occurrence of c before pos 
    i = s.rfind(c, 0, pos) 
    if i == -1: return None 
    return i

def extract_phrases(keyword,text): 
    """ Extract the phrases that match the keyword from the text """
    #position = text.find(keyword.lower())
    positions = [m.start() for m in re.finditer(keyword, text)]
    #print("Position:",positions)
    start = 0
    end = 0
    phrases = []
    for position in positions:
        start = find_prev(text, position, '.')
        if start is None:
            return
        end = find_next(text, position, '.')
        if end is None:
            return
        
        phrases.append(text[start + 1:end].replace('\n', ' '))

    return phrases
    

def promptText_keywords(question, api_key):
    
    keywords_tag = "Extract keywords from this question:\n\n "
    #keywords_tag = "Extract keywords  and synonims of keywords from this question :\n\n "
    prompt = keywords_tag + question
    #openai.organization = 'Default'
    openai.api_key = api_key
    engine_list = openai.Engine.list() # calling the engines available from the openai api 
    print('INPUT:\n',prompt)
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0,
        max_tokens=340,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        #stop=["\n"]
    )
    print('\nOUTPUT:',response['choices'][0]['text'])
    return response['choices'][0]['text']

def promptText_question(question,inputtext, api_key):
    
    openai.api_key = api_key
    prompt = "Text:\n"+inputtext+ "\n\n Prompt:In the text above, " + question
    print('INPUT:\n',prompt)
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        temperature=0,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        #stop=["\n"]
    )
    print('\nOUTPUT:',response['choices'][0]['text'])
    return response