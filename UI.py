#! /usr/bin/env python
import tkinter as tk
import os
# import sympy as sp
# from PIL import Image, ImageTk
# from io import BytesIO
# import textwrap

#MY FUNCTIONS
import functions
import embedding_functions
from Tkinter_helper import CustomText, custom_paste, HyperlinkManager,Interlink,COLOR_LIST, RightClicker
import sys
import pandas as pd
import numpy as np
import openai
sys.setrecursionlimit(10000)
MAX_PHRASES_TO_USE = 7

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.last_url = ''
        self.create_widgets()
                                   

    def create_widgets(self):
        # make folders if it doesn't exist
        if not os.path.exists('papers'):
            os.makedirs('papers')
        if not os.path.exists('embeddings'):
            os.makedirs('embeddings')
        
        
        # variables
        self.dollars = tk.DoubleVar()
        self.dollars.set(0.0)
        
        self.token_usage = tk.IntVar()
        self.token_usage.set(0)
        
        self.token_label = tk.StringVar()
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')
        
        self.papertitle = tk.StringVar()
        self.papertitle.set('\n')


        # Column 0 widgets
        tk.Label(self.master, text="API Key").grid(row=0, column=0)
        self.apikey = tk.Entry(self.master, width=30)
        self.apikey.grid(row=1, column=0)
        self.apikey.bind('<Button-3>', RightClicker)

        tk.Label(self.master, text="arXiv URL").grid(row=2, column=0)
        self.url = tk.Entry(self.master, width=35)
        self.url.grid(row=3, column=0)
        self.url.bind('<Button-3>', RightClicker)
        # tk.Label(self.master, text="Paper title").grid(row=4, column=0)
        
        tk.Label(self.master, textvariable=self.papertitle, wraplength=500).grid(row=5, column=0)
        
        

        #menu for embedding
        self.default_embedding = tk.StringVar()
        self.default_embedding.set("Embeddings")
        self.default_embedding.trace("w", self.callback_to_embedding) #callback to update the url
        self.check_embedding_in_folder() #check if there are embeddings in the folder
        if len(self.embeddings) > 0:
            self.embedding_menu = tk.OptionMenu(self.master, self.default_embedding, *self.embeddings)
            self.embedding_menu.grid(row=4, column=0,sticky=tk.E)



        # section and subsection
        self.sections = CustomText(self.master, wrap=tk.WORD, width=70, height=50)
        self.sections.grid(row=6, column=0, rowspan=3)
        self.sections.bind('<Button-3>', RightClicker)
        
        
        #Column 1 widgets
        tk.Label(self.master, text="Question").grid(row=1,column=1, columnspan=2)
        self.question = tk.Text(self.master, wrap=tk.WORD, width=70, height=2)
        self.question.grid(row=2, column=1, columnspan=2)
        self.question.bind('<Button-3>', RightClicker)


        

        #Column 2 widgets
        tk.Label(self.master, textvariable = self.token_label).grid(row=9, column=0 , sticky=tk.W)
        
        #Set defaults values
        # if api.txt exist then insert the content of api.txt into apikey entry else insert default value
        if os.path.isfile('API.csv'):
            openai.api_key_path = "API.csv"
            with open('API.csv', 'r') as f:
                self.apikey.insert(0, f.read())
        else:
            self.apikey.insert(0, 'Your API Key here')
            # if apikey is selected by the user then cancel its content
            self.apikey.bind('<Button-1>', lambda event: self.apikey.delete(0, tk.END))
            tk.Button(self.master, text='Save API Key', command=self.save_api_key).grid(row=1, column=0, sticky=tk.W)

        # if default_values.csv exist then load url and question from default_values.csv
        if os.path.isfile('default_url.csv'):
            with open('default_url.csv', 'r') as f:
                self.url.insert(tk.END, f.read())
        if os.path.isfile('default_question.csv'):
            with open('default_question.csv', 'r') as f:
                self.question.insert(tk.END, f.read())
        #add one button to save default url
        tk.Button(self.master, text='Set default URL', command=self.save_url).grid(row=3, column=0, sticky=tk.W)
        #add one button to save default question
        tk.Button(self.master, text='Set default Question', command=self.save_question).grid(row=2, column=2, sticky=tk.E)


       
        self.question.focus()
        
         # new textbox for the phrases matching the question
        self.textbox2 = CustomText(self.master, height=20, width=90, wrap='word')
        self.textbox2.grid(row=6, column=1, columnspan=2)
        self.textbox2.bind('<Button-3>', RightClicker)
        self.textbox2.insert(tk.END, "Phrases")
        self.textbox2.config(state=tk.DISABLED,
                             background="white",
                             foreground="black",
                             font=("Helvetica", 11),
                             borderwidth=2,
                             )

        # output box to display the result
        self.textbox = tk.Text(self.master, height=20, width=90, wrap='word')
        self.textbox.grid(row=8, column=1, columnspan=2)
        self.textbox.bind('<Button-3>', RightClicker)
        self.textbox.insert(tk.END, "Output")
        self.textbox.config(state=tk.DISABLED,
                            background="white",
                            foreground="black",
                            font=("Helvetica", 11,'bold'),
                            borderwidth=2,
                            )
        
        tk.Label(self.master, text="Phrases in Tex").grid(row=5, column=1, columnspan=2)
        tk.Label(self.master, text="Answer from GPT-3").grid(row=7, column=1, columnspan=2)

        # add a slider to change the standard deviation, from 0 to 4 with label "Standard deviation"
        self.std_dev = tk.IntVar()
        self.std_dev.set(0)
        self.std_dev_slider = tk.Scale(self.master, from_=0, to=4, orient=tk.HORIZONTAL, variable=self.std_dev)
        self.std_dev_slider.grid(row=4, column=1, columnspan=2)
        self.std_dev_slider.bind('<Button-3>', RightClicker)
        tk.Label(self.master, text="Standard deviation").grid(row=3, column=1,columnspan=2)
        self.std_dev_slider.set(2)
        

        #BUTTONS
        #button under url box named "Get paper"
        tk.Button(self.master, text='Get paper and create embedding', command=self.get_paper).grid(row=4, column=0)

        tk.Button(self.master, text='Reset usage', command=self.reset_token_usage).grid(row=10, column=0, sticky=tk.W)                     

       


        

        tk.Button(self.master, text='Run', command=self.run).grid(row=10,
                                                                  column=1,
                                                                  pady=4,
                                                                  sticky=tk.E)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=10,
                                                                    column=2,
                                                                    pady=4,
                                                                    sticky=tk.W)
        


    def callback_to_url(self,*args):
        self.url.delete(0, tk.END)
        url_to_use = "http://arxiv.org/abs/"+self.default_paper.get()
        self.url.insert(0,url_to_use)
        self.get_paper()

    def callback_to_embedding(self,*args):
        self.url.delete(0, tk.END)
        url_to_use = "http://arxiv.org/abs/"+self.default_embedding.get()
        self.url.insert(0,url_to_use)
        self.embedding_to_use = "embeddings/"+self.default_embedding.get()
        self.get_embedding()

    def check_papers_in_folder(self):
        self.folders = list(os.listdir('papers/'))
    
    def check_embedding_in_folder(self):
        self.embeddings = list(os.listdir('embeddings/'))

    def reset_token_usage(self):
        self.token_usage.set(0)
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')
        self.dollars.set(0.0)

    def save_api_key(self):
        api_key = self.apikey.get()
        with open('API.csv', 'w') as f:
            f.write(api_key)
    
    def save_url(self):
        url = self.url.get()
        with open('default_url.csv', 'w') as f:
            f.write(url)
    
    def save_question(self):
        question = self.question.get("1.0", tk.END)
        with open('default_question.csv', 'w') as f:
            f.write(question)

    def update_token_usage(self,tokens, model):
        total_token_used = self.token_usage.get() #get the current token usage
        total_dollars_used = self.dollars.get() #get the current dollars usage
        
        total_token_used += tokens #add the tokens used to the total token usage
        self.token_usage.set(total_token_used) #update the token usage

        if model == 'text-davinci-002': #if the model is davinci
            dollars = tokens * (0.06/1000)
        elif model == 'text-curie-006': #if the model is curie
            dollars = tokens * (0.006/1000)
        elif model == 'text-babbage-001': #if the model is babbage
            dollars = tokens * (0.0012/1000)
        elif model =='text-ada-001': #if the model is ada
            dollars = tokens * (0.0008/1000)
        else:
            dollars = 0
        total_dollars_used += dollars #add the dollars used to the total dollars usage
        self.dollars.set(total_dollars_used) #update the dollars usage

        self.token_label.set('Usage: '+str(total_token_used)+' tokens ($'+"{:3.5f}".format(total_dollars_used)+')') #update the token usage label

    def get_paper_and_embedding(self):
        self.get_paper()
        self.get_embedding()
        

    def get_embedding(self):
        path = 'embeddings/'
        if hasattr(self, 'embedding_to_use'):
            path += self.embedding_to_use
        else:
            path += self.url.get().split('/')[-1]
        path += '/text-search-babbage-doc-001.csv'
        df = pd.read_csv(path, index_col=0)
        df['similarity'] = df.similarity.apply(eval).apply(np.array)
        df['search'] = df.search.apply(eval).apply(np.array)
        self.df = df
        
            # apply the hyperlinks to the phrases

        

    def get_paper(self):
        """ Get the paper from the url """
        # EXTRACT THE PAPER FIRST FROM THE URL
        url = self.url.get()  # get the url from the entry box
        tex_files,bibfiles = functions.getPaper(url)  # get the paper from arxiv
        print('tex_files found:', tex_files)
        complete_text = functions.extract_all_text(tex_files)  # extract the text from the paper
        final_text = embedding_functions.texStripper(complete_text)
        self.complete_text = " ".join(final_text['full'])
        self.bib_text = functions.extract_all_text(bibfiles)  # extract the text from the bib file

        # OBTAIN THE EMBEDDING FROM THE PHRASES IN THE PAPER
        emb_folder='embeddings'
        filename = url.split('/')[-1]
        if not os.path.exists(emb_folder+'/'+filename):
            os.makedirs(emb_folder+'/'+filename)
            df = pd.DataFrame(final_text['full'], columns=['Phrase'])
            df2 = embedding_functions.save_embedding(df,filename,emb_folder)
            self.df = df2
        else:
            self.get_embedding()
            print('embedding already exists')
        
        print('bib_text found:', bibfiles)

        # SET THE INFO ON SCREEN
        header = functions.getTitleOfthePaper(url) #get the title of the paper
        self.papertitle.set(header)  # set the papertitle label
        self.last_url = url  # save the last url
        #find section and subsection of the paper
        list_of_section = final_text['sections']
        list_of_section = functions.remove_duplicates(list_of_section, simplecase=True)
        print(list_of_section)
        self.sections.delete(1.0, tk.END)
        # interlink = Interlink(self.sections, self.keybox, self.question)
        for i in list_of_section:
            self.sections.insert(tk.END, i+'\n')
            # apply the hyperlinks to the phrases
            # self.sections.highlight_pattern(i,interlink)


    def run(self):
        api_key = self.apikey.get()  # get the api key from the entry box
        question = self.question.get("1.0", tk.END)  # get the question from the entry box




        if self.last_url != self.url.get():  # if the url has changed
            self.get_paper_and_embedding()  # download the paper
        
        if self.df is None:
            self.get_embedding()
 
        # Get list_of_phrases from the text
        list_of_phrases = []
        # get the value of stadard_deviation from the slider
        standard_deviation = self.std_dev.get()
        _,newres = embedding_functions.search_phrases(self.df, question, how_many_std=standard_deviation,connect_adj=True)
        list_of_phrases = newres.Phrase.tolist()
        list_of_similarity = newres.query_doc_similarities.round(3).tolist()
        # take only the first 5 phrases
        if len(list_of_phrases) > MAX_PHRASES_TO_USE:
            list_of_phrases = list_of_phrases[:MAX_PHRASES_TO_USE]
            list_of_similarity = list_of_similarity[:MAX_PHRASES_TO_USE]

        # combine each phrase with its similarity
        list_of_phrases_with_similarity = []
        for i in range(len(list_of_phrases)):
            list_of_phrases_with_similarity.append("("+str(list_of_similarity[i])+") "+list_of_phrases[i])




        # Initialize the textbox to receive the generated text
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete(1.0, tk.END)

        if len(list_of_phrases) > 0: #if there are phrases!
            list_of_phrases_with_similarity, all_hyperlinks = functions.get_hyperlink(list_of_phrases_with_similarity, self.complete_text+self.bib_text)
             # show the phrases in the output box
            self.textbox2.config(state=tk.NORMAL)
            self.textbox2.delete('1.0', tk.END)  # clear the output box
            self.textbox2.insert(tk.END, '-'+'\n-'.join(list_of_phrases_with_similarity))  # insert phrases in the textbox
            
            
            
            
            
            # MOST IMPORTANT STEP, ASK GPT-3 TO GIVE THE ANSWER
            try:
                response = functions.promptText_question(question, list_of_phrases, self.papertitle.get(), api_key) #ask GPT-3 to give the answer
                tokens = response['usage']['total_tokens']
                model = response['model']
                answer = response['choices'][0]['text']
                
                self.update_token_usage(tokens, model) #update the token usage

                self.textbox.insert(tk.END, answer)  # insert the answer in the output box
                self.textbox.config(background="green") # change the background color of the output box
                self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
            except Exception as e:
                self.textbox.insert(tk.END, 'Error: ' + str(e))
                self.textbox.config(background="red") # change the background color of the output box
                self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
            

           

            # apply the hyperlinks to the phrases
            hyperlink = HyperlinkManager(self.textbox2, self.url)
            for link in all_hyperlinks:
                self.textbox2.highlight_pattern(link,hyperlink)
  
            # for k,keyword in enumerate(keywords.split(',')):
            #     #print(COLOR_LIST[k%len(COLOR_LIST)])
            #     self.textbox2.highlight_pattern(keyword, tag=COLOR_LIST[k%len(COLOR_LIST)])
            self.textbox2.config(state=tk.DISABLED)
        else:
            self.textbox.insert(tk.END, 'No phrases found in the paper.')
        self.textbox.config(state=tk.DISABLED)




root = tk.Tk()
root.title("ArXiv Paper Genie: Q&A Tool with OpenAI GPT-3")
root.geometry("1500x800")
root.columnconfigure(3) 
root.configure(background="darkgray")
root.bind_class("Entry", "<<Paste>>", custom_paste)
root.grid_columnconfigure(0, weight=1) 
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
app = Application(master=root)
app.mainloop()
