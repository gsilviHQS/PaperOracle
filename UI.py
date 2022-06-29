#! /usr/bin/env python
import tkinter as tk 
import os

#MY FUNCTIONS
import functions
from Tkinter_helper import CustomText, custom_paste





default_url = 'https://arxiv.org/abs/2201.08194v1'
default_question = 'what are noisy intermediate-scale quantum devices?'


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="API Key").grid(row=0)
        self.dollars = tk.DoubleVar()
        self.dollars.set(0.0)
        self.token_usage = tk.IntVar()
        self.token_usage.set(0)
        self.token_label = tk.StringVar()
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')
        tk.Label(self.master, textvariable = self.token_label).grid(row=0, column=2 , sticky=tk.E)
        tk.Label(self.master, text="arXiv URL").grid(row=1)
        tk.Label(self.master, text="Paper title").grid(row=2)
        tk.Label(self.master, text="Question").grid(row=3)
        tk.Label(self.master, text="Keywords to search\n(separated by comma)").grid(row=5)

     
        tk.Label(self.master, text="Answer from GPT-3").grid(row=6)
        tk.Label(self.master, text="Matching Phrases \n in tex files").grid(row=7)

        self.papertitle = tk.StringVar()
        self.papertitle.set('\n')
        tk.Label(self.master, textvariable=self.papertitle, wraplength=500).grid(row=2, column=1)

        self.apikey = tk.Entry(self.master, width=30)

        # if api.txt exist then insert the content of api.txt into apikey entry else insert default value
        if os.path.isfile('API.txt'):
            with open('API.txt', 'r') as f:
                self.apikey.insert(0, f.read())
        else:
            self.apikey.insert(0, 'Your API Key here')
            #add button to save the api key
            tk.Button(self.master, text='Save API Key', command=self.save_api_key).grid(row=0, column=2, sticky=tk.W)

        
        
        self.url = tk.Entry(self.master, width=50)
        self.url.insert(0, default_url)
        self.question = tk.Entry(self.master, width=50)
        self.question.insert(0, default_question)

        self.apikey.grid(row=0, column=1)
        self.url.grid(row=1, column=1)
        self.question.grid(row=3, column=1)

        self.keybox = tk.Text(self.master, width=50, height=1)
        self.keybox.grid(row=5, column=1)
        # self.keybox.config(state=tk.DISABLED)

        # output box to display the result
        self.textbox = tk.Text(self.master, height=20, width=90)
        self.textbox.grid(row=6, column=1, columnspan=2)
        self.textbox.insert(tk.END, "Output")
        self.textbox.config(state=tk.DISABLED,
                            background="white",
                            foreground="black",
                            font=("Helvetica", 11),
                            borderwidth=2,
                            )
        
        # new textbox for the phrases matching the question
        self.textbox2 = CustomText(self.master, height=20, width=90)
        self.textbox2.grid(row=7, column=1, columnspan=2)
        self.textbox2.insert(tk.END, "Phrases")
        self.textbox2.config(state=tk.DISABLED,
                             background="white",
                             foreground="black",
                             font=("Helvetica", 11),
                             borderwidth=2,
                             )

        # configuring a tag with a certain style (font color)
        self.textbox2.tag_configure("blue", foreground="blue")



        #add button next to token usage to reset the valuef of token usage and dollars usage
        tk.Button(self.master, text='Reset usage', command=self.reset_token_usage).grid(row=1, column=2, sticky=tk.E)                     

        tk.Button(self.master, text="Generate keywords from question", command=self.search_keywords).grid(row=4,
                                                                                          column=1)

        self.boolean2 = tk.IntVar()
        self.boolean2.set(0)
        self.check_phrase = tk.Checkbutton(self.master, text="(Expensive)Check phrases for relevance", variable=self.boolean2).grid(row=8, 
                                                                                                     column=2, 
                                                                                                     sticky=tk.W)
        

        tk.Button(self.master, text='Run', command=self.run).grid(row=8,
                                                                  column=1,
                                                                  pady=4)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=9,
                                                                    column=1,
                                                                    pady=4)


    def reset_token_usage(self):
        self.token_usage.set(0)
        self.token_label.set('Usage: '+str(self.token_usage.get())+' tokens')
        self.dollars.set(0.0)

    def save_api_key(self):
        api_key = self.apikey.get()
        with open('API.txt', 'w') as f:
            f.write(api_key)

    def update_token_usage(self,tokens, model):
        total_token_used = self.token_usage.get() #get the current token usage
        total_dollars_used = self.dollars.get() #get the current dollars usage
        
        total_token_used += tokens #add the tokens used to the total token usage
        self.token_usage.set(total_token_used) #update the token usage

        if model == 'text-davinci-002': #if the model is davinci
            dollars = tokens * 0.00006
        elif model == 'text-babbage-001': #if the model is babbage
            dollars = tokens * 0.0000012
        else:
            dollars = 0
        total_dollars_used += dollars #add the dollars used to the total dollars usage
        self.dollars.set(total_dollars_used) #update the dollars usage

        self.token_label.set('Usage: '+str(total_token_used)+' tokens ($'+"{:3.5f}".format(total_dollars_used)+')') #update the token usage label


    def search_keywords(self):
        api_key = self.apikey.get()
        question = self.question.get()
        keywords, tokens, model = functions.promptText_keywords(question, api_key)
        self.update_token_usage(tokens, model)
       
        # show keywords in the output box
        self.keybox.config(state=tk.NORMAL)
        self.keybox.delete('1.0', tk.END)  # clear the output box
        self.keybox.insert(tk.END, keywords.strip('\n'))  # insert keywords in the keybox
        return keywords.strip('\n')

    def run(self):
        api_key = self.apikey.get()  # get the api key from the entry box
        question = self.question.get()  # get the question from the entry box

        #HANDLE THE PAPER
        url = self.url.get()  # get the url from the entry box
        tex_files = functions.getPaper(url)  # get the paper from arxiv
        print('tex_files found:', tex_files)
        complete_text = functions.extract_all_text(tex_files)  # extract the text from the paper
        header = functions.getTitleOfthePaper(url) #get the title of the paper
        self.papertitle.set(header)  # set the papertitle label
        
        #HANDLE THE KEYWORDS
        keywords = self.keybox.get("1.0", tk.END).strip()  # get the keywords from the output box in lower case        
        if keywords == '':  # if the keywords are not provided, promt GPT to generate them from the question
            keywords = self.search_keywords()
        print('Keywords to use:', keywords)

        # Get list_of_phrases from the text
        list_of_phrases = []
        number_of_phrases = 0
        
        for keyword in keywords.split(','):  # loop through the keywords
            phrase, stop, number_of_phrases = functions.extract_phrases(keyword.strip(), complete_text, api_key, number_of_phrases)
            
            if phrase is not None:
                list_of_phrases.extend(phrase)
                number_of_phrases = len(list_of_phrases)
                print('For keyword \'' + keyword + '\' the phrase found are:', len(phrase))
            else:
                # try lower case TODO: Improve lower/upper/plural/singular handling all in once
                lowercase_keyword = keyword.strip().lower()
                if lowercase_keyword != keyword.strip():
                    phrase_lower, stop, number_of_phrases = functions.extract_phrases(lowercase_keyword, complete_text, api_key, number_of_phrases)  # try lower case
                    if phrase_lower is not None:
                        list_of_phrases.append(".\n".join(phrase_lower))
                        print('For keyword \'' + lowercase_keyword + '\' the phrase found are:', phrase_lower)
                else:
                    print('For keyword \'' + keyword + '\' no phrase found')
            if stop:
                break  # if the stop flag is set, break the loop
      
        # print('Phrases (',len(list_of_phrases),')',list_of_phrases)

        # Initialize the textbox to receive the generated text
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete(1.0, tk.END)

        if len(list_of_phrases) > 0: #if there are phrases!
            
            #print('list_of_phrases',list_of_phrases)
            #CHECK if the user wants to use the check for relevance of each phrase,
            # otherwise it will just order phrases by most common according to keywords appearance
            # and limit the number to PHRASES_TO_USE (defined in functions.py)
            if self.boolean2.get() == 1: 
                askGPT3 = True
            else:
                askGPT3 = False
            clean_list_of_phrases, tokens, model = functions.check_relevance(list_of_phrases,question,api_key,askGPT3)
            self.update_token_usage(tokens, model) #update the token usage
            
            just_phrases = []
            phrase_with_frequency = []
            for phrase in clean_list_of_phrases:
                just_phrases.append(phrase[0])
                phrase_with_frequency.append('('+str(phrase[1])+')'+phrase[0])

            #substitue in the phrases the \cite with the hyperlink to arxiv
            phrase_with_frequency, all_hyperlinks = functions.get_hyperlink(phrase_with_frequency, complete_text)

            
            # show the phrases in the output box
            self.textbox2.config(state=tk.NORMAL)
            self.textbox2.delete('1.0', tk.END)  # clear the output box
            self.textbox2.insert(tk.END, '-'+'\n-'.join(phrase_with_frequency))  # insert phrases in the textbox
            self.textbox2.config(state=tk.DISABLED)
            # apply the tag "blue" 
            for link in all_hyperlinks:
                self.textbox2.highlight_pattern(link, "blue")
            
            
            # MOST IMPORTANT STEP, ASK GPT-3 TO GIVE THE ANSWER
            try:
                result, tokens, model = functions.promptText_question(question, '-'+'\n-'.join(just_phrases), header, api_key) #ask GPT-3 to give the answer
                self.update_token_usage(tokens, model) #update the token usage
                self.textbox.insert(tk.END, result)  # insert the answer in the output box
            except Exception as e:
                self.textbox.insert(tk.END, 'Error: ' + str(e))
            
        else:
            self.textbox.insert(tk.END, 'No phrases found in the paper matching the keywords. Try different keywords.')
        self.textbox.config(state=tk.DISABLED)




root = tk.Tk()
root.title("ArXiv Paper Genie: Q&A Tool with OpenAI GPT-3")
root.geometry("1000x800")
root.columnconfigure(3)
root.bind_class("Entry", "<<Paste>>", custom_paste)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
app = Application(master=root)
app.mainloop()
