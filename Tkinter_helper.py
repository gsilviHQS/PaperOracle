import tkinter as tk
import webbrowser 
from functools import partial


#UTILITIES for INTERFACE

COLOR_LIST = ["red","cyan","green","magenta","orange","pink","brown"]

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
        self.tag_configure("red", foreground="#ff0000")
        self.tag_configure("blue", foreground="#0000ff")
        self.tag_configure("green", foreground="#00ff00")
        self.tag_configure("yellow", foreground="#ffff00")
        self.tag_configure("cyan", foreground="#00ffff")
        self.tag_configure("magenta", foreground="#ff00ff")
        self.tag_configure("black", foreground="#000000")
        self.tag_configure("white", foreground="#ffffff")
        self.tag_configure("gray", foreground="#808080")
        self.tag_configure("lightgray", foreground="#c0c0c0")
        self.tag_configure("darkgray", foreground="#404040")


    def highlight_pattern(self, pattern, hyperlink=None,tag=None, start="1.0", end="end",
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
            if tag is not None:
                self.tag_add(tag, "matchStart", "matchEnd")
            if hyperlink is not None:
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
                self.target_box.config(background="blue") # change the background color of the output box
                self.target_box.after(200, lambda: self.target_box.config(background="white")) # reset the background color after 200ms
                return
class Interlink(HyperlinkManager):
    def __init__(self, text, keybox, questionbox):
        super().__init__(text, keybox)
        self.questionbox = questionbox
        self.text.tag_config("hyper", foreground="green", underline=1)
        self.text.tag_bind("hyper", "<Button-3>", self._copy_in_keywords) #override the default copy in urlbox from super().__init__
    def add(self, pattern):
        # add an action to the manager, copying the pattern to keywords box
        tag = "hyper-%d" % len(self.links) # use len(links) to get a unique number
        self.links[tag] = self._copy_in_keywords
        self.urls[tag] = pattern
        
        return "hyper", tag
    def _copy_in_keywords(self, event=None):
        for tag in self.text.tag_names(tk.CURRENT):
            if tag[:6] == "hyper-":
                self.target_box.delete(1.0 , tk.END)
                self.target_box.insert(tk.END, self.urls[tag].strip('\t'))
                self.target_box.config(background="green")
                self.target_box.after(200, lambda: self.target_box.config(background="white"))
                if event is None:
                    self.questionbox.delete(1.0, tk.END)
                    self.questionbox.insert(tk.END, "Summarize")
                    self.questionbox.config(background="green")
                    self.questionbox.after(200, lambda: self.questionbox.config(background="white"))

class RightClicker: # Right clicker class
    def __init__(self, event): # Initialize the right clicker
        right_click_menu = tk.Menu(None, tearoff=0, takefocus=0) # takefocus=0 to avoid the menu to be closed when the mouse is over it, tearoff=0 to avoid the menu to be displayed as a separate window

        for txt in ['Cut', 'Copy', 'Paste']: # Add the commands to the right click menu
            right_click_menu.add_command( # Add the commands to the right click menu
                label=txt, command=lambda event=event, text=txt: #e
                self.right_click_command(event, text)) # Add the commands to the right click menu

        right_click_menu.tk_popup(event.x_root + 40, event.y_root + 10, entry='0')
        # to keep the menou open, we need to add the following line
        # entry='0' to keep the menu open
        # entry='1' to close the menu when the mouse is over it
        # entry='2' to close the menu when the mouse is over it and the mouse button is released
        # entry='3' to close the menu when the mouse is over it and the mouse button is released

    def right_click_command(self, event, cmd):
        event.widget.event_generate(f'<<{cmd}>>')