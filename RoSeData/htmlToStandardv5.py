#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# New in 4.1: id now starts at 1 to be more like Webanno
# New in 5.0: Implemented as a Tkinter App and as a class

import glob
import os
import lxml.etree as et
import regex as re
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

class htmlToStandard():
    def __init__(self):
        # Build App
        self.ht = Tk()
        self.ht.focus_force()
        self.ht.title("self.htML-Standard-Konversion (CNDH)")
        
        self._indir = StringVar(self.ht, value="Hier Pfad zu Verzeichnis mit HTMLs eingeben")
        inDir = Entry(self.ht, textvariable=self._indir, width=50).grid(padx=10, pady=10)
        btn = Button(self.ht, text="Verzeichnis wählen", command=self._set_directory).grid(row=0, column=1, padx=10)
        
        self._outF = StringVar(self.ht, value="Hier Name der XML Standard-Datei eingeben")
        outF = Entry(self.ht, textvariable=self._outF, width=50).grid(padx=10, pady=10)
        
        self._outM = StringVar(self.ht, value="Hier Name der XML Meta-Datei eingeben")
        outM = Entry(self.ht, textvariable=self._outM, width=50).grid(padx=10, pady=10)
        
        btn = Button(self.ht, text="Konversion starten", relief=RAISED, command=self.convert).grid(columnspan=2, sticky=W+E)
        
        self._info = StringVar(self.ht, value="")
        info = Message(self.ht, textvariable=self._info, width=50).grid(columnspan=2, pady=10)
        
        with open("RoSe.log", mode="a") as log:
            log.write("Starting conversion of self.htML files to one XML file.\n")
        
        mainloop()
        
    def _set_directory(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self._indir.set(dirname)
            
    def convert(self):
        
        #Check input
        if self._outF.get() == "Hier Name der XML Standard-Datei eingeben":
            messagebox.showerror(title="Fehlender XML-Name", message="Bitte gib einen Namen für deine XML-Standarddatei an.")
        elif self._outM.get() == "Hier Name der XML Meta-Datei eingeben":
            messagebox.showerror(title="Fehlender XML-Name", message="Bitte gib einen Namen für deine XML-Meta-Datei an.")
        else:
            filelist = glob.iglob(os.path.join(self._indir.get(), '*.htm*'))
            tupled_filelist = []
            for file in filelist:
                filename = os.path.basename(file)
                number = re.findall(r'\d+',filename)
                tupled_filelist.append((int(number[0]),file))
            if len(tupled_filelist) < 1:
                messagebox.showerror(title="Keine HTMLs gefunden", message="Unter dem von dir angegebenen Dateipfad konnten keine HTML-Dateien gefunden werden.")
                return None
            parser = et.HTMLParser(remove_blank_text=True)

            ## some statistics
            completes = 0
            incompletes = 0

            # open files to write
            outXMLFile = open(self._outF.get(),encoding='utf-8',mode='w')
            outMetaFile = open(self._outM.get(),encoding='utf-8',mode='w')
        
            # create root element for the generated xml files  
            root = et.Element('corpus')
            root.set('version', '1.0')
            xmlDoc = et.ElementTree(root)

            metaroot = et.Element('CNDH')
            metaroot.set('version', '1.0')
            xmlDoc = et.ElementTree(metaroot)

            # If you build up one xml tree for all files and print it in the end,
            # you could run into memory problems. Hack to prevent that:
            # 1) write declaration and root element start tag,
            # 2) write the elements in the loop and delete them immediately afterwards
            # 3) write end tag of root element after the loop.
            #
            # write declaration and root directly as string as lxml does not provide a function for this
            outXMLFile.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            outXMLFile.write("<" + root.tag + ">\n")

            outMetaFile.write("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
            outMetaFile.write("<" + metaroot.tag + ">\n")
            
            # unique ids to bring metadata and phrases back together later
            authid = 0
            pubid = 0

            # unique id for every phrase
            phraseid = 1

            # authorList = []
            publicationList = []
            
            for number, file in sorted(tupled_filelist):
                with open(file,encoding='utf-8') as f:
                    doc = et.parse(f, parser)
                    #Create a node for all phrases by one file
                    fileElem = et.SubElement(root,'document', file=os.path.basename(file))

                    # search for the element that encloses the metadata
                    tooltipsMeta = doc.xpath("//tbody//span[contains(@id,'htmlPanelGroup31')]")

                    for tooltipM in tooltipsMeta:
                        metaDataList = []
                        contextList = []
                        # get text children of htmlPanelGroups to save metadata
                        year = tooltipM.xpath("child::span[contains(@id,'htmlOutputText551')]//text()")
                        author = tooltipM.xpath("child::span[contains(@id,'htmlOutputText561')]//text()")
                        pubTitle = tooltipM.xpath("child::span[contains(@id,'htmlOutputText591')]//text()")
                        pubNation = tooltipM.xpath("child::span[contains(@id,'htmlOutputText631')]//text()")
                        pubPub = tooltipM.xpath("child::span[contains(@id,'htmlOutputText651')]//text()")
                        # correct the formatting
                        year[0] = year[0].rstrip(" ")
                        author[0] = author[0].rstrip(", ")
                        pubNation[0] = pubNation[0].rstrip("] [")
                        pubNation[0] = pubNation[0].lstrip(" [")
                        pubPub[0] = pubPub[0].lstrip(" ")
                        pubPub[0] = pubPub[0].rstrip("]")
                        pubPub[0] = pubPub[0]
                        # keep track of authors and publications via dictionary
                        pubInfo = [author[0], pubTitle[0], pubNation[0], pubPub[0], year[0]]
                        
                        found = False
                        found_author = False
                        
                        this_authid = authid
                        this_pubid = pubid
                        
                        for pubID, authID, publication in publicationList:
                            if pubInfo == publication:
                                found = True
                                this_pubid = pubID
                                this_authid = authID
                                break
                            else:
                                if publication[0] == pubInfo[0]:
                                    this_authid = authID
                                    found_author = True
                                        
                        if phraseid == 0:
                                publicationList.append((pubid,authid,pubInfo))
                                this_pubid = pubid
                                this_authid = authid
                                pubid += 1
                                authid += 1  
                                found = True
                                

                        #testfile.write("Phrase: " + str(phraseid) + "\n")
                        if found:
                            #testfile.write("Publication already in list: " + str(this_pubid) + str(this_authid) + pubInfo[1] + "\n")
                            pass
                        elif found_author:
                            #testfile.write("Author already in list: " + str(pubid) + str(this_authid) + pubInfo[1] + "\n")
                            publicationList.append((pubid,this_authid,pubInfo))
                            pubid += 1
                        else:
                            #testfile.write("Publication added: " + str(pubid) + str(authid) + pubInfo[1] + "\n")
                            publicationList.append((pubid,authid,pubInfo))
                            this_pubid = pubid
                            this_authid = authid
                            pubid += 1
                            authid += 1
                                    
                        # get elements that are in the same table row and contain the tooltip text for the context
                        firstPartContext = tooltipM.xpath("ancestor::tr//span[@class='datos_cabecera' and @id[contains(.,'htmlOutputText111')]]")
                        searchTerm = firstPartContext[0].xpath("../span[contains(@id,'htmlOutputText71')]")
                        secondPartContext = firstPartContext[0].xpath("../span[contains(@id,'htmlOutputText181')]")
                        if firstPartContext[0].text:
                            firstPartContextText = firstPartContext[0].text.strip()
                        else:
                            firstPartContextText = ""
                        if secondPartContext[0].text:
                            secondPartContextText = secondPartContext[0].text.strip()
                        else:
                            secondPartContextText = "" 
                        contextList.extend([firstPartContextText, searchTerm[0].text.strip(),secondPartContextText])
                        phrase = ' '.join(contextList)
                        
                        # cut away unneeded context (so only sentence with searchTerm remains)
                        #More abbreviations can be added but have to be added to both conditions
                        abbreviations = r'Mr|Dr|Sr|Mrs|Sra|Dra|Av|D|Da|Gob|Gral|Ing|Prof|Profa|Srta'
                        sentence_endings = r'\.|!|\?|—|»|«'
                        sentence_starters = r'\p{Lu}|¿|¡|-|»|"| |*|—|«'
                        
                        splitPattern = r'(?<!\([^\)]*?(?=(?<=(?<!'+abbreviations+')['+sentence_endings+']"?)[ |\n](?=['+sentence_starters+'])[^\(\)]*\)))(?<=(?<!'+abbreviations+')['+sentence_endings+']"?)[ |\n](?=['+sentence_starters+'])'
                        splitPattern2 = r'(?<=:"?)[ |\n]'
                        
                        phraseList = re.split(splitPattern+'|'+splitPattern2,phrase)
                        for partPhrase in phraseList:
                            foundWord = re.search(searchTerm[0].text.strip(),partPhrase)
                            if foundWord:
                                clearPhrase = partPhrase
                                if partPhrase == phraseList[0]:
                                    beforePhrase = " "
                                else:
                                    beforePhrase = lastPhrase
                            lastPhrase = partPhrase
                                
                        clearPhrase = clearPhrase.lstrip(' -—*\n,')
                        clearPhrase = clearPhrase.rstrip(',')
                        
                        #only for bugfixing
                        #outTestFile.write("-------------------\n\n")
                        #outTestFile.write(phrase + "\n\n")
                        #for element in phraseList:
                            #outTestFile.write(element + "\n")
                        #outTestFile.write("\n" + clearPhrase + "\n\n")

                        # check if phrase is a poem (identified by multiple \n in between other signs)
                        poemTrue = re.search('.+\n.+\n',clearPhrase)
                        metaDataList = year
                        metaDataList.extend(author)
                        metaDataList.extend(pubTitle)
                        metaDataList.extend(pubNation)
                        metaDataList.extend(pubPub)
                        # create xml elements
                        resultElem = et.SubElement(fileElem,'phrase', id=str(phraseid),foundTerm=searchTerm[0].text.strip(), authorID=str(this_authid), publicationID=str(this_pubid))
                        phraseid += 1
                        # check if sentence is complete (at least the end)
                        completeSentFinish = re.search(u'[\.\?!:"«»\']', clearPhrase[-1])               
                        completeSentStart = re.search(u'[\p{Lu}¿¡"«»\']',clearPhrase[0])
                        #Do a special check for sentences after ':'
                        lookforPoints = re.search(r':', beforePhrase[-1])
                        if lookforPoints:
                            completeSentStart = True
                        # add text to xml elements
                        resultElem.text = clearPhrase
                        if completeSentFinish:
                            if completeSentStart:
                                resultElem.set('complete','yes')
                                completes += 1
                            else:
                                resultElem.set('complete','no')
                                incompletes += 1
                        else:
                            resultElem.set('complete','no')
                            incompletes += 1
                        if poemTrue:
                            resultElem.set('style','poem')
                        else:
                            resultElem.set('style','plain')
                        
                        # Temporary for testing
                        #if completeSentFinish and completeSentStart:
                            #outTestFile.write("This file was found to be COMPLETE\n")
                        #else:
                            #outTestFile.write("This file was found to NOT BE COMPLETE\n")
                        
                    # add the searchTerm to the file element
                    searchfield = doc.xpath("//input[contains(@id,'jsf:import:CNDHEForm:ListaCompleja:__row0:asyncTable:0:lema')]")
                    searchTermOnFile = searchfield[0].get("value")
                    fileElem.set('searchTerm',searchTermOnFile)
                    # print result entry to xml file
                    treeResult = et.tostring(fileElem, encoding = 'unicode', pretty_print=True)
                    outXMLFile.write(treeResult)
                    root.remove(fileElem) # to free up the space (free memory)
            
            # build metadata
            for pubID, authID, publication in publicationList:
                #testfile.write(str(pubID)+str(authID)+''.join(publication)+"\n")
                pubElem = et.SubElement(metaroot, 'publication')
                pubElem.set("publicationID",str(pubID))
                authorElem = et.SubElement(pubElem, 'author', authorID=str(authID))
                authorElem.text = publication[0]
                nameElem = et.SubElement(pubElem, 'name')
                nameElem.text = publication[1]
                nationElem = et.SubElement(pubElem, 'nation')
                nationElem.text = publication[2]
                publisherElem = et.SubElement(pubElem, 'publisher')
                publisherElem.text = publication[3]
                yearElem = et.SubElement(pubElem, 'date')
                yearElem.text = publication[4]
                # write metadata tree
                metatreeResult = et.tostring(pubElem, encoding = 'unicode', pretty_print=True)
                outMetaFile.write(metatreeResult)
                metaroot.remove(pubElem) # to free up the space (free memory)

            outXMLFile.write("</" + root.tag + ">")
            outMetaFile.write("</" + metaroot.tag + ">")

            # print out some statistics
            info += "Finished parsing!\n"
            info += "Total of complete sentences: {}\n".format(str(completes))
            info += "Total of incomplete sentences: {}\n".format(str(incompletes))
            info += "Total of all sentences: {}\n".format(str(completes+incompletes))
            self._info.set(info)

            outXMLFile.close()
            outMetaFile.close()
        
def main():
    pass
        
if __name__ == "__main__":
    main()
