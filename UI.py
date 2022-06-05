import tkinter as tk 

import functions
import os

class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        #self.pack()
        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.master, text="API Key").grid(row=0)
        tk.Label(self.master, text="arXiv URL").grid(row=1)
        tk.Label(self.master, text="Question").grid(row=2)
        tk.Label(self.master, text="Keywords to search").grid(row=3)
        tk.Label(self.master, text="Answer").grid(row=4)



        self.apikey = tk.Entry(self.master, width=30 )
        #add default value to apikey entry
        #if api.txt exist then insert the content of api.txt into apikey entry else insert default value
        if os.path.isfile('API.txt'):
            with open('API.txt', 'r') as f:
                self.apikey.insert(0, f.read())
        else:
            self.apikey.insert(0, 'Your API Key')
        
        self.url = tk.Entry(self.master, width=50)
        self.url.insert(0, "http://arxiv.org/abs/2002.12902")
        self.question = tk.Entry(self.master, width=50)
        self.question.insert(0, "How many qubits are used and which type?")

        self.apikey.grid(row=0, column=1)
        self.url.grid(row=1, column=1)
        self.question.grid(row=2, column=1) 

        #add an output box for the keywords to be shown in 
        self.keybox = tk.Text(self.master, width=50, height=1)
        self.keybox.grid(row=3, column=1)
        #self.keybox.config(state=tk.DISABLED)



        #add an output box to display the result
        self.textbox = tk.Text(self.master, height=20, width=60)
        self.textbox.grid(row=4, column=1, columnspan=1)
        self.textbox.insert(tk.END, "Output")
        self.textbox.config(state=tk.DISABLED)
        self.textbox.config(background="white")
        self.textbox.config(foreground="black")
        self.textbox.config(font=("Helvetica", 12))
        self.textbox.config(borderwidth=2)
        #self.textbox.config(highlightbackground="black")

        self.textbox.config(highlightthickness=2)
        self.textbox.config(insertbackground="black")
        self.textbox.config(insertwidth=2)
        self.textbox.config(selectbackground="black")

        tk.Button(self.master, text="Search keywords", command=self.search_keywords).grid(row=3, 
                                                                                          column=2,
                                                                                          sticky=tk.W)

        tk.Button(self.master, text='Run', command=self.run).grid(row=5, 
                                                                  column=1,
                                                                  pady=4)
        tk.Button(self.master, text='Quit', command=self.quit).grid(row=6, 
                                                                    column=1,
                                                                    pady=4)
    def search_keywords(self):
        api_key = self.apikey.get()
        question = self.question.get()
        keywords = functions.promptText_keywords(question, api_key)
        #show keywords in the output box
        print(type(keywords))
        self.keybox.config(state=tk.NORMAL)
        self.keybox.delete('1.0', tk.END) # clear the output box
        #insert keywords in the output box
        self.keybox.insert(tk.END, keywords.strip('\n')) 

    def run(self):
        api_key = self.apikey.get()
        question = self.question.get()
        url = self.url.get()
        print(question, url)

        texfilename = functions.getPaper(url)
        print(texfilename)
        # list_of_sections = functions.extract_section_and_subsections(functions.get_sections(texfilename),texfilename)

        keywords = self.keybox.get("1.0", tk.END).strip().split(',') # get the keywords from the output box


        # get phrases from the text
        phrases = []
        """ for keyword in keywords:
            print('Keyword', keyword)
            for section in list_of_sections:
                phrase = functions.extract_phrases(keyword, section)
                print(phrase)
                if phrase is not None:
                    phrases.append(phrase) """
        for keyword in keywords:
            print('Keyword', keyword)
            phrase = functions.extract_phrases(keyword, functions.extract_all_text(texfilename))
            print(phrase)
            if phrase is not None:
                phrases.append(".\n".join(phrase))
        phrases = ".\n".join(phrases)

        #print('Phrases',phrases, len(phrases))

        if len(phrases)>0:
            result = functions.promptText_question(question,phrases,api_key)
            #print result in self.textbox
            self.textbox.config(state=tk.NORMAL)
            self.textbox.delete(1.0,tk.END)
            self.textbox.insert(tk.END, result['choices'][0]['text'])
            self.textbox.config(state=tk.DISABLED)
        else:
            self.textbox.config(state=tk.NORMAL)
            self.textbox.delete(1.0,tk.END)
            self.textbox.insert(tk.END, 'No answer found')
            self.textbox.config(state=tk.DISABLED)


root = tk.Tk()
root.title("ArXiv Question Answering with GPT-3 OpenAI")
root.geometry("800x500")
root.columnconfigure(3)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=1)
app = Application(master=root)
app.mainloop()