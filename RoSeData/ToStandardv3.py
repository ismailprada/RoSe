#!/usr/bin/env python3

# Written by Ismail Prada
# March 2017 (Version 3: July 2017)

# New in Version 3:
# Implemented in Tkinter

import csv
import lxml.etree as et
import re
import os
import sys
import webbrowser
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

csv.field_size_limit(sys.maxsize)

class ToStandard():
    def __init__(self):
        self.root = Tk()
        self.root.focus_force()
        self.root.title("Webanno-Standard-Konversion")
        
        self._inWebAnno = StringVar(self.root, value="Hier Pfad zu Webanno-TSV-Datei eingeben")
        Entry(self.root, textvariable=self._inWebAnno, width=50).grid(columnspan=2, padx=10, pady=10)
        Button(self.root, text="Datei wählen", command= lambda x="webanno": self._set_file(x)).grid(row=0, column=2, padx=10)
        
        self._indir = StringVar(self.root, value="Hier Pfad zu Standard-XML-Datei eingeben")
        Entry(self.root, textvariable=self._indir, width=50).grid(columnspan=2, padx=10, pady=10)
        Button(self.root, text="Datei wählen", command= lambda x="standard": self._set_file(x)).grid(row=1, column=2, padx=10)

        Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)
        
        self.mode = StringVar(self.root, "Überschreiben")
        
        Label(self.root, text="Modus:").grid(row=3, column=0, sticky=W+E)
        option_box = OptionMenu(self.root, self.mode, "Überschreiben",
            "Nur Veränderte ersetzen (Benötigt ID)", "Anhängen")
        option_box.grid(row=3, column=1, columnspan=2, sticky=W+E)
        
        Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)

        tag_btn = Button(self.root, text="Starte Konversion", relief=RAISED, command=self.go).grid(columnspan=3, sticky=W+E, pady=5, padx=5)
        #tag_btn = Button(self.root, text="Finde Attribute", relief=RAISED, command=self.scan).grid(row=7, column=1, sticky=W+E, pady=10, padx=5)
        
        Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)
        
        self._info = StringVar(self.root, value="")
        Message(self.root, textvariable=self._info, width=500).grid(columnspan=3, pady=10)
        self._info2 = StringVar(self.root, value="")
        Message(self.root, textvariable=self._info2, width=500).grid(columnspan=3, pady=10)

        mainloop()
        
    def _set_file(self, inf):
        if inf == "standard":
            dirname = filedialog.askopenfilename(filetypes=[("XML files","*.xml")])
        else:
            dirname = filedialog.askopenfilename(filetypes=[("Webanno TSV files","*.tsv")])
        if dirname:
            if inf == "standard":
                self._indir.set(dirname)
            else:
                self._inWebAnno.set(dirname)
                
    def go(self):
        try:
            with open(self._inWebAnno.get(),mode="r",encoding="utf8")as f:
                phrasedict = {}
                tsvreader = csv.reader(f, delimiter='\t', quoting=csv.QUOTE_NONE)
                for row_num, row in enumerate(tsvreader):
                    if row_num == 0:
                        header = row # save the header
                    elif len(row) > 0 and row[0].startswith("#id="):
                        new_id = re.findall("\d+",row[0])[0] # get id
                    elif len(row) > 0 and row[0].startswith("#text="):
                        phrasedict[int(new_id)] = [re.sub("#text=","",row[0]),[]]
                    elif len(row) > 0:
                        phrasedict[int(new_id)][1].append(row)
        except:
            messagebox.showerror(title="Datei nicht gefunden", message="Bitte gib einen gültigen Pfad zu deiner Webanno-TSV-Datei an.")
            return None
        # read the header to mark positions of attributes
        header_list = header[0].split(" # ")
        header_dict = {} # Attribute : index
        for num, attr in enumerate(header_list):
            if len(attr) > 0: # ignore empty fields
                attr_name = re.findall('(?<=\.)\w+(?= \|)',attr)
                if attr_name[0] == 'Dependency':
                    depRel = re.findall('(?<=\| )\w+(?= \|)',attr)
                    depRel[0] = 'dep_parent'
                    header_dict[depRel[0]] = num+2 # if it's a dependency, we need another column
                    attr_name[0] = 'dep_tag'
                header_dict[attr_name[0].lower()] = num+1 # fit to columns
        # check if a original standard file is given
        if self._indir.get() != "Hier Pfad zu Standard-XML-Datei eingeben" and self._indir.get() != "" and "metadata" in header_dict:
            try:
                tree = et.parse(self._indir.get())
            except:
                messagebox.showerror(title="Datei nicht gefunden", message="Bitte gib einen gültigen Pfad zu deiner Standard-XML-Datei an.")
                return None
            root = tree.getroot()
            # Metadaten auslesen und zugehörige Sätze finden
            # Ursprungsdatei könnte auch automatisch ausgelesen werden
            # Häkchen "Find original Standard file automatically"
            # Check if metadata is found
            # if yes, read metadata and append phrases accordingly
            # if no, simply append phrases one after the other => TODO
            for phrase_id, phrase in phrasedict.items():
                # Read metadata
                metadata = phrase[1][0][header_dict["metadata"]].split(", ")
                # find the correct node
                corr_phrase = root.xpath("//phrase[@id={}]".format(metadata[2]))
                if corr_phrase:
                    if len(corr_phrase) > 1:
                        self._info2.set("Phrase {}: Multiple corresponding phrases were found, data will be appended to first occurence".format(str(phrase_id)))
                    corr_phrase = corr_phrase[0]
                    mode = self.mode.get()
                    if mode == "full overwrite":
                        # delete all old children
                        for child in corr_phrase:
                            corr_phrase.remove(child)
                        # append new ones
                        for token in phrasedict[phrase_id][1]:
                            new_id = "{}-{}".format(corr_phrase.attrib['id'],str(token[0]).split("-")[1])
                            tokenElem = et.SubElement(corr_phrase, 'token', id = new_id)
                            tokenElem.text = token[1]
                            setAttributes(tokenElem, header_dict, corr_phrase, token)
                    elif mode == "replace changed ones (requires id)":
                        # check which childrens have changed
                        # only delete and replace new ones
                        for child in corr_phrase:
                            for token in phrasedict[phrase_id][1]:
                                if child.attrib['id'] == str(token[0]):
                                    child.text = token[1]
                                    setAttributes(child, header_dict, corr_phrase, token)
                    elif mode == "append":
                        # simply add all tokens without consideration of old ones
                        for token in phrasedict[phrase_id][1]:
                            tokenElem = et.SubElement(corr_phrase, 'token', id=str(token[0]))
                            tokenElem.text = token[1]
                            setAttributes(tokenElem, header_dict, corr_phrase, token)
                else:
                    self._info2.set("Phrase {}: No corresponding phrase was found in the Standard file".format(str(phrase_id)))
            with open(self._indir.get(), mode="w", encoding="utf-8") as outf:
                treeResult = et.tostring(root, encoding="unicode", pretty_print=True)
                outf.write(treeResult)
                self._info.set("Standard file was written")
            #~ else:
                #~ self._info2.set("Your Webanno Import file contains no metadata column or the column is not called 'metadata'.")
                
        else:
            self._info2.set("Your Webanno Import file contains no metadata column or the column is not called 'metadata' or you have not assigned a file to merge with. A new file will be created.")
            # if no file is given, write a new Standard file
            new_file = os.path.basename(self._inWebAnno.get())[:-4]
            with open("output/"+new_file+"Standard.xml",mode="w",encoding="utf8") as f:
                # write an xml tree like in standard with the given information
                root = et.Element('corpus')
                root.set('version', '1.0')
                xmlDoc = et.ElementTree(root)
                
                f.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
                f.write("<" + root.tag + ">\n")
                
                # only this one input file
                fileElem = et.SubElement(root,'document', file=new_file+".tsv", searchTerm="?")
                
                for phrase_id in sorted(phrasedict):
                    phraseElem = et.SubElement(fileElem,'phrase', id=str(phrase_id),foundTerm="?", authorID="?", publicationID="?")
                    phraseElem.text = phrasedict[phrase_id][0]
                    for token in phrasedict[phrase_id][1]:
                        tokenElem = et.SubElement(phraseElem, 'token', id=str(token[0]))
                        tokenElem.text = token[1]
                        for attribute, column in header_dict.items():
                            if attribute != "metadata":
                                try:
                                    tokenElem.set(attribute,token[column])
                                except:
                                    self._info2.set("Error at",token[0])
                
                treeResult = et.tostring(fileElem, encoding='unicode', pretty_print=True)
                f.write(treeResult)
                root.remove(fileElem) # to free up the space (free memory)
                f.write("</" + root.tag + ">")
                
            #webbrowser.open(new_file+"Standard.xml") # open file?
            self._info.set("Standard file was written.")


def main():
    new_conv = ToStandard()
    

if __name__ == "__main__":
    main()
