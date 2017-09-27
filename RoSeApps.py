#!/usr/bin/python3

from RoSeData import htmlToStandardv5
from RoSeData import SpanishTaggerv4
from RoSeData import StandardToWebannov2
from RoSeData import ToStandardv3
from RoSeData import searchv4_1
from tkinter import *
import webbrowser

LAST_UPDATE = "02.08.2017"
VERSION = "0.3"

def htmlToStandard():
    with open("RoSe.log", mode="a") as log:
        log.write("Starting conversion of HTML files to one XML file.\n")
        new_conv = htmlToStandardv5.htmlToStandard()

def tagger():
    with open("RoSe.log", mode="a") as log:
        log.write("Starting Tagging process.\n")
        new_tagger = SpanishTaggerv4.Tagger()
        
def toWebanno():
    with open("RoSe.log", mode="a") as log:
        log.write("Starting Conversion from Standard to Webanno.\n")
        new_conv = StandardToWebannov2.ToWebanno()
    
def toStandard():
    with open("RoSe.log", mode="a") as log:
        log.write("Starting Conversion from Webanno to Standard.\n")
        new_conv = ToStandardv3.ToStandard()
    
def search():
    with open("RoSe.log", mode="a") as log:
        log.write("Starting Search Module.\n")
        new_search = searchv4_1.Search()
    
def more_info():
    webbrowser.open("http://www.rose.uzh.ch/de/forschung/dom.html")

def show_doc():
    webbrowser.open("RoSeData/Dokumentation.pdf")
    
def impressum():
    imp = Toplevel()
    imp.title("Impressum")
    imp.focus_force()
    info_text = """Diese Applikation wurde von Ismail Prada für das 
Romanische Seminar der Universität Zürich entwickelt."""
    last_update = "Diese Version wurde am {} geupdatet".format(LAST_UPDATE)
    version = "Die Versionsnummer dieser Applikation ist {}".format(VERSION)
    info = Label(imp, text=info_text, justify=LEFT).grid(pady=5, padx=5)
    vers = Label(imp, text=version, justify=LEFT).grid(pady=5, padx=5)
    update = Label(imp, text=last_update, justify=LEFT).grid(pady=5, padx=5)

def main():
    root = Tk()
    root.title("RoSe Applikationssammlung")
    menu = Menu(root)
    root.config(menu=menu)
    infomenu = Menu(menu)
    menu.add_cascade(label="Mehr Info", menu=infomenu)
    infomenu.add_command(label="Mehr Infos zum Projekt", command=more_info) # Link auf Projektseite
    infomenu.add_command(label="Zeige Dokumentation", command=show_doc) #Öffnet Dokumentation
    infomenu.add_command(label="Impressum", command=impressum)
    
    title_text = "RoSe Applikationen"
    title = Label(root, text=title_text, font="Verdana 20 bold").grid()
    
    intro_text = """Dieses Programm bietet Zugriff auf verschiedene Werkzeuge \nzur Arbeit am SNF-Projekts des Romanischen Seminars Zürich"""
    intro = Label(root, text=intro_text, font="Verdana", justify=LEFT).grid(padx=10)
    
    logo_img = PhotoImage(file="RoSeData/uzh_logo.png").subsample(2,2)
    logo = Label(root, image=logo_img, justify=RIGHT).grid(row=0, column=1,rowspan=2, padx=10, pady=10)
    
    buttons = [
        ("HTML \u21d2 XML", htmlToStandard),
        ("XML Taggen", tagger),
        ("XML \u21d2 Webanno", toWebanno),
        ("Webanno \u21d2 XML", toStandard),
        ("XML durchsuchen", search)
    ]
    
    for desc, func in buttons:
        new_button = Button(root, text=desc, command=func, padx=10, pady=10).grid(sticky=W+E)
    
    with open("RoSe.log", mode="w", encoding="utf-8") as log:
        log.write("Starting App...\n")
    
    mainloop()



if __name__ == "__main__":
    main()
