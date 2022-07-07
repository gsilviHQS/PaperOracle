#! /usr/bin/env python
import tkinter as tk
import os

#MY FUNCTIONS
import functions
from Tkinter_helper import CustomText, custom_paste, HyperlinkManager,Interlink,COLOR_LIST



class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.last_url = ''
        self.create_widgets()
                                   

    def create_widgets(self):
        # variables
        self.dollars = tk.DoubleVar()
        self.dollars.set(0.0)
        self.token_usage = tk.IntVar()
        self.token_usage.set(0)
        self.token_label = tk.StringVar()
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')

        # Column 0 widgets
        tk.Label(self.master, text="API Key").grid(row=0, column=0)
        self.apikey = tk.Entry(self.master, width=30)
        self.apikey.grid(row=1, column=0)
        tk.Label(self.master, text="arXiv URL").grid(row=2, column=0)
        self.url = tk.Entry(self.master, width=40)
        self.url.grid(row=3, column=0)
        # tk.Label(self.master, text="Paper title").grid(row=4, column=0)
        self.papertitle = tk.StringVar()
        self.papertitle.set('\n')
        tk.Label(self.master, textvariable=self.papertitle, wraplength=500).grid(row=5, column=0)
       
        self.sections = CustomText(self.master, wrap=tk.WORD, width=70, height=50)
        self.sections.grid(row=6, column=0, rowspan=3)
        
        
        #Column 1 widgets
        tk.Label(self.master, text="Question").grid(row=0,column=1, columnspan=2)
        self.question = tk.Text(self.master, width=70, height=2)
        self.question.grid(row=1, column=1, columnspan=2)

        tk.Label(self.master, text="Keywords to search (separated by comma)").grid(row=2, column=1, columnspan=2)
        self.keybox = tk.Text(self.master, width=70, height=2)
        self.keybox.grid(row=3, column=1, columnspan=2)
        tk.Label(self.master, text="Matching Phrases in tex files").grid(row=5, column=1, columnspan=2)
        tk.Label(self.master, text="Answer from GPT-3").grid(row=7, column=1, columnspan=2)

        #Column 2 widgets
        tk.Label(self.master, textvariable = self.token_label).grid(row=9, column=0 , sticky=tk.W)
        
        #Set defaults values
        # if api.txt exist then insert the content of api.txt into apikey entry else insert default value
        if os.path.isfile('API.csv'):
            with open('API.csv', 'r') as f:
                self.apikey.insert(0, f.read())
        else:
            self.apikey.insert(0, 'Your API Key here')
            #add button to save the api key
            tk.Button(self.master, text='Save API Key', command=self.save_api_key).grid(row=1, column=0, sticky=tk.E)

        # if default_values.csv exist then load url and question from default_values.csv
        if os.path.isfile('default_url.csv'):
            with open('default_url.csv', 'r') as f:
                self.url.insert(tk.END, f.read())
        if os.path.isfile('default_question.csv'):
            with open('default_question.csv', 'r') as f:
                self.question.insert(tk.END, f.read())
        #add one button to save default url
        tk.Button(self.master, text='Save URL', command=self.save_url).grid(row=3, column=0, sticky=tk.E)
        #add one button to save default question
        tk.Button(self.master, text='Save Question', command=self.save_question).grid(row=1, column=2, sticky=tk.E)


       
        self.question.focus()
        
         # new textbox for the phrases matching the question
        self.textbox2 = CustomText(self.master, height=20, width=90)
        self.textbox2.grid(row=6, column=1, columnspan=2)
        self.textbox2.insert(tk.END, "Phrases")
        self.textbox2.config(state=tk.DISABLED,
                             background="white",
                             foreground="black",
                             font=("Helvetica", 11),
                             borderwidth=2,
                             )

        # output box to display the result
        self.textbox = tk.Text(self.master, height=20, width=90)
        self.textbox.grid(row=8, column=1, columnspan=2)
        self.textbox.insert(tk.END, "Output")
        self.textbox.config(state=tk.DISABLED,
                            background="white",
                            foreground="black",
                            font=("Helvetica", 11),
                            borderwidth=2,
                            )
        
       


        #BUTTONS
        #button under url box named "Get paper"
        tk.Button(self.master, text='Get paper', command=self.get_paper).grid(row=4, column=0)

        tk.Button(self.master, text='Reset usage', command=self.reset_token_usage).grid(row=10, column=0, sticky=tk.W)                     

        tk.Button(self.master, text="Generate keywords from question", command=self.search_keywords).grid(row=4,
                                                                                          column=1, columnspan=2)

        self.boolean2 = tk.IntVar()
        self.boolean2.set(0)
        self.check_phrase = tk.Checkbutton(self.master, text="(Expensive)Check phrases for relevance", variable=self.boolean2).grid(row=9, 
                                                                                                     column=1, 
                                                                                                     sticky=tk.E)
        

        tk.Button(self.master, text='Run', command=self.run).grid(row=10,
                                                                  column=1,
                                                                  pady=4,
                                                                  sticky=tk.E)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=10,
                                                                    column=2,
                                                                    pady=4,
                                                                    sticky=tk.W)


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

    def get_paper(self):
        """ Get the paper from the url """
        url = self.url.get()  # get the url from the entry box
        tex_files,bibfiles = functions.getPaper(url)  # get the paper from arxiv
        print('tex_files found:', tex_files)
        self.complete_text = functions.extract_all_text(tex_files)  # extract the text from the paper
        self.bib_text = functions.extract_all_text(bibfiles)  # extract the text from the bib file
        print('bib_text found:', bibfiles)
        header = functions.getTitleOfthePaper(url) #get the title of the paper
        self.papertitle.set(header)  # set the papertitle label
        self.last_url = url  # save the last url
        #find section and subsection of the paper
        list_of_section = functions.get_sections(tex_files)
        list_of_section = functions.remove_duplicates(list_of_section, simplecase=True)
        print(list_of_section)
        self.sections.delete(1.0, tk.END)
        interlink = Interlink(self.sections, self.keybox, self.question)
        for i in list_of_section:
            self.sections.insert(tk.END, i)
            # apply the hyperlinks to the phrases
            self.sections.highlight_pattern(i,interlink)
        
        

    def search_keywords(self):
        api_key = self.apikey.get()
        question = self.question.get("1.0", tk.END)
        keywords, tokens, model = functions.promptText_keywords(question, api_key)
        self.update_token_usage(tokens, model)
        keywords = keywords.strip().strip('\n') #remove the newline character from the keywords
        # show keywords in the output box
        self.keybox.config(state=tk.NORMAL)
        # clear keybox
        self.keybox.delete(1.0, tk.END)  # clear the output box
        self.keybox.insert(tk.END, keywords)  # insert keywords in the keybox
        print('Keywords to use:', repr(keywords))
        return keywords

    def run(self):
        api_key = self.apikey.get()  # get the api key from the entry box
        question = self.question.get("1.0", tk.END)  # get the question from the entry box

        if self.last_url != self.url.get():  # if the url has changed
            self.get_paper()  # download the paper
        #TODO: apply the hyperlinks to the papertitle label, first change to a custom textbox
        
        #HANDLE THE KEYWORDS
        keywords = self.keybox.get("1.0", tk.END).strip()  # get the keywords from the output box        
        if keywords == '':  # if the keywords are not provided, promt GPT to generate them from the question
            keywords = self.search_keywords()
        print('Keywords in use:',keywords)

        # Get list_of_phrases from the text
        list_of_phrases = []
        number_of_phrases = 0
        
        for keyword in keywords.split(','):  # loop through the keywords
            phrase, stop, number_of_phrases = functions.extract_phrases(keyword.strip(), self.complete_text, api_key, number_of_phrases)
            
            if phrase is not None:
                list_of_phrases.extend(phrase)
                number_of_phrases = len(list_of_phrases)
                print('For keyword \'' + keyword + '\' the phrases found are:', len(phrase))
            else:
                print('For keyword \'' + keyword + '\' no phrase found')
                # # try lower case TODO: Improve lower/upper/plural/singular handling all in once
                    
            if stop:
                break  # if the stop flag is set, break the loop
      
        # print('Phrases (',len(list_of_phrases),')',list_of_phrases)

        # Initialize the textbox to receive the generated text
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete(1.0, tk.END)

        if len(list_of_phrases) > 0: #if there are phrases!
            
            #print('list_of_phrases',list_of_phrases)
            # Here the code check if the user wants to use the check for relevance of each phrase,
            # otherwise it will just order phrases by most common according to keywords appearance
            # and limit the number to PHRASES_TO_USE (defined in functions.py)
            if self.boolean2.get() == 1: 
                askGPT3 = True
            else:
                askGPT3 = False
            list_of_phrases = functions.connect_adjacent_phrases(list_of_phrases) 
            clean_list_of_phrases, tokens, model = functions.check_relevance(list_of_phrases,question,api_key,askGPT3)
            self.update_token_usage(tokens, model) #update the token usage
            
            just_phrases = []
            phrase_with_frequency = []
            for phrase in clean_list_of_phrases:
                just_phrases.append(phrase[0])
                phrase_with_frequency.append('('+str(phrase[1])+')'+phrase[0])

            #substitue in the phrases the \cite with the hyperlink to arxiv
            phrase_with_frequency, all_hyperlinks = functions.get_hyperlink(phrase_with_frequency, self.complete_text+self.bib_text)

            
            # show the phrases in the output box
            self.textbox2.config(state=tk.NORMAL)
            self.textbox2.delete('1.0', tk.END)  # clear the output box
            self.textbox2.insert(tk.END, '-'+'\n-'.join(phrase_with_frequency))  # insert phrases in the textbox
            
            # apply the hyperlinks to the phrases
            hyperlink = HyperlinkManager(self.textbox2, self.url)
            for link in all_hyperlinks:
                self.textbox2.highlight_pattern(link,hyperlink)
  
            for k,keyword in enumerate(keywords.split(',')):
                print(COLOR_LIST[k%len(COLOR_LIST)])
                self.textbox2.highlight_pattern(keyword, tag=COLOR_LIST[k%len(COLOR_LIST)])
            self.textbox2.config(state=tk.DISABLED)
            
            # MOST IMPORTANT STEP, ASK GPT-3 TO GIVE THE ANSWER
            try:
                if 'Summarize' in question:
                    result, tokens, model = functions.promptText_question(question, just_phrases, self.papertitle.get(), api_key) #ask GPT-3 to give the answer
                else:
                    result, tokens, model = functions.promptText_question2(question, just_phrases, self.papertitle.get(), api_key) #ask GPT-3 to give the answer
                self.update_token_usage(tokens, model) #update the token usage
                self.textbox.insert(tk.END, result)  # insert the answer in the output box
                self.textbox.config(background="green") # change the background color of the output box
                self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
            except Exception as e:
                self.textbox.insert(tk.END, 'Error: ' + str(e))
                self.textbox.config(background="red") # change the background color of the output box
                self.textbox.after(400, lambda: self.textbox.config(background="white")) # reset the background color after 200ms
            
        else:
            self.textbox.insert(tk.END, 'No phrases found in the paper matching the keywords. Try different keywords.')
        self.textbox.config(state=tk.DISABLED)




root = tk.Tk()
root.title("ArXiv Paper Genie: Q&A Tool with OpenAI GPT-3")
root.geometry("1500x800")
root.columnconfigure(3) 
root.bind_class("Entry", "<<Paste>>", custom_paste)
root.grid_columnconfigure(0, weight=1) 
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
app = Application(master=root)
app.mainloop()
