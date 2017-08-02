#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Written by Ismail Prada
# Version 4.0: Implementation in Tkinter
# May 2017 (4.0: July 2017)

###BEMERKUNGEN###
# checkpublisher könnte bei exact_matches Probleme machen TODO
###

import datetime
import itertools
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
from tkinter import messagebox
from collections import namedtuple, Counter
from collections import OrderedDict
import time
import sys
import webbrowser
from lxml import etree as ET
import re
import unicodedata


class Search():
    def __init__(self):
        self.search_list = []
        self.relation_list = []
        self.custom_attributes = []
        self.options_list = []
        self.term_counter = 0
        
        self.root = Tk()
        self.root.focus_force()
        self.root.title("Search Corpus")
        # 1 Frame mit den Knöpfen für "Main" und "Metadata"
        navigation = Notebook(self.root)
        # 1 Frame für Main
        self._create_main()
        # 1 Frame für Metadata
        self._create_meta()
        navigation.add(self.main, text="Main")
        navigation.add(self.meta, text="Metadata")
        navigation.grid()
        
        mainloop()
        
        
    def _create_main(self):
        self.main = Frame(self.root)
        input_f = LabelFrame(self.main, text="Datei-Eingabe")
        self._create_input_frame(input_f)
        input_f.grid(padx=10, pady=5, sticky=W+E)
        filter_f = LabelFrame(self.main, text="Filteroptionen")
        self._create_filter_frame(filter_f)
        filter_f.grid(padx=10, pady=5, sticky=W+E)
        button_f = LabelFrame(self.main, text="Befehle")
        self._create_button_frame(button_f)
        button_f.grid(padx=10, pady=5, sticky=W+E)
        self.user_info = Text(self.main, height=8)
        self.user_info.grid(sticky=W+E)
        
        
    def _create_input_frame(self, input_f):
        self._indir = StringVar(input_f, value="")
        Label(input_f, justify=LEFT, text="Pfad zu Standard-XML-Datei:").grid(row=0, column=0, padx=10, sticky=W)
        Entry(input_f, textvariable=self._indir, width=50).grid(row = 0, column=1, pady=10, sticky=W+E)
        Button(input_f, text="Datei wählen", command=self._set_standard_file).grid(row=0, column=2, padx=10)
        
        self._inmeta = StringVar(input_f, value="")
        Label(input_f, justify=LEFT, text="Pfad zu Metadaten-Datei:").grid(row=1, column=0, padx=10, sticky=W)
        Entry(input_f, textvariable=self._inmeta, width=50).grid(row = 1, column=1, pady=10, sticky=W+E)
        Button(input_f, text="Datei wählen", command=self._set_meta_file).grid(row=1, column=2, padx=10)
        
        
    def _set_standard_file(self):
        dirname = filedialog.askopenfilename(filetypes=[("XML files","*.xml")])
        if dirname:
            self._indir.set(dirname)
            
    def _set_meta_file(self):
        dirname = filedialog.askopenfilename(filetypes=[("XML files","*.xml")])
        if dirname:
            self._inmeta.set(dirname)
            
    def _create_filter_frame(self, frame):
        self.criteria = OrderedDict()
        self.criteria["Wort"] = StringVar(frame)
        self.criteria["Lemma"] = StringVar(frame)
        for n, (l, v) in enumerate(self.criteria.items()):
            Label(frame, text=l+":").grid(row=n, column=0, sticky=W, padx=10)
            Entry(frame, textvariable=v).grid(row=n, column=1, columnspan=2, pady=10, padx=5, sticky=W+E)
        self._case_sensitive_word = BooleanVar(frame)
        Checkbutton(frame, text="Gross- und Kleinschreibung beachten", variable=self._case_sensitive_word).grid(row=0, column=3, sticky=W+E)
        pos_options = ["A", "C", "DA", "DD", "DE", "DI", "DP", "DT",
            "Fc", "Fo", "Fp", "Fs", "I", "NC", "NP", "PD", "PE", "PI", 
            "PP", "PR", "PT", "RG", "RN", "SP", "VA", "VM", "VS", "W", "Z"]
        self.criteria["POS"] = StringVar(frame)
        Label(frame, text="POS:").grid(row=2, column=0, sticky=W, padx=10)
        Combobox(frame, values=pos_options, textvariable=self.criteria["POS"]).grid(row=2, column=1, columnspan=2, pady=10, padx=5, sticky=W+E)
        dep_options= ["S", "ao", "atr", "cag", "cc", "cd", "ci", "conj", 
            "coord", "cpred", "creg", "et", "f", "gerundi", "grup.a",
            "grup.adv", "grup.nom", "grup.verb", "impers", "inc", 
            "infinitiu", "interjecció", "mod", "morfema.pronominal", 
            "morfema.verbal", "neg", "participi", "pass", "prep", "realtiu", 
            "s.a", "sa", "sadv", "sentence", "sn", "sp", "spec", "suj", "v"]
        self.criteria["Dependenz"] = StringVar(frame)
        Label(frame, text="Dependenz:").grid(row=3, column=0, sticky=W, padx=10)
        Combobox(frame, values=dep_options, textvariable=self.criteria["Dependenz"]).grid(row=3, column=1, columnspan=2, pady=10, padx=5, sticky=W+E)
        custom_attr = StringVar(frame)
        custom_attr_value = StringVar(frame)
        Label(frame, text="Weitere (Name, Wert):").grid(row=4, column=0, sticky=W, padx=10)
        Entry(frame, textvariable=custom_attr).grid(row=4, column=1, sticky=W+E)
        Entry(frame, textvariable=custom_attr_value).grid(row=4, column=2, sticky=W+E)
        Button(frame, text="Hinzufügen", command= lambda x=custom_attr, y=custom_attr_value: self._add_custom_criteria(x, y)).grid(row=4, column=3, sticky=W, pady=10, padx=5)
        
    
    def _add_custom_criteria(self, attr_name, attr_value):
        if len(attr_name.get()) > 0:
            self.custom_attributes.append(
                (attr_name.get(),
                attr_value.get()))
        attr_name.set("")
        attr_value.set("")
        
    
    def _create_button_frame(self, frame):
        # Go-Button
        Button(frame, text="Suche", command=self.go, width=10).grid(row=0, column=0, sticky=W+E, padx=5, pady=5)
        # Add-Button
        Button(frame, text="+Bedingung", command=self.add, width=10).grid(row=0, column=1, sticky=W+E, padx=5, pady=5)
        # Or-Button
        Button(frame, text="+Option", command=self.option, width=10).grid(row=0, column=2, sticky=W+E, padx=5, pady=5)
        # Relation-OptionMenu
        self._relation = StringVar(frame, "No relation")
        relMenu = OptionMenu(frame, self._relation, "", *["No relation", 
            "is child of", "is parent of", "is right of", "is left of"])
        relMenu.configure(width=10)
        relMenu.grid(row=0, column=3, sticky=W+E, padx=5, pady=5)
        # Ziel-OptionMenu
        self._target = StringVar(frame, "0:None")
        self.targets = ["0:None"]
        self.tarMenu = OptionMenu(frame, self._target, "", *self.targets)
        self.tarMenu.configure(width=10)
        self.tarMenu.grid(row=0, column=4, columnspan=2, sticky=W+E, padx=5, pady=5)
        # Reset-Button
        Button(frame, text="Zurücksetzen", command=self.reset, width=10).grid(row=0, column=6, sticky=W+E, padx=5, pady=5)
        Button(frame, text="Schliessen", command=self.exit, width=10).grid(row=0, column=7, sticky=E, padx=5, pady=5)
        
        
    def go(self):
        flagMETA = False
        # add possible remaining searchterm
        self.add()
        # clean unnecessary search terms out of the list
        self.delete_unneeded()
        try:
            tree = ET.iterparse(self._indir.get(), tag="phrase")
        except:
            messagebox.showerror(title="Ungültige Eingabe", message="Unter dem angegeben Pfad konnte keine gültige Standard-XML-Datei gefunden werden. Bitte überprüfen Sie die Eingabe und versuchen Sie es nochmal.")
            return None
        num_total = 0
        num_tagged = 0
        num_found = 0
        tokenCounter = Counter()
        # parse the metadata tree first
        if len(self._inmeta.get()) > 0:
            try:
                with open(self._inmeta.get(), mode="r", encoding="utf8") as meta:
                    metatree = ET.parse(meta)
                    metaroot = metatree.getroot()
            except:
                messagebox.showerror(title="Ungültige Eingabe", message="Unter dem angegeben Pfad konnte keine gültige Standard-XML-Meta-Datei gefunden werden. Bitte überprüfen Sie die Eingabe und versuchen Sie es nochmal.")
                return None
            flagMETA = True
        # run all phrases through the filters
        with open("found_sentences.html", encoding="utf-8", mode="w") as outfile:
            output_parts = []
            general_counter = Counter()
            for action, phrase in tree:
                if action == "end" and len(phrase) > 0:
                    general_counter["check_phrases"] += 1
                    # check if the metadata fits
                    if flagMETA:
                        pubID = phrase.get("publicationID")
                        pub = metaroot.xpath(
                            "publication[@publicationID={}]".format(pubID))
                        metadata_correct = self.metadatafilter(pub, pubID)
                        metadata_exists = True
                    else:
                        metadata_exists = False
                        metadata_correct = True
                    if metadata_correct or not metadata_exists:
                        general_counter["metadata_correct"] += 1
                        # check if the relations fit
                        found_combinations = self.checkrelations(phrase)
                        if found_combinations:
                            general_counter["found_phrases"] += 1
                            # Ausgabe sollte folgendermassen erfolgen:
                            # => Informationen zum Satz (id, publicationID bzw. Metadaten
                            # => Originaler Satz
                            # => Tokenisierter Satz mit HTML Markup
                            for count, entry in enumerate(found_combinations):
                                general_counter["found_relations"] += 1
                                tokenized_sent = []
                                for token in phrase:
                                    if token in entry.values():
                                        tokenized_sent.append("<b>{}</b>".format(token.text))
                                    else:
                                        tokenized_sent.append(token.text)
                                tokenized_sent = " ".join(tokenized_sent)
                                if not metadata_exists:
                                    insert_metadata = ""
                                else:
                                    # Get metadata (pub is the metadata node)
                                    publication = pub[0].find("name").text
                                    authorname = pub[0].find("author").text
                                    nation = pub[0].find("nation").text
                                    publisher = pub[0].find("publisher").text
                                    date = pub[0].find("date").text
                                    insert_metadata = """
                                    <p>Publication: {}<br>
                                    Author: {}<br>
                                    Country of origin: {}<br>
                                    Publisher and date of publishing: {}<br>
                                    Original date: {}</p>
                                    """.format(publication, authorname, nation, publisher, date)
                                output = """
                                <p>ID: {}, ResultNo.: {}, PublicationID: {}, AuthorID: {}</p>
                                {}
                                <p>
                                Original sentence:
                                </p>
                                <p>
                                {}
                                </p>
                                <p>
                                Tokenized sentence (Found terms highlighted):
                                </p>
                                <p>
                                {}
                                </p>
                                
                                """.format(phrase.get("id"), str(count+1), phrase.get("publicationID"), phrase.get("authorID"), insert_metadata, phrase.text, tokenized_sent)
                                output += "="*80
                                output_parts.append(output)
                    # Inform user
                    self.user_info.delete("1.0", END)
                    self.user_info.insert(END, "Checked phrases: {}; Found phrases: {}".format(general_counter["check_phrases"], general_counter["found_phrases"]))
                    self.user_info.update()
            statistics = """
            <p>Phrases checked: {}<br>
            Phrases found:   {}<br>
            Relations found: {}</p>
            """.format(general_counter["check_phrases"], general_counter["found_phrases"], general_counter["found_relations"])
            statistics += "="*80
            output = """
            <head><meta http-equiv="content-type" content="text/html; charset=UTF-8"></head>
            {}
            """.format(statistics)
            output_parts.insert(0, output)  
            outfile.write(" ".join(output_parts))
            self.user_info.insert(END, "\nFinished writing!")
        webbrowser.open("found_sentences.html")
                        
    def checkrelations(self, phrase):
        # Ziel: Alle Bedingungen müssen erfüllt sein mit einem einzigen Set an Token
        # Ansatz: Token durchgehen
        # Kontrolliere, welche Token auf welche IDs passen.
        # Stelle eine Liste mit allen möglichen Kombinationen dieser Verteilung auf.
        # Probiere aus, ob eine dieser Kombinationen die Beziehungsbedingungen erfüllt.
        # Mehrere valide Kombinationen sind möglich und werfen jeweils ein eigenes
        # Suchresultat
        
        # 1. Für jede ID werden alle möglichen Token berechnet (Dictionary: ID: [Token])
        # 2. Eine Liste von Listen mit allen möglichen Kombinationen wird erstellt
        # Bsp: [[(1,token1),(2,token2)][(1,token2),(2,token1)]]
        # 3. Für jede dieser Listen werden nun alle Beziehungen kontrolliert.
        # Wenn alle Beziehungen funktionieren, ist dieser Satz ein Treffer
        # Es werden aber auch die anderen Möglichkeiten durchgegangen,
        # da auch mehrere mögliche Kombinationen notiert werden müssen.
        # 4. Das Suchresultat wird zusammengebaut. Die Token, welche gefunden
        # wurden im Speziellen, werden wie in HTML mit <b>TOKEN</b> markiert.
        
        id_dict = {}
        # setze alle möglichen Token pro id in ein dictionary
        for options in self.search_list:
            id_dict[options[0]["id"]] = []
            for entry in options:
                for token in phrase:
                    if self.check_attribs(token, entry):
                        id_dict[options[0]["id"]].append(token)
        # kreiere die Liste mit allen Möglichkeiten
        # um das dictionary in itertools einzuspeisen, müssen wir es zuerst in eine
        # Liste von Listen umwandeln:
        # [[(1,token1),(1,token2)][(2,token1),(2,token2)]]
        poss_list = []
        for entry in id_dict:
            entry_list = []
            if len(id_dict[entry]) <= 0:
                return False
            else:
                for token in id_dict[entry]:
                    entry_list.append((entry,token))
                poss_list.append(entry_list)
        # make combinations
        combinations = list(itertools.product(*poss_list))
        # make combinations dictionaries
        # check relations for each combination
        found_combinations = []
        for combination in combinations:
            combination = dict(combination)
            relations_true = True
            for relation in self.relation_list:
                if relation[1] == 0: # Dependenz
                    if combination[relation[2]].attrib["dep_parent"] == "_":
                        relations_true = False
                        break
                    if combination[relation[0]] is not combination[relation[2]].getparent()[int(combination[relation[2]].attrib["dep_parent"])-1]:
                        relations_true = False
                        break # as soon as one relation is not true, we abort
                elif relation[1] == 1: # Position
                    if combination[relation[0]].getnext() is not combination[relation[2]]:
                        relations_true = False
                        break # as soon as one relation is not true, we abort
            if relations_true: # all relations match, we can save our find
                found_combinations.append(combination)
        return found_combinations
        
    
    @staticmethod
    def check_attribs(token, entry):
        if len(entry["lemma"]) > 0:
            if token.attrib["lemma"] != entry["lemma"]:
                return False
        if len(entry["dep"]) > 0:
            if token.attrib["dep_tag"] != entry["dep"]:
                return False
        if len(entry["word"]) > 0:
            if token.text != entry["word"]:
                return False
        if len(entry["POS"]) > 0:
            if not token.attrib["pos"].startswith(entry["POS"]):
                return False
        for attr, value in entry["custom"]:
            if token.attrib[attr] != value:
                return False
        return True 
        
                        
    def metadatafilter(self, pub, pubID):
        if pub:
            metadict = {}
            for child in pub[0]:
                if child.text is not None:
                    metadict[child.tag] = child.text
                else:
                    metadict[child.tag] = ""
            # check for author
            author = self.checkmeta(
                "Autor",
                "author",
                metadict)
            # check publication title
            title = self.checkmeta(
                "Publikation",
                "name",
                metadict)
            # check nation of origin
            origin = self.checkmeta(
                "Urspungsland",
                "nation",
                metadict)
            # check the publisher
            publisher = self.checkpublisher(
                "Herausgeber",
                "publisher",
                metadict)
            # check the date
            date = self.checkdate("date", metadict)
            if author and title and origin and publisher and date:
                return True
            else:
                return False
        else:
            print("No publication with ID {} found.".format(pubID))
            return False
            
            
    def checkdate(self, metaEntry, metadict):
        # get the user given date limits
        startday = self.earliest[0][0].get()
        startmonth = self.earliest[1][0].get()
        startyear = self.earliest[2][0].get()
        if startday == "" or startmonth == "" or startyear == "":
            return True
        endday = self.latest[0][0].get()
        endmonth = self.latest[1][0].get()
        endyear = self.latest[2][0].get()
        if endday == "" or endmonth == "" or endyear == "":
            return True
        try:
            start = datetime.date(int(startyear),int(startmonth),int(startday))
            end = datetime.date(int(endyear),int(endmonth),int(endday))
        except ValueError:
            messagebox.showerror(title="Ungültige Zeitspanne", message="Die Daten für die erlaubte Zeitspanne sind nicht zulässig. Bitte beachten Sie, dass die Daten im Format Tag/Monat/Jahr angegeben werden müssen.\nFür die weitere Bearbeitung wird das Kriterium der Zeispanne ignoriert.")
            return True
        metadate = metadict["date"]
        if metadate is None:
            return True # To change?
        metadates = metadate.split("-")
        # Check if a date range or a single date is given
        if len(metadates) == 1:
            metadates[0] = re.sub("[^\d\W]","",metadates[0])
            m = re.match("(\d\d)\/(\d\d)\/(\d{4})", metadates[0])
            if m:
                day = m.group(1)
                month = m.group(2)
                year = m.group(3)
            else:
                day = 1
                month = 7
                year = metadates[0]
            metadate = datetime.date(int(year),int(month),int(day))
            if start < metadate < end:
                return True
            else:
                return False
        elif len(metadates) == 2:
            metadates[0] = re.sub("[^\d\W]","",metadates[0])
            metadates[1] = re.sub("[^\d\W]","",metadates[1])
            m1 = re.match("(\d\d)\/(\d\d)\/(\d{4})", metadates[0])
            if m1:
                day = m.group(1)
                month = m.group(2)
                year = m.group(3)
                startdate = datetime.date(int(year),int(month),int(day))
            else:
                day = 1
                month = 1
                year = metadates[0]
                startdate = datetime.date(int(year),int(month),int(day))
            m2 = re.match("(\d\d)\/(\d\d)\/(\d{4})", metadates[1])
            if m2:
                day = m.group(1)
                month = m.group(2)
                year = m.group(3)
                enddate = datetime.date(int(year),int(month),int(day))
            else:
                day = 31
                month = 12
                year = metadates[1]
                enddate = datetime.date(int(year),int(month),int(day))
            Range = namedtuple('Range', ['start', 'end'])
            r1 = Range(start=startdate, end=enddate)
            r2 = Range(start=start, end=end)
            latest_start = max(r1.start, r2.start)
            earliest_end = min(r1.end, r2.end)
            overlap = (earliest_end - latest_start).days + 1
            if overlap > 0:
                return True
            else:
                return False
        else:
            print("Something went wrong when processing dates: Date format {} not recognized".format(' '.join(metadates)))
                
                
    def checkmeta(self, crit, metaEntry, metadict):
        searched, exact_match = self.meta_criterias[crit]
        searched = searched.get()
        exact_match = exact_match.get()
        if exact_match:
            if searched.lower() == metadict[metaEntry].lower():
                return True
            else:
                return False
        else:
            if self.remove_accents(searched.lower()) in self.remove_accents(metadict[metaEntry]).lower():
                return True
            else:
                return False


    def checkpublisher(self, crit, metaEntry, metadict):
        searched, exact_match = self.meta_criterias[crit]
        searched = searched.get()
        exact_match = exact_match.get()
        if exact_match:
            # This could be refined by tranforming dates to date objects,
            # then compare them as time objects
            appl = searched.lower()
            metalist = metadict[metaEntry].lower().split(", ")
            for meta in metalist:
                if appl == meta:
                    return True
            return False
        else:
            applist = self.remove_accents(searched).lower().split()
            meta = self.remove_accents(metadict[metaEntry]).lower()
            for appl in applist:
                if appl not in meta:
                    return False
            return True


    def delete_unneeded(self):
        new_search_list = []
        for pos in range(len(self.search_list)):
            # check if searchterm has any criterias or is part of a relation
            at_least_one_option_valid = False
            for entry in self.search_list[pos]:
                entry_valid = False
                for key, value in entry.items():
                    if key != "id" and len(value) > 0:
                        entry_valid = True
                        break
                if entry_valid:
                    at_least_one_option_valid = True
                    new_search_list.append(self.search_list[pos])
                    break
            if not at_least_one_option_valid:
                # check relations next
                relation_valid = False
                for relation in self.relation_list:
                    if relation[0] == self.search_list[pos][0]["id"] or relation[2] == self.search_list[pos][0]["id"]:
                        relation_valid = True
                        break
                if relation_valid:
                    new_search_list.append(self.search_list[pos])
        self.search_list = new_search_list
                    
                    
    def add(self):
        # add a new term to the list of terms
        new_term = {}
        self.options_list = []
        self.term_counter += 1
        new_term["id"] = self.term_counter
        self._get_searchterms(new_term)
        self.options_list.append(new_term)
        self.search_list.append(self.options_list)
        # add a new relation, if needed
        relation_type = self._relation.get()
        relation_target = self._target.get()
        relation_target = relation_target.split(":")[0]
        if relation_type != "No relation":
            new_relation = self.relation_normalizer(
                relation_type,
                relation_target,
                new_term["id"])
            self.relation_list.append(new_relation)
        self.update_usermessage(relation_type, relation_target, new_term["id"])
        self.update_terms(new_term)
        self._clear_search()
        #~ print(self.search_list)
        #~ print(self.relation_list)
        
    def update_terms(self, term):
        self.targets.append("{}:{}".format(str(term["id"]), repr(term)))
        self.tarMenu['menu'].delete(0, 'end')
        new_choices = self.targets
        for choice in new_choices:
            self.tarMenu['menu'].add_command(label=choice, command=lambda x=choice: self._target.set(x))
        
    def update_usermessage(self, relation, target, source):
        if relation == "No relation":
            new = "Added new token with ID {}.\n".format(source)
        elif relation == "is child of":
            new = "Added new token with ID {0}\n{0} is child of {1}.\n".format(
                source, target)
        elif relation == "is parent of":
            new = "Added new token with ID {0}\n{0} is parent of {1}.\n".format(
                source, target)
        elif relation == "is right of":
            new = "Added new token with ID {0}\n{0} is positioned to the right of {1}.\n".format(
                source, target)
        elif relation == "is left of":
            new = "Added new token with ID {0}\n{0} is positioned to the left of {1}.\n".format(
                source, target)
        elif relation == "OR":
            alternatives = []
            for option in target:
                alternatives.append(repr(option))
            new = "Added new token {0} as an alternative of {1}.\n".format(
                repr(source), ' and '.join(alternatives))
        self.user_info.insert(END, new)
        
    @staticmethod
    def relation_normalizer(reltype, target, source):
        target = int(target)
        if reltype == "is parent of":
            return (source, 0, target)
        elif reltype == "is child of":
            return (target, 0, source)
        elif reltype == "is left of":
            return (source, 1, target)
        elif reltype == "is right of":
            return (target, 1, source)
        
    def _get_searchterms(self, dct):
        dct["word"] = self.criteria["Wort"].get()
        dct["lemma"] = self.criteria["Lemma"].get()
        dct["POS"] = self.criteria["POS"].get()
        dct["dep"] = self.criteria["Dependenz"].get()
        dct["custom"] = self.custom_attributes
        
    def option(self):
        new_term = {}
        new_term["id"] = self.term_counter
        self._get_searchterms(new_term)
        self.update_usermessage("OR", self.options_list, new_term)
        self.options_list.append(new_term)
        self._clear_search()
        
    def reset(self):
        self._clear_search()
        self.search_list = []
        self.relation_list = []
        self.term_counter = 0
        self.targets = ["0:None"]
        self.user_info.delete(1.0,END)
        
        
    def _clear_search(self):
        for c in self.criteria:
            self.criteria[c].set("")
        self._case_sensitive_word.set(False)
        self._relation.set("No relation")
        self._target.set("0:None")
        self.custom_attributes = []
        
        
    def _create_meta(self):
        self.meta = Frame(self.root)
        meta_main = LabelFrame(self.meta, text="Metadaten")
        self._create_meta_main(meta_main)
        meta_main.grid(row=0, columnspan=1, padx=10, pady=5, sticky=W+E)
        timespan = LabelFrame(self.meta, text="Erlaubter Zeitraum")
        self._create_timespan(timespan)
        timespan.grid(row=1, column=0, padx=10, pady=5, sticky=W+E)
        
    def _create_meta_main(self, frame):
        self.meta_criterias = OrderedDict()
        self.meta_criterias["Autor"] = (StringVar(frame), BooleanVar(frame))
        self.meta_criterias["Publikation"] = (StringVar(frame), BooleanVar(frame))
        self.meta_criterias["Urspungsland"] = (StringVar(frame), BooleanVar(frame))
        self.meta_criterias["Herausgeber"] = (StringVar(frame), BooleanVar(frame))
        for n, (l, (v, b)) in enumerate(self.meta_criterias.items()):
            Label(frame, text=l+":").grid(row=n, column=0, sticky=W, padx=10)
            Entry(frame, textvariable=v).grid(row=n, column=1, columnspan=2, pady=5, padx=5, sticky=W+E)
            Checkbutton(frame, text="Nur exakte Treffer", variable=b).grid(row=n, column=3, sticky=W+E, padx=5)
    
    def _create_timespan(self, frame):
        self.earliest = [(StringVar(frame), 2), (StringVar(frame), 2), (StringVar(frame), 4)]
        self.latest = [(StringVar(frame), 2), (StringVar(frame), 2), (StringVar(frame), 4)]
        Label(frame, text="Frühestes Datum:").grid(row=0, column=0, sticky=W, padx=10, pady=5)
        Label(frame, text="Spätestes Datum:").grid(row=1, column=0, sticky=W, padx=10, pady=5)
        # ugly but for some reason won't work in the loop
        self.earliest[0][0].trace("w", lambda *args: self._character_limit(self.earliest[0][0], self.earliest[0][1]))
        self.earliest[1][0].trace("w", lambda *args: self._character_limit(self.earliest[1][0], self.earliest[1][1]))
        self.earliest[2][0].trace("w", lambda *args: self._character_limit(self.earliest[2][0], self.earliest[2][1]))
        for i in range(len(self.earliest)):
            e = Entry(frame, textvariable=self.earliest[i][0], width=self.earliest[i][1])
            e.grid(row=0, column=i+1, sticky=W+E)
        self.latest[0][0].trace("w", lambda *args: self._character_limit(self.latest[0][0], self.latest[0][1]))
        self.latest[1][0].trace("w", lambda *args: self._character_limit(self.latest[1][0], self.latest[1][1]))
        self.latest[2][0].trace("w", lambda *args: self._character_limit(self.latest[2][0], self.latest[2][1]))
        for i in range(len(self.latest)):
            e = Entry(frame, textvariable=self.latest[i][0], width=self.latest[i][1])
            e.grid(row=1, column=i+1, sticky=W+E)
        Label(frame, text="Format: TT/MM/JJJJ").grid(sticky=W+E, pady=5, padx=10)
        
    def _character_limit(self, entry_text, n):
        """Helper function to not allow more than n chars in Entry"""
        if len(entry_text.get()) > 0:
            entry_text.set(entry_text.get()[:n])
    
    def exit(self):
        exit()
        
    @staticmethod
    def remove_accents(input_str):
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

def main():
    new_search = Search()
    

if __name__ == "__main__":
    main()
