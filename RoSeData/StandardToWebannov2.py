#! /usr/bin/python3
# April/Mai 2017 by Ismail Prada

# Version 2: Implemented in Tkinter
# Filter von Attributen fällt weg, da diese einfach in Webanno
# abgeschaltet werden können.
# Bei Bedarf kann die Filter reimplementiert werden.

import csv
import os
from tkinter import *
from tkinter.ttk import Combobox
from tkinter import filedialog
from tkinter import messagebox
from lxml import etree as ET

class ToWebanno():
    def __init__(self):
        self.root = Tk()
        self.root.title("Standard-Webanno-Konversion")
        self.root.focus_force()
        
        self._indir = StringVar(self.root, value="Hier Pfad zu Standard-XML-Datei eingeben")
        inDir = Entry(self.root, textvariable=self._indir, width=50).grid(columnspan=2, padx=10, pady=10)
        choose_indir = Button(self.root, text="Datei wählen", command=self._set_file).grid(row=0, column=2, padx=10)
        
        self._outF = StringVar(self.root, value="Hier Name für Webanno-Datei eingeben")
        outF = Entry(self.root, textvariable=self._outF, width=50).grid(columnspan=2, padx=10, pady=10)
        
        separator = Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)
        
        label = Label(self.root, text="Erlaubt Stile:").grid(row=3, column=0, sticky=E, padx=10, pady=5)
        
        self._styles = StringVar(self.root, value="")
        possible_styles = ["all", "plain", "poem"]
        self.styles = Combobox(self.root, values=possible_styles, textvariable=self._styles).grid(row=3, column=1, sticky=W+E, padx=10, pady=5)
        
        label = Label(self.root, text="Anzahl Sätze pro Datei:").grid(row=4, column=0, sticky=E, padx=10, pady=5)
        self._ppf = IntVar(self.root, value=200)
        ppf = Entry(self.root, textvariable=self._ppf).grid(row=4, column=1, sticky=W+E, padx=10, pady=5)
        
        self._only_completes = IntVar(self.root, value=0)
        Checkbutton(self.root, text="Nur komplette Sätze bearbeiten", variable=self._only_completes).grid(column=1, sticky=W)
        
        separator = Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)
        
        tag_btn = Button(self.root, text="Starte Konversion", relief=RAISED, command=self.go).grid(row=7, columnspan=3, sticky=W+E, pady=10, padx=5)
        #tag_btn = Button(self.root, text="Finde Attribute", relief=RAISED, command=self.scan).grid(row=7, column=1, sticky=W+E, pady=10, padx=5)
        
        self._info = StringVar(self.root, value="")
        info = Message(self.root, textvariable=self._info, width=500).grid(columnspan=3, pady=10)
        self._info2 = StringVar(self.root, value="")
        info2 = Message(self.root, textvariable=self._info2, width=500).grid(columnspan=3, pady=10)
        
        mainloop()
        
    def _set_file(self):
        dirname = filedialog.askopenfilename(filetypes=[("XML files","*.xml")])
        if dirname:
            self._indir.set(dirname)
            
    def go(self):
        try:
            ppf = self._ppf.get()
        except:
            messagebox.showerror(title="Ungültige Eingabe", message="""Bitte überprüfe, dass es sich bei deiner Eingabe in "Anzahl Sätze pro Datei" um eine ganzzahlige Zahl handelt.""")
            return None
            
        self._info.set("Starting...")
        self.root.update()
        
        try:
            tree = ET.iterparse(self._indir.get(), events=("end", ), tag="phrase")
        except:
            messagebox.showerror(title="Ungültiger Dateipfad", message="Unter dem angegebenen Dateipfad konnte keine XMl-Datei gefunden werden.")
            self._info.set("Process stopped.")
            self.root.update()
            return None
            
        self.attributes = self.find_attributes(self._indir.get())
        
        phrasecount = 0
        documentcount = 0
        
        for action, elem in tree:
            if self.checkFilter(elem):
                # Weitere Filter, um nicht komplette Sätze auszusortieren
                phrasecount += 1
                if phrasecount % ppf == 1 or documentcount == 0:
                    documentcount += 1
                    try:
                        webanno.close()
                    except:
                        pass
                    webanno = open("output/"+self._outF.get()+"-"+str(documentcount)+".tsv", mode="w", encoding="utf-8")
                    curr_writer = self.openNewTSV(webanno)
                curr_writer.writerow(["#id={}".format(str(int(elem.attrib["id"])+1))])
                tokencount = 0
                for token in elem:
                    tokencount += 1
                    attr_list = []
                    attr_list.append("{}-{}".format(phrasecount, tokencount))
                    attr_list.append(token.text)
                    if tokencount == 1:
                        doc = elem.getparent()
                        docname = doc.attrib["file"]
                        webanno_metadata = ", ".join([os.path.basename(self._indir.get()), docname, elem.attrib["id"]])
                    else:
                        webanno_metadata = "_"
                    attr_list.append(webanno_metadata)
                    for attr in self.HEADER:
                        if attr == "dependency":
                            attr_list.append(token.attrib["dep_tag"])
                            attr_list.append("{}-{}".format(phrasecount, token.attrib["dep_parent"]))
                        else:
                            attr_list.append(token.attrib[attr])
                    curr_writer.writerow(attr_list)
                curr_writer.writerow([])
                self._info2.set(str(phrasecount) + " Sätze wurden konvertiert!")
                self.root.update()
        self._info.set("Konversion erfolgreich beendet.")
        self.root.update()
    
    def find_attributes(self, infile):
        attributes = set()
        tree = ET.iterparse(infile, events=("end", ), tag="phrase")
        for action, elem in tree:
            for token in elem:
                for attr in token.attrib:
                    attributes.add(attr)
            # clean up working space
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]
                
        if "dep_tag" in attributes and "dep_parent" in attributes:
            attributes.remove("dep_tag")
            attributes.remove("dep_parent")
            attributes.add("dependency")
        
        return attributes
        
            
    def checkFilter(self, elem):
        styles = self._styles.get()
        if self._only_completes.get() == 1:
            completes = True
        else:
            completes = False
        styleValue = False
        completeValue = False
        if styles == "all" or styles is None:
            styleValue = True
        else:
            if elem.attrib["style"] == styles:
                styleValue = True
        if completes:
            if elem.attrib["complete"] == "yes":
                completeValue = True
        else:
            completeValue = True
            
        if completeValue and styleValue:
            return True
        else:
            return False
            
    def openNewTSV(self, webanno):
        global app
        global HEADER
        
        WAwriter = csv.writer(webanno, delimiter='\t', quoting=csv.QUOTE_NONE, escapechar='\\')
        
        # Write header
        # special headers
        lemma_header = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma | value"
        pos_header = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS | PosValue"
        dep_header = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency | DependencyType | AttachTo=de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"
        metadata_header = "webanno.custom.Metadata | Metadatavalue"
        hashtag = " # "
        # custom headers
        customs = []
        custom_pattern = "webanno.custom.CHANGE | CHANGEvalue"
        
        headers = []
        header_order = []
        
        # append all headers that are needed
        headers.append(metadata_header)
        for attr in self.attributes:
            if attr == "lemma":
                headers.append(lemma_header)
            elif attr == "pos":
                headers.append(pos_header)
            elif attr == "dependency":
                headers.append(dep_header)
            else:
                custom_header = custom_pattern.replace("CHANGE", attr)
                headers.append(custom_header)
            header_order.append(attr)
        header = " # {}".format(" # ".join(headers))
        WAwriter.writerow([header])
        self.HEADER = header_order
        return WAwriter
        
        
    #~ def scan(self):
        #~ pass

def main():
    towebanno = ToWebanno()

if __name__ == '__main__':
    main()
