#! /usr/bin/env python
import tkinter as tk 

import functions
import os

default_url = 'https://arxiv.org/abs/2201.08194v1'
default_question = 'What is the weak barren plateau condition?'


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="API Key").grid(row=0)
        tk.Label(self.master, text="arXiv URL").grid(row=1)
        tk.Label(self.master, text="Question").grid(row=2)
        tk.Label(self.master, text="Keywords to search").grid(row=3)
        tk.Label(self.master, text="Paper").grid(row=5)
        tk.Label(self.master, text="Answer from GPT-3").grid(row=6)
        tk.Label(self.master, text="Matching Phrases \n in tex files").grid(row=7)

        self.papertitle = tk.StringVar()
        self.papertitle.set('\n')
        tk.Label(self.master, textvariable=self.papertitle, wraplength=500).grid(row=5, column=1)

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
        self.question.grid(row=2, column=1)

        self.keybox = tk.Text(self.master, width=50, height=1)
        self.keybox.grid(row=4, column=1)
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
        self.textbox2 = tk.Text(self.master, height=20, width=90)
        self.textbox2.grid(row=7, column=1, columnspan=2)
        self.textbox2.insert(tk.END, "Phrases")
        self.textbox2.config(state=tk.DISABLED,
                             background="white",
                             foreground="black",
                             font=("Helvetica", 11),
                             borderwidth=2,
                             )

        tk.Button(self.master, text="Search keywords from question", command=self.search_keywords).grid(row=3,
                                                                                          column=1)
        #add boolean variable 
        self.boolean = tk.IntVar()
        self.boolean.set(0)
        #add checkbox below search keywords button to ask for synonims
        self.checkbox = tk.Checkbutton(self.master, text="and synonyms", variable=self.boolean).grid(row=3, 
                                                                                                     column=2, 
                                                                                                     sticky=tk.W)
        self.boolean2 = tk.IntVar()
        self.boolean2.set(0)
        self.check_phrase = tk.Checkbutton(self.master, text="Check phrases for relevance", variable=self.boolean2).grid(row=4, 
                                                                                                     column=2, 
                                                                                                     sticky=tk.W)
        

        tk.Button(self.master, text='Run', command=self.run).grid(row=8,
                                                                  column=1,
                                                                  pady=4)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=9,
                                                                    column=1,
                                                                    pady=4)
    def save_api_key(self):
        api_key = self.apikey.get()
        with open('API.txt', 'w') as f:
            f.write(api_key)

    def search_keywords(self):
        api_key = self.apikey.get()
        question = self.question.get()
        # print value of boolean variable
        if self.boolean.get() == 1:
            keywords = functions.promptText_keywords(question, api_key, True).strip('\n')
        else:
            keywords = functions.promptText_keywords(question, api_key).strip('\n')
        # show keywords in the output box
        self.keybox.config(state=tk.NORMAL)
        self.keybox.delete('1.0', tk.END)  # clear the output box
        self.keybox.insert(tk.END, keywords)  # insert keywords in the keybox
        return keywords

    def run(self):
        api_key = self.apikey.get()  # get the api key from the entry box
        question = self.question.get()  # get the question from the entry box
        url = self.url.get()  # get the url from the entry box

        tex_files = functions.getPaper(url)  # get the paper from arxiv
        print('tex_files:', tex_files)
        self.papertitle.set(functions.getTitleOfthePaper(url))  # set the title of the paper label from the url

        keywords = self.keybox.get("1.0", tk.END).strip()  # get the keywords from the output box in lower case        
        if keywords == '':  # if the keywords are not provided, promt GPT to generate them from the question
            keywords = self.search_keywords()

        print('Keywords to use:', keywords)
        # get list_of_phrases from the text
        list_of_phrases = []
        number_of_phrases = 0
        complete_text = functions.extract_all_text(tex_files)
        for keyword in keywords.split(','):  # loop through the keywords
            phrase, stop, number_of_phrases = functions.extract_phrases(keyword.strip(), complete_text, question,  api_key, number_of_phrases)
            
            if phrase is not None:
                list_of_phrases.extend(phrase)
                number_of_phrases = len(list_of_phrases)
                print('For keyword \'' + keyword + '\' the phrase found are:', len(phrase))
            else:
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
        # relevance = promptText_relevance(question, sentence, api_key)


        if self.boolean2.get() == 1: 
            askGPT3 = True
        else:
            askGPT3 = False
        clean_list_of_phrases = functions.check_relevance(list_of_phrases,question,api_key,askGPT3)
        just_phrases = []
        phrase_with_frequency = []
        for phrase in clean_list_of_phrases:
            just_phrases.append(phrase[0])
            phrase_with_frequency.append('('+str(phrase[1])+')'+phrase[0])
        


        # print('Phrases (',len(list_of_phrases),')',list_of_phrases)
        self.textbox.config(state=tk.NORMAL)
        self.textbox.delete(1.0, tk.END)
        if len(just_phrases) > 0:
            list_of_phrases = '-'+'\n-'.join(just_phrases)
            print('list_of_phrases',list_of_phrases)

            # show the phrases in the output box
            self.textbox2.config(state=tk.NORMAL)
            self.textbox2.delete('1.0', tk.END)  # clear the output box
            self.textbox2.insert(tk.END, '-'+'\n-'.join(phrase_with_frequency))  # insert phrases in the textbox
            self.textbox2.config(state=tk.DISABLED)
            header = functions.getTitleOfthePaper(url)
            try:
                result = functions.promptText_question(question, list_of_phrases, header, api_key)
                self.textbox.insert(tk.END, result['choices'][0]['text'])  # insert the answer in the output box
            except Exception as e:
                self.textbox.insert(tk.END, 'Error: ' + str(e))
            
        else:
            if askGPT3:
                self.textbox.insert(tk.END, 'No relevant phrases found in the paper matching the keywords. Try different keywords or untick "Check phrases for relevance"')
            else:
                self.textbox.insert(tk.END, 'No phrases found in the paper matching the keywords. Try different keywords.')
        self.textbox.config(state=tk.DISABLED)


root = tk.Tk()
root.title("ArXiv Paper Answerin Machine with GPT-3 OpenAI")
root.geometry("1000x800")
root.columnconfigure(3)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
app = Application(master=root)
app.mainloop()
