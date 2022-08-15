#! /usr/bin/env python
import tkinter as tk
import os

import sklearn.utils._typedefs
import sklearn.utils._heap
import sklearn.utils._sorting
import sklearn.utils._vector_sentinel
import sklearn.neighbors._partition_nodes
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


sys.setrecursionlimit(10000)
MAX_PHRASES_TO_USE = 10
FOLDER_EMB = 'embeddings/'
class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        #initialization
        self.last_question_and_answer = None
        self.dfs = [] #list of dataframes
        self.checkbuttons = []
        self.last_embeddings = []
        self.number_of_prompts = 0
        self.create_widgets()
                                   

    def create_widgets(self):
        # make folders if it doesn't exist
        self.init_folders()

        
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
        if os.path.isfile('default_url.csv'):
            with open('default_url.csv', 'r') as f:
                self.url.insert(tk.END, f.read())
        
        tk.Label(self.master, textvariable=self.papertitle, wraplength=400).grid(row=5, column=0)
        
        
        self.textembedding = tk.Text(self.master, width=50, height=40, wrap=tk.WORD)
        self.vsb = tk.Scrollbar(self.master, orient="vertical")
        self.vsb.grid(row=6, column=0, sticky='nse')
        self.vsb.config(command=self.textembedding.yview)
        self.textembedding.grid(row=6, column=0, rowspan=2)
        self.textembedding['yscrollcommand'] = self.vsb.set

 

        # # section and subsection
        # self.sections = CustomText(self.master, wrap=tk.WORD, width=60, height=35)
        # self.sections.grid(row=6, column=0, rowspan=3)
        # self.sections.bind('<Button-3>', RightClicker)
        
        tk.Label(self.master, textvariable = self.token_label).grid(row=9, column=0 , sticky=tk.W)
        
        #Column 1 widgets
        # add a slider to change the standard deviation, from 0 to 4 with label "Standard deviation"
        

        #menu for embedding
        # self.default_embedding = tk.StringVar()
        # self.default_embedding.set("Embeddings")
        # self.default_embedding.trace("w", self.callback_to_embedding) #callback to update the url
        self.check_embedding_in_folder() #check if there are embeddings in the folder
        


        # output box to display the result
        
        tk.Label(self.master, text="Answer from GPT-3").grid(row=3, column=1, columnspan=2)
        self.textbox = tk.Text(self.master, height=40, width=70, wrap='word')
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
        if os.path.isfile('default_question.csv'):
            with open('default_question.csv', 'r') as f:
                self.question.insert(tk.END, f.read())

        

        #Column 2 widgets
        self.std_dev = tk.IntVar()
        self.std_dev.set(0)
        self.std_dev_slider = tk.Scale(self.master, from_=0, to=4, orient=tk.HORIZONTAL, variable=self.std_dev)
        self.std_dev_slider.grid(row=4, column=3)
        self.std_dev_slider.bind('<Button-3>', RightClicker)
        tk.Label(self.master, text="Standard deviation of phrases in TeX").grid(row=3, column=3)
        self.std_dev_slider.set(2)

          # new textbox for the phrases matching the question
        
        tk.Label(self.master, text="Phrases in Tex given to GPT").grid(row=5, column=3, columnspan=1)
        self.phraseinTex = CustomText(self.master, height=35, width=60, wrap='word')
        self.phraseinTex.grid(row=6, column=3, rowspan=3)
        self.phraseinTex.bind('<Button-3>', RightClicker)
        self.phraseinTex.insert(tk.END, "Phrases")
        self.phraseinTex.config(state=tk.DISABLED,
                             background="white",
                             foreground="black",
                             font=("Helvetica", 11),
                             borderwidth=2,
                             )
        self.vsb3 = tk.Scrollbar(self.master, orient="vertical")
        self.vsb3.grid(row=6, column=3, rowspan=3, sticky='nse')
        self.vsb3.config(command=self.phraseinTex.yview)
        self.phraseinTex['yscrollcommand'] = self.vsb3.set


        

        #BUTTONS
        #button under url box named "Get paper"
        tk.Button(self.master, text='Get paper and create embedding', command=self.pre_confirm_paper).grid(row=4, column=0)

        tk.Button(self.master, text='Reset usage', command=self.reset_token_usage).grid(row=10, column=0, sticky=tk.W)                     

       


        

        tk.Button(self.master, text='Run', command=self.run).grid(row=11,
                                                                  column=1,
                                                                  pady=4,
                                                                  sticky=tk.E)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=11,
                                                                    column=2,
                                                                    pady=4,
                                                                    sticky=tk.W)
        

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
    
    def check_embedding_in_folder(self):
        """
        Check if there are embeddings in the folder, and defaults used last time
        If so, then set the checkbox, already checked according to the default embeddings
        """
        self.checkbuttons = []
        # clear self.textembedding
        self.textembedding.delete(1.0, tk.END)
        self.embeddings = list(os.listdir(FOLDER_EMB))
        def_emb = []
        if os.path.isfile('default_embeddings.csv'):
            with open('default_embeddings.csv', 'r') as f:
                # read all the lines in the file
                def_emb = f.readlines()
                # remove the newline character at the end of each line
                def_emb = [x.strip() for x in def_emb]

        if len(self.embeddings) > 0:
            for emb in self.embeddings:
                with open(FOLDER_EMB+emb+'/info.json', 'r') as f:
                    info = json.load(f)
                j = tk.IntVar()
                if emb in def_emb:
                    j.set(1)
                cb = WrappingCheckbutton(self.master, text=info, variable=j)
                # add cb to a list of checkbuttons
                self.checkbuttons.append((j,emb))
                self.textembedding.window_create("end", window=cb)
                self.textembedding.insert("end", "\n") # to force one checkbox per line

                # check if the checkbox is checked

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

        self.token_label.set('Usage: '+str(total_token_used)+' tokens ($'+"{:3.3f}".format(total_dollars_used)+')') #update the token usage label

    # def get_paper_and_embedding(self):
    #     self.get_paper()
    #     self.get_embedding()
        
    def get_checked_embedding(self):
        """
        Get the list of checked embedding from UI
        """
        list_of_embeddings = []
        for i,but in self.checkbuttons:
            if i.get() == 1:
                list_of_embeddings.append(but)
        # save the default embeddings to a file
        with open('default_embeddings.csv', 'w') as f:
            for emb in list_of_embeddings:
                f.write(emb+'\n')
        print("Embedding to use",list_of_embeddings)
        return list_of_embeddings

    def get_embedding(self, embedding_to_use):
        """
        Get the embedding from the folder
        """
        FOLDER_EMB = 'embeddings/'
        self.dfs = []
        self.all_texts = []
        self.all_bib = []
        self.all_info = []
        for emb in embedding_to_use:
            path = FOLDER_EMB+emb
            path += '/text-search-babbage-doc-001.csv'
            df = pd.read_csv(path, index_col=0)
            # df['similarity'] = df.similarity.apply(eval).apply(np.array)
            df['search'] = df.search.apply(eval).apply(np.array)
            # append the df to the list of dfs (dataframes)
            self.dfs.append(df)
            # get also the text
            with open(FOLDER_EMB+emb+'/'+emb+'.json', 'r') as f:
                final_text = json.load(f)
                self.all_texts.append(" ".join(final_text['full']))
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

        title,abstract = functions.getTitleOfthePaper(url) #get the title of the paper
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
        # insert a button below the abstract to confirm the paper
        self.confirm = tk.Button(self.titleabstract, text="Confirm", command=self.confirm_paper)
        self.confirm.pack()

    def confirm_paper(self):
        """
        Confirm the paper and get the embedding
        """
        print('Paper confirmed')
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
        self.save_url()

        header,abstract = functions.getTitleOfthePaper(url) #get the title of the paper

        # wait for the user to confirm the paper

        self.papertitle.set("embedding...\n"+header)  # set the papertitle label
        self.master.update()
        tex_files,bibfiles = functions.getPaper(url)  # get the paper from arxiv
        print('tex_files found:', tex_files)
        print('bib_text found:', bibfiles)
        filename = url.split('/')[-1] #get the filename from the url
        
        if not os.path.exists(FOLDER_EMB+filename):
            print('Creating folder for embeddings')
            os.makedirs(FOLDER_EMB+filename)

        if not os.path.exists(FOLDER_EMB+filename+'/bibtex.json'):
            bib_text = functions.extract_all_text(bibfiles)  # extract the text from the bib file
            with open(FOLDER_EMB+filename+'/bibtex.json', 'w') as f:
                json.dump(bib_text, f)

        if not os.path.exists(FOLDER_EMB+filename+'/'+filename+'.json'):
            complete_text = functions.extract_all_text(tex_files)  # extract all the text from the tex files
            final_text = embedding_functions.texStripper(complete_text) # refine the text
            self.complete_text = " ".join(final_text['full'])
            # save complete text to file
            with open(FOLDER_EMB+filename+'/'+filename+'.json', 'w') as f:
                json.dump(final_text, f)
            
            # create the embedding of the text
            df = pd.DataFrame(final_text['full'], columns=['Phrase'])
            df2,dollars,tokens = embedding_functions.save_embedding(df,filename,FOLDER_EMB, final_text['tokens'])
            self.update_token_usage(tokens, dollars)
            # save title here
            with open(FOLDER_EMB+filename+'/info.json', 'w') as f:
                json.dump(header, f)
            # recheck the checkbuttons
            self.check_embedding_in_folder()

            self.papertitle.set("embedding...\n DONE!")  # set the papertitle label

        else:
            print('complete text already exists')
            self.papertitle.set("embedding...\n already present")
       

        
        

        # SET THE INFO ON SCREEN
        
  
        # save header to info.json
        
        #find section and subsection of the paper
        # list_of_section = final_text['sections']
        # list_of_section = functions.remove_duplicates(list_of_section, simplecase=True)
        # print(list_of_section)
        # self.sections.delete(1.0, tk.END)
        # # interlink = Interlink(self.sections, self.keybox, self.question)
        # for i in list_of_section:
        #     self.sections.insert(tk.END, i+'\n')
            # apply the hyperlinks to the phrases
            # self.sections.highlight_pattern(i,interlink)


    def run(self):
        """
        Run the program
        """
        list_of_phrases = []
        list_of_phrases_with_similarity = []
        api_key = self.apikey.get()  # get the api key from the entry box
        question = self.question.get("1.0", tk.END).strip('\n')  # get the question from the entry box
        self.save_question()
        # add question to textbox
        # chec if textbox contains "Output"
        self.textbox.config(state=tk.NORMAL)
        if self.number_of_prompts == 0:
            self.textbox.delete(1.0, tk.END)
            self.textbox.insert(tk.END, 'You:\n'+question+'\n')
        else:
            self.textbox.insert(tk.END, '\nYou:\n'+question+'\n')
            self.textbox.see("end")
        
        self.master.update()
        
        # check if the embeddings used have changed and update the embedding if necessary
        embedding_to_use = self.get_checked_embedding()
        if self.last_embeddings != embedding_to_use:
            self.get_embedding(embedding_to_use)
            self.last_embeddings = embedding_to_use
            
        # set the textbox ready for input
        self.phraseinTex.config(state=tk.NORMAL)
        self.phraseinTex.delete('1.0', tk.END)  # clear the output box
        
        # get the value of stadard_deviation from the slider
        standard_deviation = self.std_dev.get()
        engine_search_query ='text-search-babbage-query-001'

        embedding_question, tokens, dollars = embedding_functions.compute_price_search_query_embedding(question,engine_search_query)
        self.update_token_usage(tokens, dollars) # update the token usage, just 
        # loop over all dataframes/embeddings and find the phrases that are similar to the question
        for i,df in enumerate(self.dfs):
            # print first phrase in df
            phrases_with_similarity = []
            title = self.all_info[i]
            # Get list_of_phrases from the embeddings
            newres = embedding_functions.search_phrases(df, embedding_question, how_many_std=standard_deviation,connect_adj=True)
            if i==0: 
                list_of_phrases.append('From paper:'+title+'\n')
                phrases_with_similarity.append('>From paper:'+title+'\n')
            else:
                list_of_phrases.append('\nFrom paper:'+title+'\n')
                phrases_with_similarity.append('\n\n >From paper:'+title+'\n')

            temp_list_of_phrases = newres.Phrase.tolist()[:MAX_PHRASES_TO_USE]
            
            # compute mean and standard deviation of the embeddings, for each paper
            mean = df.query_doc_similarities.mean()
            std = df.query_doc_similarities.std()
            for sim,phr in zip(newres.query_doc_similarities.round(3).tolist(),temp_list_of_phrases):
                phrases_with_similarity.append("("+str("{:1.3f}".format((sim-mean)/std))+") "+phr)
            # find if there are hyperlink with arXiv and add them to the list of phrases
            phrases_with_similarity, all_hyperlinks = functions.get_hyperlink(phrases_with_similarity, self.all_texts[i]+self.all_bib[i])
            self.phraseinTex.insert(tk.END, '\n'.join(phrases_with_similarity))  # insert phrases in the textbox
            self.master.update()

            list_of_phrases.extend(temp_list_of_phrases)
            list_of_phrases_with_similarity.extend(phrases_with_similarity[:MAX_PHRASES_TO_USE])
            # if len(list_of_phrases) > MAX_PHRASES_TO_USE+(i+1) and :
            #     break

        if len(list_of_phrases) > 0: #if there are phrases!
            
            # MOST IMPORTANT STEP, ASK GPT-3 TO GIVE THE ANSWER
            try:
                response = functions.promptText_question(question, list_of_phrases,self.last_question_and_answer,len(self.dfs), api_key) #ask GPT-3 to give the answer
                tokens = response['usage']['total_tokens']
                model = response['model']
                answer = response['choices'][0]['text'].strip('\n')
                dollars = functions.compute_price_completion(tokens, model)
                self.update_token_usage(tokens, dollars) #update the token usage
                self.textbox.insert(tk.END,'\nGPT3:\n'+answer+'\n')  # insert the answer in the output box
                self.textbox.see("end")
                self.textbox.config(background="green") # change the background color of the output box
                self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
                # save the question and answer in self.question_and_answer to used in next prompt as reference
                self.last_question_and_answer= 'You:'+question+'\n\nGPT3:'+answer+'\n'
                with open('history.json', 'a') as f:
                    json.dump({'question':question,'answer':answer}, f)
                    f.write('\n')
                self.number_of_prompts += 1

            except Exception as e:
                self.textbox.insert(tk.END, 'Error: ' + str(e))
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
        else:
            self.textbox.insert(tk.END, '\n Attention! You need to select papers to use.')
        self.textbox.config(state=tk.DISABLED)




root = tk.Tk()
root.title("ArXiv Paper Oracle: Q&A Tool with OpenAI GPT-3")
root.geometry("2000x1000")
root.columnconfigure(4) 
root.configure(background="darkgray")
root.bind_class("Entry", "<<Paste>>", custom_paste)
root.grid_columnconfigure(0, weight=1) 
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
root.grid_columnconfigure(3, weight=1)
app = Application(master=root)
app.mainloop()
