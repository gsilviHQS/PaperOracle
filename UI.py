#! /usr/bin/env python
import tkinter as tk
import os

import sklearn.utils._typedefs
import sklearn.utils._heap
import sklearn.utils._sorting
import sklearn.utils._vector_sentinel
import sklearn.neighbors._partition_nodes
import PIL._tkinter_finder
import huggingface_hub.hf_api
import huggingface_hub.repository
#MY FUNCTIONS
import functions
import embedding_functions
from Tkinter_helper import CustomText, custom_paste, HyperlinkManager,Interlink,COLOR_LIST, RightClicker, WrappingCheckbutton
import sys
import pandas as pd
import numpy as np
import openai
import json
from openai.embeddings_utils import cosine_similarity

from PIL import Image, ImageOps
import io

import matplotlib.pyplot as plt
from matplotlib import rcParams
rcParams['text.usetex'] = True
rcParams['text.latex.preamble'] = r'\usepackage{amsfonts} \usepackage{amssymb} \usepackage{amsmath}'



# set the environment variable TOKENIZERS_PARALLELISM=true
os.environ['TOKENIZERS_PARALLELISM'] = 'true' 

sys.setrecursionlimit(10000)
MAX_PHRASES_TO_USE = 10
FOLDER_EMB = 'embeddings/'
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        #initialization
        self.last_question_and_answer = None
        self.final_text = None
        self.button4more = None
        self.dfs = [] #list of dataframes
        self.last_embeddings = []
        self.number_of_prompts = 0
        self.groups = {}
        self.img = []
        self.init_folders()
        self.create_widgets()
        self.init_defaults()
        self.check_embedding_in_folder() #check if there are embeddings in the folder
        
        
                                   

    def create_widgets(self):
        """
        Create the widgets for the GUI
        """
        # Variables
        self.dollars = tk.DoubleVar()
        self.dollars.set(0.0)
        
        self.token_usage = tk.IntVar()
        self.token_usage.set(0)
        
        self.token_label = tk.StringVar()
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')
        
        self.papertitle = tk.StringVar()
        self.papertitle.set('')


        # Column 0 widgets
        tk.Label(self.master, text="API Key").grid(row=0, column=0)
        self.apikey = tk.Entry(self.master, width=35)
        self.apikey.grid(row=1, column=0)
        self.apikey.bind('<Button-3>', RightClicker)
        if os.path.isfile('API.csv'):
            openai.api_key_path = "API.csv"
            with open('API.csv', 'r') as f:
                self.apikey.insert(0, f.read())
        else:
            self.apikey.insert(0, 'Your API Key here')
            # if apikey is selected by the user then cancel its content
            self.apikey.bind('<Button-1>', lambda event: self.apikey.delete(0, tk.END))
            tk.Button(self.master, text='Save API Key', command=self.save_api_key).grid(row=1, column=1, sticky=tk.W)

        tk.Label(self.master, text="arXiv URL").grid(row=2, column=0)
        self.url = tk.Entry(self.master, width=35)
        self.url.grid(row=3, column=0)
        self.url.bind('<Button-3>', RightClicker)
        
        
        tk.Label(self.master, textvariable=self.papertitle, wraplength=400).grid(row=5, column=0)
        
        
        self.textembedding = tk.Text(self.master, width=60, height=40, wrap=tk.WORD)
        self.vsb = tk.Scrollbar(self.master, orient="vertical")
        self.vsb.grid(row=6, column=0, sticky='nse')
        self.vsb.config(command=self.textembedding.yview)
        self.textembedding.grid(row=6, column=0, rowspan=2)
        self.textembedding['yscrollcommand'] = self.vsb.set
        

 

        # # section and subsection
        # self.sections = CustomText(self.master, wrap=tk.WORD, width=60, height=35)
        # self.sections.grid(row=6, column=0, rowspan=3)
        # self.sections.bind('<Button-3>', RightClicker)
        
        tk.Label(self.master, textvariable = self.token_label).grid(row=10, column=0 , sticky=tk.W)
        
        #Column 1 widgets

        # output box to display the result
        
        tk.Label(self.master, text="Answer from GPT-3").grid(row=3, column=1, columnspan=2)
        self.textbox = tk.Text(self.master, height=40, width=60, wrap='word')
        self.textbox.grid(row=4, column=1, columnspan=2, rowspan=3)
        self.textbox.bind('<Button-3>', RightClicker)
        self.textbox.insert(tk.END, "Output")
        self.textbox.config(state=tk.DISABLED,
                            background="white",
                            foreground="black",
                            font=("Helvetica", 11,'bold'),
                            borderwidth=2,
                            )
        self.vsb2 = tk.Scrollbar(self.master, orient="vertical")
        self.vsb2.grid(row=4, column=1, columnspan=2,rowspan=3, sticky='nse')
        self.vsb2.config(command=self.textbox.yview)
        self.textbox['yscrollcommand'] = self.vsb2.set

        tk.Label(self.master, text="Question").grid(row=9,column=1, columnspan=2)
        self.question = tk.Text(self.master, wrap=tk.WORD, width=70, height=3 , font=("Helvetica", 11))
        self.question.grid(row=10, column=1, columnspan=2)
        self.question.bind('<Button-3>', RightClicker)


        

        #Column 2 widgets
        # add a checkbox to select if the user want separate answer for each paper


        tk.Label(self.master, text="Standard deviation of phrases in TeX").grid(row=9, column=3)
        self.std_dev = tk.IntVar()
        self.std_dev.set(0)
        self.std_dev_slider = tk.Scale(self.master, from_=1, to=5, orient=tk.HORIZONTAL, variable=self.std_dev)
        self.std_dev_slider.grid(row=10, column=3)
        self.std_dev_slider.bind('<Button-3>', RightClicker)
        self.std_dev_slider.set(3)
        
        self.separate_answer = tk.IntVar()
        self.separate_answer.set(0)
        self.separate_answer_checkbox = tk.Checkbutton(self.master, text="Separate answer for each paper", variable=self.separate_answer)
        self.separate_answer_checkbox.grid(row=11, column=3)

        self.at_least_one_phrase = tk.IntVar()
        self.at_least_one_phrase.set(1)
        self.at_least_one_answer_checkbox = tk.Checkbutton(self.master, text="At least one phrase per paper", variable=self.at_least_one_phrase)
        self.at_least_one_answer_checkbox.grid(row=12, column=3)

          # new textbox for the phrases matching the question
        
        tk.Label(self.master, text="Phrases in Tex given to GPT").grid(row=4, column=3, columnspan=1)
        self.phraseinTex = CustomText(self.master, height=35, width=60, wrap='word')
        self.phraseinTex.grid(row=5, column=3, rowspan=3)
        self.phraseinTex.bind('<Button-3>', RightClicker)
        self.phraseinTex.insert(tk.END, "Phrases")
        self.phraseinTex.config(state=tk.DISABLED,
                             background="white",
                             foreground="black",
                             font=("Helvetica", 11),
                             borderwidth=2,
                             )
        self.vsb3 = tk.Scrollbar(self.master, orient="vertical")
        self.vsb3.grid(row=5, column=3, rowspan=3, sticky='nse')
        self.vsb3.config(command=self.phraseinTex.yview)
        self.phraseinTex['yscrollcommand'] = self.vsb3.set

        #


        

        #BUTTONS
        #button under url box named "Get paper"
        tk.Button(self.master, text='Get paper and create embedding', command=self.pre_confirm_paper).grid(row=4, column=0)


        tk.Button(self.master, text='Group papers', command=self.group_papers).grid(row=10, column=0, sticky=tk.E)    
        tk.Button(self.master, text='Reset usage', command=self.reset_token_usage).grid(row=11, column=0, sticky=tk.W)                     

        tk.Button(self.master, text='Run', command=self.run).grid(row=11,
                                                                  column=1,
                                                                  pady=4,
                                                                  sticky=tk.E)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=11,
                                                                    column=2,
                                                                    pady=4,
                                                                    sticky=tk.W)
        
    def group_papers(self):
        self.checked_list = self.get_checked_embedding()
        #TODO: finish this function
        # make a new popup window to group papers

        if len(self.checked_list ) == 0:
            return
        else:
            self.grouppapers = tk.Toplevel(self.master)
            self.grouppapers.geometry('400x200')
            # insert the title of the paper
            self.grouppapers.title('Group papers')
            # insert the abstract of the paper
            self.group_list = tk.Text(self.grouppapers, height=10, width=80)
            self.group_list.pack()
            # list the papers in group_list text, loop over the embedding_to_use
            for i in range(len(self.checked_list)):
                self.group_list.insert(tk.END, self.checked_list [i])
                self.group_list.insert(tk.END, '\n')
            # add a second textbox for the group name
            self.group_name = tk.Text(self.grouppapers, height=1, width=80)
            self.group_name.pack()
            # add a button to confirm the group
            tk.Button(self.grouppapers, text='Confirm', command=self.confirm_group).pack()
            # add a button to cancel the group
            tk.Button(self.grouppapers, text='Cancel', command=self.cancel_group).pack()
        
            
    def confirm_group(self):
        # get the group name from the textbox
        group_name = self.group_name.get('1.0', tk.END).strip('\n')
        # get the papers from the textbox
        # add the group to the groups list
        self.groups[group_name]= self.checked_list

        #  save the groups to a file
        with open('groups.svg', 'w') as f:
            f.write(json.dumps(self.groups))

        # close the group window
        self.grouppapers.destroy()
        self.check_embedding_in_folder()
        
        print(self.groups)

    def cancel_group(self):
        # close the group window
        self.grouppapers.destroy()


    
    def init_defaults(self):
        if os.path.isfile('default_url.csv'):
            with open('default_url.csv', 'r') as f:
                self.url.insert(tk.END, f.read())

        if os.path.isfile('default_question.csv'):
            with open('default_question.csv', 'r') as f:
                self.question.insert(tk.END, f.read())

        if os.path.isfile('groups.svg'):
            with open('groups.svg', 'r') as f:
                self.groups = json.loads(f.read())



    def init_folders(self):
        if not os.path.exists('papers'):
            os.makedirs('papers')
        if not os.path.exists('embeddings'):
            os.makedirs('embeddings')

        
    # def callback_to_url(self,*args):
    #     self.url.delete(0, tk.END)
    #     url_to_use = "http://arxiv.org/abs/"+self.default_paper.get()
    #     self.url.insert(0,url_to_use)
    #     self.get_paper()

    # def callback_to_embedding(self,*args):
    #     self.url.delete(0, tk.END)
    #     url_to_use = "http://arxiv.org/abs/"+self.default_embedding.get()
    #     self.url.insert(0,url_to_use)
    #     self.embedding_to_use = self.default_embedding.get()
    #     self.get_paper_and_embedding()

    # def check_papers_in_folder(self):
    #     self.folders = list(os.listdir('papers/'))

    def list_embeddings(self):
        self.checkbuttons = []
        type_of_embedding = ['text-search-ada-doc-001.csv','text-search-babbage-doc-001.csv','text-search-curie-doc-001.csv']
        self.embeddings = list(os.listdir(FOLDER_EMB))
        if len(self.embeddings) > 0:
            for model in type_of_embedding: # divide by model
                only_model = model.replace('.csv','')
                for emb in self.embeddings: #loop over complete list of embeddings
                    #embeddings in  each folder
                    emb_in_folder = list(os.listdir(FOLDER_EMB+emb))
                    # keep only .csv files
                    emb_in_folder = [x for x in emb_in_folder if x.endswith('.csv')]
                    # if there are none, then skip this embedding
                    if len(emb_in_folder) == 0:
                        continue
                    if model not in emb_in_folder:
                        continue
                    with open(FOLDER_EMB+emb+'/info.json', 'r') as f:
                        info = json.load(f)
                    j = tk.IntVar()
                    cb = WrappingCheckbutton(self.master, text=info, variable=j)
                    if emb+only_model in self.default_emb:
                        j.set(1)
                        #set the background color of the checkbox to green
                        cb.config(bg='light green')
                    self.checkbuttons.append((j,emb,cb,only_model))
    
    def check_embedding_in_folder(self):
        """
        Check if there are embeddings in the folder, and defaults used last time
        If so, then set the checkbox, already checked according to the default embeddings
        Create a list of checkboxes for the embeddings in the folder
        """
        
        # clear self.textembedding
        self.textembedding.delete(1.0, tk.END)
        self.default_emb = []
        if os.path.isfile('default_embeddings.csv'):
            with open('default_embeddings.csv', 'r') as f:
                # read all the lines in the file
                def_emb = f.readlines()
                # remove the newline character at the end of each line
                self.default_emb = [x.strip() for x in def_emb]
                print('default embeddings: ', def_emb)
        
        self.list_embeddings() #populate the checkbuttons list

                #list the self.groups if there are any
        buttons_already_used = []
        if len(self.groups)>0:
            self.textembedding.insert(tk.END, 'Groups: \n')
            for key in self.groups.keys():
                self.textembedding.insert(tk.END, key)
                self.textembedding.insert(tk.END, '\n')
                # list the values of the groups
                for id,mod in self.groups[key]:
                    print(id,mod, key)
                    for j,emb,cb,model in self.checkbuttons:
                        if id == emb and mod == model:
                            print('found')
                            self.textembedding.window_create("end", window=cb)
                            self.textembedding.insert("end", '\n') 
                            # remove the checkbox from the list of checkbuttons
                            buttons_already_used.append(cb)
                            break

        for general_models in ['text-search-ada-doc-001','text-search-babbage-doc-001','text-search-curie-doc-001']:
            self.textembedding.insert(tk.END,'\nMODEL:'+general_models+'\n')
            for j,emb,cb,model in self.checkbuttons:
                if cb in buttons_already_used:
                    continue
                if model == general_models:
                    self.textembedding.window_create("end", window=cb)
                    self.textembedding.insert("end", "\n") # to force one checkbox per line

    def reset_token_usage(self):
        """"
        Reset the token/cost usage to 0
        """
        self.token_usage.set(0)
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')
        self.dollars.set(0.0)

    def save_api_key(self):
        """
        Save the API key in a file
        """
        api_key = self.apikey.get()
        with open('API.csv', 'w') as f:
            f.write(api_key)
    
    def save_url(self):
        """
        Save the url in a file
        """
        url = self.url.get()
        with open('default_url.csv', 'w') as f:
            f.write(url)
    
    def save_question(self):
        """
        Save the question in a file
        """
        question = self.question.get("1.0", tk.END)
        with open('default_question.csv', 'w') as f:
            f.write(question)
    
    def save_to_history(self,question,answer):
        with open('history.json', 'a') as f:
            json.dump({'question':question,'answer':answer}, f)
            f.write('\n')

    def update_token_usage(self,tokens,dollars):
        """
        Update the token usage and dollars spent
        """
        total_token_used = self.token_usage.get() #get the current token usage
        total_dollars_used = self.dollars.get() #get the current dollars usage
        
        total_token_used += tokens #add the tokens used to the total token usage
        self.token_usage.set(total_token_used) #update the token usage


        total_dollars_used += dollars #add the dollars used to the total dollars usage
        self.dollars.set(total_dollars_used) #update the dollars usage

        self.token_label.set('Usage: '+str(total_token_used)+' tokens ('+'{:3.3f}'.format(total_dollars_used)+'$)'+\
                             '\n (Last: '+str(tokens)+ ' tokens ('+'{:3.3f}'.format(dollars)+'$)') #update the token usage label

    # def get_paper_and_embedding(self):
    #     self.get_paper()
    #     self.get_embedding()
        
    def get_checked_embedding(self):
        """
        Get the list of checked embedding from UI
        """
        list_of_embeddings = []
        for i,but,cb,model in self.checkbuttons:
            if i.get() == 1:
                list_of_embeddings.append((but,model))
                # turn the checkbox to green
                cb.config(bg='light green')
            else:
                # turn the checkbox to standard color
                cb.config(bg='light grey')
        # save the default embeddings to a file
        with open('default_embeddings.csv', 'w') as f:
            for emb,model in list_of_embeddings:
                f.write(emb+model+'\n')
        print("Embedding to use",list_of_embeddings)
        return list_of_embeddings

    def get_embedding(self, embedding_to_use, model='text-search-babbage-doc-001'):
        """
        Get the embedding from the folder
        """
        FOLDER_EMB = 'embeddings/'
        self.dfs = []
        self.all_texts = []
        self.all_bib = []
        self.all_info = []
        for emb,model in embedding_to_use:
            path = FOLDER_EMB+emb
            path += '/'+model+'.csv'
            df = pd.read_csv(path, index_col=0)
            # df['similarity'] = df.similarity.apply(eval).apply(np.array)
            df['search'] = df.search.apply(eval).apply(np.array)
            # append the df to the list of dfs (dataframes)
            self.dfs.append((df,model))
            # get also the text
            with open(FOLDER_EMB+emb+'/'+emb+'.json', 'r') as f:
                fulltext = json.load(f)
                self.all_texts.append(" ".join(fulltext['full']))
            # get also the bibtex
            with open(FOLDER_EMB+emb+'/bibtex.json', 'r') as f:
                bibtex = json.load(f)
                self.all_bib.append(bibtex)
            # get also the info.json 
            with open(FOLDER_EMB+emb+'/info.json', 'r') as f:
                info = json.load(f)
                self.all_info.append(info)

    def pre_confirm_paper(self):
        url = self.url.get()  # get the url from the entry box
        self.save_url()
        ### get the text
        self.papertitle.set("Obtaining PDF and tex files...")
        self.master.update()
        
        title,abstract = functions.getTitleOfthePaper(url) #get the title and abstract of the paper
        self.tex_files,self.bibfiles = functions.getPaper(url)  # get the paper from arxiv
        complete_text = functions.extract_all_text(self.tex_files)  # extract all the text from the tex files
        self.final_text = embedding_functions.texStripper(complete_text,title,abstract) # refine the text
        
        # open a new window to show the title and abstract of the paper
        self.titleabstract = tk.Toplevel(self.master)
        self.titleabstract.geometry('800x600')
        # insert the title of the paper
        self.titleabstract.title(title)
        # insert the abstract of the paper
        self.textabstract = tk.Text(self.titleabstract, height=40, width=80)
        self.textabstract.pack()
        self.textabstract.insert("1.0", 'Title: \n'+title)
        self.textabstract.insert("end", '\n\n')
        self.textabstract.insert("end", 'Abstract: \n'+abstract)
        # insert the url of the paper
        self.textabstract.insert("end", "\n\n")
        self.textabstract.insert("end", "URL: "+url)
        self.textabstract.insert("end", "\n\nTeX files found:"+str(self.tex_files))
        self.textabstract.insert("end", "\n\nBibtex files found:"+str(self.bibfiles))
        # create a dropdown menu to select the model for the embedding
        self.model = tk.StringVar(self.titleabstract)
        self.model.set('text-search-babbage-doc-001') # default value
        # get the cost estimate of each embedding
        cost_estimate_ada = "{:3.3f}".format(embedding_functions.compute_price_search_doc_embedding(self.final_text['tokens'], 'text-search-ada-doc-001'))
        cost_estimate_babbage = "{:3.3f}".format(embedding_functions.compute_price_search_doc_embedding(self.final_text['tokens'],'text-search-babbage-doc-001'))
        cost_estimate_curie = "{:3.3f}".format(embedding_functions.compute_price_search_doc_embedding(self.final_text['tokens'],'text-search-curie-doc-001'))

        
        # add a label with the cost estimate of the embeddings
        tk.Label(self.titleabstract, text="Cost estimate for the embedding: ").pack()
        tk.Label(self.titleabstract, text="Ada: "+str(cost_estimate_ada)+"$").pack()
        tk.Label(self.titleabstract, text="Babbage: "+str(cost_estimate_babbage)+"$").pack()
        tk.Label(self.titleabstract, text="Curie: "+str(cost_estimate_curie)+"$").pack()
        # add label above option menu
        tk.Label(self.titleabstract, text="Choose a model for the embedding of the paper: ").pack()

        self.dropdown = tk.OptionMenu(self.titleabstract, self.model, 'text-search-ada-doc-001','text-search-babbage-doc-001', 'text-search-curie-doc-001')
        self.dropdown.pack()

        # insert a button below the abstract to confirm the paper
        self.confirm = tk.Button(self.titleabstract, text="Confirm", command=self.confirm_paper)
        self.confirm.pack()

    def confirm_paper(self):
        """
        Confirm the paper and get the embedding
        """
        print('Paper confirmed, create embedding with model: '+self.model.get())
        self.textabstract.insert("end", "\n\n...Creating embedding using "+self.model.get()+"...")
        self.get_paper()
        self.titleabstract.destroy()

    def get_paper(self):
        """ Get the paper from the url 
        Create a new folder for the paper and save the paper in it
        Check if the paper is already in the folder
        Create the embedding for the paper

        """
        # EXTRACT THE PAPER FIRST FROM THE URL
        url = self.url.get()  # get the url from the entry box
        
        filename = url.split('/')[-1] #get the filename from the url
        header,abstract = functions.getTitleOfthePaper(url) #get the title of the paper

        self.papertitle.set("embedding...\n"+header)  # set the papertitle label
        self.master.update()
        
        if not os.path.exists(FOLDER_EMB+filename):
            print('Creating folder for embeddings')
            os.makedirs(FOLDER_EMB+filename)

        if not os.path.exists(FOLDER_EMB+filename+'/bibtex.json'):
            bib_text = functions.extract_all_text(self.bibfiles)  # extract the text from the bib file
            with open(FOLDER_EMB+filename+'/bibtex.json', 'w') as f:
                json.dump(bib_text, f)
        

        if not os.path.exists(FOLDER_EMB+filename+'/'+filename+'.json'):
            # self.complete_text = " ".join(self.final_text['full'])
            # save complete text to file
            with open(FOLDER_EMB+filename+'/'+filename+'.json', 'w') as f:
                json.dump(self.final_text, f)     
        else:
            print('complete text already exists')
        
        model_in_use = self.model.get()
        if not os.path.exists(FOLDER_EMB+filename+'/'+model_in_use+'.csv'):

            # create the embedding of the text
            df = pd.DataFrame(self.final_text['full'], columns=['Phrase'])
            df2= embedding_functions.save_embedding(df,filename,FOLDER_EMB,engine_search=model_in_use)
            dollars= embedding_functions.compute_price_search_doc_embedding(self.final_text['tokens'], model_in_use)
            self.update_token_usage(self.final_text['tokens'], dollars)
            # save title here
            with open(FOLDER_EMB+filename+'/info.json', 'w') as f:
                json.dump(header, f)
            # recheck the checkbuttons
            self.check_embedding_in_folder()
            self.papertitle.set("embedding...\n DONE!")  # set the papertitle label

        else:
            print('embedding already exists')
            self.papertitle.set("embedding...\n already present")
        self.final_text = None

        
        #find section and subsection of the paper
        # list_of_section = self.final_text['sections']
        # list_of_section = functions.remove_duplicates(list_of_section, simplecase=True)
        # print(list_of_section)
        # self.sections.delete(1.0, tk.END)
        # # interlink = Interlink(self.sections, self.keybox, self.question)
        # for i in list_of_section:
        #     self.sections.insert(tk.END, i+'\n')
            # apply the hyperlinks to the phrases
            # self.sections.highlight_pattern(i,interlink)
    def render_latex(self, text):
        """
        Render the latex text to an image
        """
        # render the latex text to an image
        try:
            # add \begin{minipage} and \end{minipage} to the text
            latextext = r'\begin{minipage}{13cm}'+r"{}".format(text)+r'\end{minipage}'
            print('Converting to latex...',latextext)
            # new plot
            # fig = plt.figure(figsize=(12, 6))
            plt.text(0.0, 1.0, latextext, fontsize=12)
            ax = plt.gca()
            ax.axis('off')
            with io.BytesIO() as png_buf:
                plt.savefig(png_buf, bbox_inches='tight', pad_inches=1)
                png_buf.seek(0)
                image = Image.open(png_buf)
                image.load()
                inverted_image = ImageOps.invert(image.convert("RGB"))
                cropped = image.crop(inverted_image.getbbox())
                cropped.save("lastprompt.png")

            self.img.append(tk.PhotoImage(file = "lastprompt.png"))
            # erase the plot
            plt.cla()
            plt.clf()
            plt.close()
            # erase lastpromt.png
            # os.remove('lastpromt.png')
            
            self.textbox.image_create(tk.END, image = self.img[-1]) # Example 1
            # self.textbox.window_create("end", window = tk.Label( image = img))
            self.textbox.insert("end", '\n\n')

            
        except Exception as e:
            print('Error rendering latex: ',e)
            self.textbox.insert(tk.END, text+'\n\n')
            #  restart the rendering 
            plt.cla()
            plt.clf()
            plt.close()


    def add_more_button(self):
        """
        Add a button to add more answer
        """
        self.button4more = tk.Button(self.textbox, text="More", padx=2, pady=2,
                                        cursor="left_ptr",
                                        bd=1, highlightthickness=0,
                                        command = self.more_answer)
        self.textbox.config(state=tk.NORMAL)
        self.textbox.window_create("end-2c", window=self.button4more)
        self.textbox.config(state=tk.DISABLED)

    def more_answer(self):
        """
        Add a more answer to the answer box
        """
        print('add more answer')
        # cancel self.button4more
        self.button4more.destroy()
        response = functions.simple_prompt(self.lastpromtanswer+'\n', api_key=self.apikey.get())
        answer = response['choices'][0]['text']
        if answer.strip() == '':
            answer = '*No answer. Start a new question*'
            latex_prob = ''
            addbutton = False
        else:
            self.save_to_history(self.lastpromtanswer, answer)
            _, latex_prob = self.compute_probability(response)
            addbutton = True
        print('answer',answer)
        self.textbox.config(state=tk.NORMAL)
        
        self.render_latex(answer.strip('\n')+latex_prob )
        # self.textbox.insert(tk.END,answer+'\n')  
        self.textbox.config(state=tk.DISABLED)
        tokens = response['usage']['total_tokens']
        model = response['model']
        self.lastpromtanswer = self.lastpromtanswer+answer
        dollars = functions.compute_price_completion(tokens, model)
        self.update_token_usage(tokens, dollars)
        
        
        if addbutton: self.add_more_button()
    def compute_probability(self, response):
        logprobs = response["choices"][0]["logprobs"]["token_logprobs"]
        prob = np.exp(logprobs)
        # average prob
        prob = prob.mean()
        print('prob',prob*100,'%')
        return prob*100, ' ('+str("{:1.1f}".format(prob*100))+'\%)'

    def run(self):
        """
        Run the program
        """
        list_of_phrases = []
        list_of_list_of_phrases = []
        list_of_phrases_with_similarity = []
        api_key = self.apikey.get()  # get the api key from the entry box
        question = self.question.get("1.0", tk.END).strip('\n')  # get the question from the entry box
        self.save_question()
        # add question to textbox
        self.textbox.config(state=tk.NORMAL)
        if self.number_of_prompts == 0:
            self.textbox.delete(1.0, tk.END)
            # self.textbox.insert(tk.END, 'You:\n'+question+'\n')
            self.render_latex('You:'+question)
        else:
            self.render_latex('You:'+question)
            # self.textbox.insert(tk.END, '\nYou:\n'+question+'\n')
            self.textbox.see("end")
        
        if self.button4more is not None:
            self.button4more.destroy()
        
        # check if the embeddings used have changed and update the embedding if necessary
        embedding_to_use = self.get_checked_embedding()
        if len(embedding_to_use) == 0:
            self.textbox.insert(tk.END, '\n Attention! You need to select papers to use.\n')
            return
        self.master.update()

        if self.last_embeddings != embedding_to_use:
            self.get_embedding(embedding_to_use)
            self.last_embeddings = embedding_to_use
            
        # set the textbox ready for input
        self.phraseinTex.config(state=tk.NORMAL)
        self.phraseinTex.delete('1.0', tk.END)  # clear the output box
        
        # get the value of standard_deviation from the slider
        standard_deviation = self.std_dev.get()

        # get the second entry of each tuple  in list embedding_to_use
        models = [x[1] for x in embedding_to_use]
        # remove duplicates
        models = functions.remove_duplicates(models, simplecase=True)
        print('models:', models)
        # engine_search_query ='text-search-babbage-query-001'
        embedding_question = {}
        for engine_search_query in models:
            embedding_question[engine_search_query], tokens, dollars = embedding_functions.compute_price_search_query_embedding(question,engine_search_query.replace('doc','query'))
            self.update_token_usage(tokens, dollars) # update the token usage

        # loop over all dataframes/embeddings and find the phrases that are similar to the question
        i=0
        number_of_papers_used = 0
        # pre compute the means and standard deviations of the embeddings
        mean= 0
        std = 0
        for df,model in self.dfs:
            df['query_doc_similarities'] = df.search.apply(lambda x: cosine_similarity(x, embedding_question[model]))
            mean += df.query_doc_similarities.mean()
            std += df.query_doc_similarities.std()**2
        mean = mean/len(self.dfs)
        std = np.sqrt(std/len(self.dfs))


        for df,model in self.dfs:
            # print first phrase in df
            phrases_with_similarity = []
            title = self.all_info[i]

            # Get list_of_phrases from the embeddings
            newres = embedding_functions.search_phrases(df,
                                                        mean,
                                                        std,
                                                        how_many_std=standard_deviation,
                                                        connect_adj=True, 
                                                        minimum_one_phrase=self.at_least_one_phrase.get())
            if len(newres)>0:
                number_of_papers_used += 1
                if i==0:
                    list_of_phrases.append('From paper:'+title+'\n')
                    phrases_with_similarity.append('>From paper:'+title+'('+model+')\n')
                else:
                    list_of_phrases.append('\nFrom paper:'+title+'\n')
                    phrases_with_similarity.append('\n\n >From paper:'+title+'('+model+')\n')

            temp_list_of_phrases = newres.Phrase.tolist()[:MAX_PHRASES_TO_USE]
            
            # compute mean and standard deviation of the embeddings, for each paper
            
            for sim,phr in zip(newres.query_doc_similarities.round(3).tolist(),temp_list_of_phrases):
                phrases_with_similarity.append("("+str("{:1.3f}".format((sim-mean)/std))+") "+phr)
            # find if there are hyperlink with arXiv and add them to the list of phrases
            phrases_with_similarity, all_hyperlinks = functions.get_hyperlink(phrases_with_similarity, self.all_texts[i]+self.all_bib[i])
            self.phraseinTex.insert(tk.END, '\n'.join(phrases_with_similarity))  # insert phrases in the textbox
            self.master.update()
            # get self.separate_answer value
            separate_answer = self.separate_answer.get()
            if separate_answer == 1:
                temp_list_of_phrases.insert(0,'\nFrom paper:'+title+'\n')
                list_of_list_of_phrases.append(temp_list_of_phrases)
            else:
                list_of_phrases.extend(temp_list_of_phrases)
            list_of_phrases_with_similarity.extend(phrases_with_similarity[:MAX_PHRASES_TO_USE])
            i+=1
            # if len(list_of_phrases) > MAX_PHRASES_TO_USE+(i+1) and :
            #     break

        if len(list_of_phrases) > 0: #if there are phrases!
            tokens = 0
            # MOST IMPORTANT STEP, ASK GPT-3 TO GIVE THE ANSWER
            try:
                # self.textbox.insert(tk.END,'\nGPT3:')
                self.render_latex('GPT3:')
                if separate_answer == 1 and len(list_of_list_of_phrases) > 1:
                    
                    for p,list_of_phrases in enumerate(list_of_list_of_phrases):
                        response, prompt = functions.promptText_question(question, list_of_phrases,1, api_key) #ask GPT-3 to give the answer
                        tokens += response['usage']['total_tokens']
                        model = response['model']
                        answer = response['choices'][0]['text']
                        probabilty_answer, latex_prob = self.compute_probability(response)
                        self.render_latex('From paper:'+self.all_info[p])
                        self.render_latex(answer.strip('\n')+ latex_prob)
                        # self.textbox.insert(tk.END,answer+'\n\n')  # insert the answer in the output box
                        self.master.update()
                else:
                    response, prompt = functions.promptText_question(question, list_of_phrases,number_of_papers_used, api_key) #ask GPT-3 to give the answer
                    tokens = response['usage']['total_tokens']
                    model = response['model']
                    answer = response['choices'][0]['text']
                    probabilty_answer, latex_prob = self.compute_probability(response)
                    self.render_latex(answer.strip('\n')+ latex_prob)

                    # self.textbox.insert(tk.END,answer+'\n')  # insert the answer in the output box
                    self.lastpromtanswer = prompt+answer
                    self.add_more_button()
                    # self.textbox.insert(tk.END,'\n')

                
                # self.textbox.see("end")
                # self.textbox.config(background="light green") # change the background color of the output box
                # self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
                dollars = functions.compute_price_completion(tokens, model)
                self.update_token_usage(tokens, dollars) #update the token usage
                # save the question and answer in self.question_and_answer to used in next prompt as reference
                # self.last_question_and_answer= 'You:'+question+'\n\nGPT3:'+answer+'\n' #UNCOMMENT IF NECESSARY
                self.save_to_history(question, answer)

                self.number_of_prompts += 1

            except Exception as e:
                self.textbox.insert(tk.END, 'Error: ' + str(e)+"\n\n")
                self.textbox.config(background="red") # change the background color of the output box
                self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
            

           

            # apply the hyperlinks to the phrases
            hyperlink = HyperlinkManager(self.phraseinTex, self.url)
            print('hyperlinks:',all_hyperlinks)
            for link in all_hyperlinks:
                self.phraseinTex.highlight_pattern(link,hyperlink)
  
            # for k,keyword in enumerate(keywords.split(',')):
            #     #print(COLOR_LIST[k%len(COLOR_LIST)])
            #     self.phraseinTex.highlight_pattern(keyword, tag=COLOR_LIST[k%len(COLOR_LIST)])
            self.phraseinTex.config(state=tk.DISABLED)

            # # TODO:try render the textbox containg latex formulas
            

        else:
            self.textbox.insert(tk.END, '\n No phrases found in Tex at the level of standard deviation selected! Try lower the standard deviation or check the box "At least one phrase per paper".')
        self.textbox.config(state=tk.DISABLED)




root = tk.Tk()
root.title("ArXiv Paper Oracle: Q&A Tool with OpenAI GPT-3")
root.geometry("1400x800")
root.columnconfigure(4) 
root.configure(background="darkgray")
root.bind_class("Entry", "<<Paste>>", custom_paste)
root.grid_columnconfigure(0, weight=1) 
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
app = Application(master=root)
app.mainloop()
