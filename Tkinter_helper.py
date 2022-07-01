import tkinter as tk
import webbrowser 
from functools import partial

#UTILITIES for INTERFACE

def custom_paste(event):
        try:
            event.widget.delete("sel.first", "sel.last")
        except:
            pass
        event.widget.insert("insert", event.widget.clipboard_get())
        return "break"

class CustomText(tk.Text):
    '''A text widget with a new method, highlight_pattern()
    '''
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

    def highlight_pattern(self, pattern, hyperlink, start="1.0", end="end",
                          regexp=False):
        '''Apply the hyperlink to all text that matches the given pattern

        If 'regexp' is set to True, pattern will be treated as a regular
        expression according to Tcl's regular expression syntax.
        '''

        start = self.index(start)
        end = self.index(end)
        self.mark_set("matchStart", start)
        self.mark_set("matchEnd", start)
        self.mark_set("searchLimit", end)

        count = tk.IntVar()
        while True:
            index = self.search(pattern, "matchEnd","searchLimit",
                                count=count, regexp=regexp) 
            if index == "": break
            if count.get() == 0: break # degenerate pattern which matches zero-length strings
            self.mark_set("matchStart", index)
            self.mark_set("matchEnd", "%s+%sc" % (index, count.get()))
            #self.tag_add(tag, "matchStart", "matchEnd")
            self.replace("matchStart", "matchEnd",pattern, hyperlink.add(pattern))
            

class HyperlinkManager:

    def __init__(self, text, urlbox):

        self.text = text
        self.target_box = urlbox
        self.text.tag_config("hyper", foreground="blue", underline=1) #hyperlink color

        self.text.tag_bind("hyper", "<Enter>", self._enter) #mouse over hyperlink
        self.text.tag_bind("hyper", "<Leave>", self._leave) #mouse leave hyperlink
        self.text.tag_bind("hyper", "<Button-1>", self._click) #click hyperlink
        self.text.tag_bind("hyper", "<Button-3>", self._copy_in_urlbox) #click hyperlink

        self.reset()

    def reset(self):
        self.links = {}
        self.urls = {}

    def add(self, pattern):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "hyper-%d" % len(self.links) # use len(links) to get a unique number
        self.links[tag] = partial(webbrowser.open, pattern)
        self.urls[tag] = pattern
        return "hyper", tag

    def _enter(self, event):
        self.text.config(cursor="hand1") # this show a hand cursor when the mouse is over a hyperlink

    def _leave(self, event):
        self.text.config(cursor="") # this reset cursor when leave

    def _click(self, event): 
        for tag in self.text.tag_names(tk.CURRENT):
            if tag[:6] == "hyper-":
                self.links[tag]() # call associated action, opening the hyperlink
                return
    def _copy_in_urlbox(self, event):
        for tag in self.text.tag_names(tk.CURRENT):
            if tag[:6] == "hyper-":
                self.target_box.delete(0, tk.END)  # CHECK which type is targetbox. if entry -, if custom box then is 1.0
                self.target_box.insert(tk.END, self.urls[tag]) # insert the hyperlink in the output box
                self.target_box.config(background="green") # change the background color of the output box
                self.target_box.after(200, lambda: self.target_box.config(background="white")) # reset the background color after 200ms
                return
class Interlink(HyperlinkManager):
      def add(self, pattern):
        # add an action to the manager.  returns tags to use in
        # associated text widget
        tag = "hyper-%d" % len(self.links) # use len(links) to get a unique number
        self.links[tag] = self._copy_in_keywords
        self.urls[tag] = pattern
        self.text.tag_bind("hyper", "<Button-3>", self._enter) #click hyperlink
        return "hyper", tag
      def _copy_in_keywords(self):
        for tag in self.text.tag_names(tk.CURRENT):
            if tag[:6] == "hyper-":
                self.target_box.delete(1.0 , tk.END)
                self.target_box.insert(tk.END, self.urls[tag].strip('\t'))
                self.target_box.config(background="green")
                self.target_box.after(200, lambda: self.target_box.config(background="white"))