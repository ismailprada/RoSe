#! /usr/bin/python3

#2016 by Ismail Prada
#Based on a tagger by http://xorrai.cs.upc.edu/downloads/STIL-2015/

# New in Version 3.2:
# file will now be written dynamically, so RAM won't fill up.
# New in Version 4:
# Implemented as Tkinter App

import freeling
from lxml import etree as ET
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox
import math
import os
import sys
import csv


class Tagger():
    def __init__(self):
        self.root = Tk()
        self.root.title("Tagger")
        self.root.focus_force()
        
        self._indir = StringVar(self.root, value="Hier Pfad zu Standard-XML-Datei eingeben")
        inDir = Entry(self.root, textvariable=self._indir, width=50).grid(columnspan=2, padx=10, pady=10)
        choose_indir = Button(self.root, text="Datei wählen", command=self._set_file).grid(row=0, column=2, padx=10)

        self._outF = StringVar(self.root, value="Hier Name für getaggte Datei eingeben")
        outF = Entry(self.root, textvariable=self._outF, width=50).grid(columnspan=2, padx=10, pady=10)

        separator = Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)
        
        label = Label(self.root, text="Erlaubt Stile:").grid(row=3, column=0, sticky=E, padx=10, pady=5)
        
        self._styles = StringVar(self.root, value="")
        possible_styles = ["all", "plain", "poem"]
        self.styles = OptionMenu(self.root, self._styles, *possible_styles).grid(row=3, column=1, sticky=W+E, padx=10, pady=5)
        
        label = Label(self.root, text="Anzahl Sätze pro Datei:").grid(row=4, column=0, sticky=E, padx=10, pady=5)
        self._ppf = IntVar(self.root, value=200)
        ppf = Entry(self.root, textvariable=self._ppf).grid(row=4, column=1, sticky=W+E, padx=10, pady=5)
        
        self._only_completes = IntVar(self.root, value=0)
        Checkbutton(self.root, text="Nur komplette Sätze taggen", variable=self._only_completes).grid(column=1, sticky=W)
        self._webanno = IntVar(self.root, value=0)
        Checkbutton(self.root, text="Datei für Webanno-Import ausgeben", variable=self._webanno).grid(column=1, sticky=W)
        
        separator = Frame(self.root, height=2, bd=1, relief=SUNKEN).grid(columnspan=3, sticky=W+E, padx=5, pady=5)
        
        tag_btn = Button(self.root, text="Tagging-Prozess starten", relief=RAISED, command=self.tag).grid(columnspan=3, sticky=W+E, pady=10, padx=5)
        
        self._info = StringVar(self.root, value="")
        info = Message(self.root, textvariable=self._info, width=500).grid(columnspan=3, pady=10)
        self._info2 = StringVar(self.root, value="")
        info2 = Message(self.root, textvariable=self._info2, width=500).grid(columnspan=3, pady=10)
        
        mainloop()
        
    def _show_file(self):
        webbrowser.open("output/"+self._outF.get()+".xml")
        
    def _set_file(self):
        dirname = filedialog.askopenfilename(filetypes=[("XML files","*.xml")])
        if dirname:
            self._indir.set(dirname)
            
    def tag(self):
        
        try:
            styles = self._styles.get()
            ppf = self._ppf.get()
            if self._only_completes.get() == 1:
                only_completes = True
            else:
                only_completes = False
            if self._webanno.get() == 1:
                webanno = True
            else:
                webanno = False
        except:
            messagebox.showerror(title="Ungültige Eingabe", message="""Bitte überprüfe, dass es sich bei deiner Eingabe in "Anzahl Sätze pro Datei" um eine ganzzahlige Zahl handelt.""")
            return None
            
        self._info.set("Starting...")
        self.root.update()
            
        # headers for the tsv
        if webanno:
            metadata_header = "webanno.custom.Metadata | Metadatavalue"
            lemma_header = "de.tudarmstadt.ukp.dkpro.core.api.segmentation.type.Lemma | value"
            pos_header = "de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS | PosValue"
            new_pos_header = "webanno.custom.NewPOS | SavePOSValue"
            morpho_header = "webanno.custom.Morpho | MorphoValue"
            comment_header = "webanno.custom.Comments | Commentvalue"
            dep_header = "de.tudarmstadt.ukp.dkpro.core.api.syntax.type.dependency.Dependency | DependencyType | AttachTo=de.tudarmstadt.ukp.dkpro.core.api.lexmorph.type.pos.POS"
            hashtag = " # "
            
        # this needs to point to the freeling install directory
        FREELINGDIR = "/usr/local";
        DATA = FREELINGDIR+"/share/freeling/";
        LANG = "es";
        PATH = DATA + LANG + "/"

        freeling.util_init_locale("default");
        
        # create tokenizer and splitter
        tk=freeling.tokenizer(PATH+"tokenizer.dat");
        sp=freeling.splitter("RoSeData/no_splitter.dat"); # a splitter is necessary for the process, 
        sid=sp.open_session();                        # but our data is already split. no_splitter.dat tells the splitter to never split

        # create options set for maco analyzer. Default values are Ok, except for data files.
        op= freeling.maco_options("es");
        op.UserMapFile="";
        op.LocutionsFile=PATH+"locucions.dat"; 
        op.AffixFile=PATH+"afixos.dat";
        op.ProbabilityFile=PATH+"probabilitats.dat"; 
        op.DictionaryFile=PATH+"dicc.src";
        op.NPdataFile=PATH+"np.dat"; 
        op.PunctuationFile=PATH+"../common/punct.dat"; 

        mf=freeling.maco(op);
        
        # activate morpho modules to be used in next call
        mf.set_active_options(False, True, True, True,  # select which among created 
                              True, True, False, True,  # submodules are to be used. 
                              True, True, False, True ); # default: all created submodules are used
        
        # create tagger
        self._info.set("Generiere Tagger...")
        self.root.update()
        tg=freeling.hmm_tagger(PATH+"tagger.dat",True,2);

        # create sense annotator and disambiguator
        self._info.set("Generiere sense disambiguator...")
        self.root.update()
        sen=freeling.senses(PATH+"senses.dat")
        wsd=freeling.ukb(PATH+"ukb.dat")

        # create parser
        self._info.set("Generiere dependency parser...")
        self.root.update()
        parser = freeling.dep_treeler(PATH+"dep_treeler/dependences.dat")
        
        # keep track of how many sentences were counted
        sent_counter = 0

        # keep track of documents created
        doc_counter = 0

        webanno_sent_counter = 0

        outputter = freeling.output_conll()
        
        # Write headers
        outf = open("output/"+self._outF.get()+".xml",encoding='utf-8',mode='w')
        outf.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        outf.write("<corpus>\n")
        # Start Tagging Process
        try:
            iterate_docs = ET.iterparse(self._indir.get(), events=("end", ), tag="document")
        except:
            messagebox.showerror(title="Ungültiger Dateipfad", message="Unter dem angegebenen Dateipfad konnte keine XMl-Datei gefunden werden.")
            self._info.set("Process stopped.")
            self.root.update()
            return None
        for action, doc in iterate_docs: # iterate all fileElems
            if True: # filter in case you only want certain docs
                self._info.set("Dokument {} wird bearbeitet...".format(doc.attrib["file"]))
                self.root.update()
                # filter out all unwanted phrases
                if styles == 'all' and only_completes == True:
                    phrases = doc.xpath('phrase[contains(@complete,"yes")]')
                elif styles == 'all' and only_completes == True:
                    phrases = doc.xpath('phrase')
                elif styles != 'all' and only_completes == True:
                    phrases = doc.xpath('phrase[contains(@complete,"yes") and contains(@style,"' + styles + '")]')
                else:
                    phrases = doc.xpath('phrase[contains(@style,"' + styles + '")]')
                for phrase in phrases:
                    phrasetext = phrase.text
                    lw = tk.tokenize(phrasetext);
                    ls = sp.split(sid, lw, True);
                    ls = mf.analyze(ls);
                    ls = tg.analyze(ls);
                    ls = sen.analyze(ls)
                    wsdis = wsd.analyze(ls)
                    dep = parser.analyze(wsdis)
                    if webanno:
                        # open a new tsv file if number of phrases is reached
                        if sent_counter % ppf == 0:
                            if doc_counter != 0:
                                conllout.close()
                            doc_counter += 1
                            conllout = open(self._outF.get() + '-' + str(doc_counter) + '.tsv',encoding='utf-8',mode='w')
                            tsvwriter = csv.writer(conllout, delimiter='\t')
                            # implement headers
                            tsvwriter.writerow([hashtag + metadata_header + hashtag + lemma_header + hashtag + pos_header + hashtag + new_pos_header + hashtag + morpho_header + hashtag + comment_header + hashtag + dep_header])
                            webanno_sent_counter = 0
                        if webanno_sent_counter != 0:
                            tsvwriter.writerow([])
                        tsvwriter.writerow(["#id=" + str(webanno_sent_counter)])
                    word_counter = 1
                    sent_counter += 1
                    self._info2.set(str(sent_counter) + " Sätze wurden analysiert!")
                    self.root.update()
                    conllstr = outputter.PrintResults(dep)
                    tokens_in_sent = conllstr.splitlines()
                    
                    # a clunky way to get the treedata
                    depdict = {}
                    for token in tokens_in_sent:
                        if len(token) > 1:
                            elements = token.split()
                            depdict[elements[0]] = [elements[1],elements[9],elements[10]]
                            
                    for sentence in ls :
                        sent_all_info = [] #only needed for the AfterFilter
                        
                        for word in sentence.get_words():
                            dictentry = depdict[str(word_counter)]
                            if dictentry[0] != word.get_form():
                                print("An error occured! Please check this phrase:",phrasetext)
                            if dictentry[1] == "0":
                                dictentry[1] = str(word_counter)
                            # we give the metadata to the phrase by storing it as a layer in the first token
                            if word_counter == 1:
                                doc = phrase.getparent()
                                docname = doc.attrib["file"]
                                webanno_metadata = os.path.basename(self._indir.get()) + ", " + docname + ", " + phrase.attrib["id"]
                            else:
                                webanno_metadata = "_"
                            tokenElem = ET.SubElement(phrase, 'token', id=str(word_counter),lemma=word.get_lemma(), pos=word.get_tag(), dep_tag=dictentry[2], dep_parent=dictentry[1])
                            tokenElem.text = word.get_form()
                            if webanno:
                                #save all info as a tuple similar to webanno/conll-Format
                                all_info = (word.get_form(), webanno_metadata, word.get_lemma(), word.get_tag(),dictentry[2], dictentry[1])
                                sent_all_info.append(all_info)
                            word_counter += 1
                            
                        if webanno:
                            allowed = self._AfterFilter(sent_all_info) #filter the phrases
                            if allowed:
                                webanno_sent_counter += 1
                                this_word_counter = 1
                                # finally write the phrases to the tsv
                                for element in sent_all_info:
                                    tsvwriter.writerow([str(webanno_sent_counter) + "-" + str(this_word_counter), element[0], element[1], element[2], element[3], "_", "_", "O", element[4], str(webanno_sent_counter) + "-" + element[5]])
                                    this_word_counter += 1
                # write docElem
                docString = ET.tostring(doc, encoding = 'unicode', pretty_print=True)
                outf.write(docString)
            doc.clear()
            # Also eliminate now-empty references from the root node to elem
            for ancestor in doc.xpath('ancestor-or-self::*'):
                while ancestor.getprevious() is not None:
                    del ancestor.getparent()[0]
            doc.getparent().remove(doc)

        outf.write("</corpus>")
        outf.close()
        del iterate_docs
        
        if webanno:
            conllout.close()

        sp.close_session(sid);
        
        self._info.set("Tagging erfolgreich beendet.")
        self.root.update()
        
    @staticmethod
    def _AfterFilter(toFilter):
        # A filter may be added here to stop certain sentences to appear in the conll-corpus
        allowed = True
        return allowed

def main():
    new_tagger = Tagger()
    

if __name__ == "__main__":
    main()
