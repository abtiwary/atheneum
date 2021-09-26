#!/usr/bin/env python

# Atheneum.py
# A Flask based book catalog server
#
# Principal Authors: Abhishek Tiwary
#                    ab.tiwary@gmail.com

import os
import sys
import json
import urllib2
import socket

from flask import Flask, request, render_template
from collections import OrderedDict
from datetime import datetime
from AtheneumDb import AtheneumDb


class Atheneum:
    def __init__(self, local_ip=None):
        self.local_ip_address = local_ip if local_ip is not None else socket.gethostbyname(socket.gethostname())
        self.local_port = 9009
        self.path_static_dir = os.path.join(os.getcwd(), "static")
        self.path_images_dir = os.path.join(self.path_static_dir, "images")
        self.path_json = os.path.join(self.path_static_dir, "json")
        self.all_rows = []
        self.current_page = 0
        #self.nb_rows_per_page = 2
        self.nb_rows_per_page = 25

class AtheneumException(Exception): pass


ATH_OBJECT = Atheneum(local_ip="60.242.90.78")
ATHDB_OBJECT = AtheneumDb()

# SOME GLOBALS
LOCAL_IP_ADDRESS = ATH_OBJECT.local_ip_address
LOCAL_PORT = ATH_OBJECT.local_port
PATH_STATIC_DIR = ATH_OBJECT.path_static_dir
PATH_IMAGES_DIR = ATH_OBJECT.path_images_dir
PATH_JSON = ATH_OBJECT.path_json
ATH_OBJECT.all_rows = ATHDB_OBJECT.GetAllRows()

# helper functions
def GetJSONFromBooksAPI(isbn):
    path_isbn_json = None
    try:
        url = "https://www.googleapis.com/books/v1/volumes?q=isbn:{}".format(isbn)
        f = urllib2.Request(url, None, {'User-Agent' : 'Mozilla/5.0'})
        f.add_header('Cache-Control', 'max-age=0')
        with open(os.path.join(PATH_JSON, "{}.json".format(isbn)), "w+") as fjsonout:
            fjsonout.write(urllib2.urlopen(f).read())
        path_isbn_json = os.path.join(PATH_JSON, "{}.json".format(isbn))
    except Exception as e:
        print >> sys.stderr, "Exception in GetJSONFromBooksAPI() for ISBN {} - {}".format(isbn, e)
    finally:
        return path_isbn_json

def GetBookThumbnails(isbn, smallthumbnail, thumbnail):
    smallthumbnail_png = os.path.join(PATH_IMAGES_DIR, "{}_small.png".format(isbn))
    thumbnail_png = os.path.join(PATH_IMAGES_DIR, "{}.png".format(isbn))
    try:
        if smallthumbnail is not None:
            f = urllib2.Request(smallthumbnail, None, {'User-Agent' : 'Mozilla/5.0'})
            f.add_header('Cache-Control', 'max-age=0')
            with open(smallthumbnail_png, "wb") as fpngout:
                fpngout.write(urllib2.urlopen(f).read())
        if thumbnail is not None:
            f = urllib2.Request(thumbnail, None, {'User-Agent' : 'Mozilla/5.0'})
            f.add_header('Cache-Control', 'max-age=0')
            with open(thumbnail_png, "wb") as fpngout:
                fpngout.write(urllib2.urlopen(f).read())

    except Exception as e:
        print >> sys.stderr, "Exception in GetJSONFromBooksAPI() for ISBN {} - {}".format(isbn, e)

    finally:
        return ("static/images/{}_small.png".format(isbn), "static/images/{}.png".format(isbn))

def DoesPreviousPageExist():
    if ATH_OBJECT.current_page > 0:
        return (True, ATH_OBJECT.current_page - 1)
    else:
        return (False, ATH_OBJECT.current_page)

def DoesNextPageExist():
    total_row_size = len(ATH_OBJECT.all_rows)
    current_page = ATH_OBJECT.current_page
    if total_row_size > ((current_page + 1) * ATH_OBJECT.nb_rows_per_page):
        return (True, ATH_OBJECT.current_page + 1)
    else:
        return (False, ATH_OBJECT.current_page)

def GetPageRows(page_number):
    page_rows = ATH_OBJECT.nb_rows_per_page
    start = page_number * page_rows
    end = start + page_rows
    current_rows = ATH_OBJECT.all_rows[start:end]
    ATH_OBJECT.current_page = page_number
    return current_rows

# perhaps add an Atheneum class, a "book" factory and a "global" list of rows for pagination

app = Flask(__name__)

@app.route('/')
def index():
    render_dict = {}
    render_dict["localip"] = LOCAL_IP_ADDRESS
    render_dict["port"] = LOCAL_PORT
    return render_template("mainpage.html", render_dict=render_dict)

@app.route("/showall")
def showall():
    render_dict = {}
    render_dict["localip"] = LOCAL_IP_ADDRESS
    render_dict["port"] = LOCAL_PORT
    rows = GetPageRows(0)
    bpp, pp = DoesPreviousPageExist()
    bnp, np = DoesNextPageExist()
    render_dict["rows"] = rows
    render_dict["previous_page"] = bpp
    render_dict["previous_page_number"] = pp
    render_dict["next_page"] = bnp
    render_dict["next_page_number"] = np
    return render_template("allitems.html", render_dict=render_dict)

@app.route("/getpage", methods=['GET', 'POST'])
def getpage():
    render_dict = {}
    render_dict['localip'] = LOCAL_IP_ADDRESS
    render_dict['port'] = LOCAL_PORT
    if request.method == 'GET':
        pagenumber = request.args.get("pagenumber")
        pagenumber = int(pagenumber)
        rows = GetPageRows(pagenumber)
        render_dict["rows"] = rows
        ATH_OBJECT.current_page = pagenumber
        bpp, pp = DoesPreviousPageExist()
        bnp, np = DoesNextPageExist()
        render_dict["previous_page"] = bpp
        render_dict["previous_page_number"] = pp
        render_dict["next_page"] = bnp
        render_dict["next_page_number"] = np
        return render_template("allitems.html", render_dict=render_dict)

@app.route("/deleteid", methods=['GET', 'POST'])
def deleteid():
    render_dict = {}
    temp_url = "http://{}:{}/showall".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
    id = None
    if request.method == 'GET':
        id = request.args.get("id")
        if id is not None:
            ATHDB_OBJECT.DeleteRowFromDb(id)
            info_str = "Deleted!"
            link_str = temp_url
            render_dict["info_str"] = info_str
            render_dict["link_str"] = link_str
            ATH_OBJECT.all_rows = ATHDB_OBJECT.GetAllRows()
            return render_template("autopageupdate.html", render_dict=render_dict)

    info_str = "Invalid!"
    link_str = temp_url
    render_dict["info_str"] = info_str
    render_dict["link_str"] = link_str
    return render_template("autopageupdate.html", render_dict=render_dict)

@app.route("/addbook")
def adddevice():
    render_dict = {}
    render_dict["localip"] = LOCAL_IP_ADDRESS
    render_dict["port"] = LOCAL_PORT
    return render_template("addbook.html", render_dict=render_dict)

@app.route("/bookadd", methods=['GET', 'POST'])
def bookadd():
    render_dict = {}
    jsonfile = None
    info_keys = ["title", "subtitle", "authors", "publisher", "publishedDate", "description",
                 "industryIdentifiers", "pageCount", "categories", "imageLinks", ]
    bookinfo_dictionary = {}
    if request.method == "POST":
        bookisbn = request.form["isbn"]
        bookisbn = bookisbn.strip()
        if bookisbn != "":
            jsonfile = GetJSONFromBooksAPI(bookisbn)
            if jsonfile is not None:
                jsonobj = None
                with open(jsonfile, "rb") as fjsonin:
                    jsonobj = json.load(fjsonin)

                try:
                    totalitems = jsonobj["totalItems"]
                    if int(totalitems) == 0:
                        raise AtheneumException("Bad ISBN result!")
                    else:
                        bookinfo = jsonobj["items"][0]["volumeInfo"]
                        for infokey in info_keys:
                            if infokey == "authors" and infokey in bookinfo:
                                bookinfo_dictionary["authors"] = ", ".join(x for x in bookinfo["authors"])
                            elif infokey == "industryIdentifiers" and infokey in bookinfo:
                                for iid in bookinfo["industryIdentifiers"]:
                                    if "type" in iid and "identifier" in iid:
                                        iid_type = iid["type"].lower().strip()
                                        if "isbn" in iid_type and "13" in iid_type:
                                            bookinfo_dictionary["isbn13"] = iid["identifier"]
                                        elif "isbn" in iid_type and "10" in iid_type:
                                            bookinfo_dictionary["isbn10"] = iid["identifier"]
                                        else:
                                            pass
                            elif infokey == "categories" and infokey in bookinfo:
                                bookinfo_dictionary["categories"] = ", ".join(x for x in bookinfo["categories"])
                            elif infokey == "publishedDate" and infokey in bookinfo:
                                bookinfo_dictionary["publisheddate"] = bookinfo[infokey]
                            elif infokey == "pageCount" and infokey in bookinfo:
                                bookinfo_dictionary["pagecount"] = bookinfo[infokey]
                            elif infokey == "imageLinks" and infokey in bookinfo:
                                if "smallThumbnail" in bookinfo[infokey]:
                                    bookinfo_dictionary["smallthumbnail"] = bookinfo[infokey]["smallThumbnail"]
                                else:
                                    bookinfo_dictionary["smallthumbnail"] = None
                                if "thumbnail" in bookinfo[infokey]:
                                    bookinfo_dictionary["thumbnail"] = bookinfo[infokey]["thumbnail"]
                                else:
                                    bookinfo_dictionary["thumbnail"] = None
                            else:
                                if infokey in bookinfo:
                                    bookinfo_dictionary[infokey] = bookinfo[infokey]
                                else:
                                    bookinfo_dictionary[infokey] = None

                    print bookinfo_dictionary
                    stpng, tpng = GetBookThumbnails(bookisbn,
                                      bookinfo_dictionary["smallthumbnail"] if "smallthumbnail" in bookinfo_dictionary else None,
                                      bookinfo_dictionary["thumbnail"] if "thumbnail" in bookinfo_dictionary else None)

                    # check that a book with either isbn10 or isbn13 does not already exist
                    isbn_10 = bookinfo_dictionary["isbn10"]
                    isbn10_rows = None
                    if isbn_10 is not None:
                        isbn10_rows = ATHDB_OBJECT.SearchInDb("isbn10", isbn_10)

                    isbn_13 = bookinfo_dictionary["isbn13"]
                    isbn13_rows = None
                    if isbn_13 is not None:
                        isbn13_rows = ATHDB_OBJECT.SearchInDb("isbn13", isbn_13)

                    if ((isbn_10 is not None and len(isbn10_rows) > 0) or
                        (isbn_13 is not None and len(isbn13_rows) > 0)
                    ):
                        # an entry already exists
                        render_dict["info_str"] = "Cannot add a book as one with this ISBN already exists!"
                        render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
                        return render_template("autopageupdate.html", render_dict=render_dict)
                    else:
                        ATHDB_OBJECT.InsertIntoDb(bookinfo_dictionary["title"], bookinfo_dictionary["subtitle"],
                                                  bookinfo_dictionary["authors"], bookinfo_dictionary["publisher"],
                                                  bookinfo_dictionary["publisheddate"], bookinfo_dictionary["description"],
                                                  bookinfo_dictionary["isbn10"], bookinfo_dictionary["isbn13"],
                                                  bookinfo_dictionary["pagecount"], bookinfo_dictionary["categories"],
                                                  stpng, tpng)
                        ATH_OBJECT.all_rows = ATHDB_OBJECT.GetAllRows()
                        render_dict["info_str"] = "Book with ISBN {} added!".format(bookisbn)
                        render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
                        return render_template("autopageupdate.html", render_dict=render_dict)

                except Exception as e:
                    render_dict["info_str"] = e
                    render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
                    return render_template("autopageupdate.html", render_dict=render_dict)

            return jsonfile
        else:
            render_dict["info_str"] = "Invalid ISBN!" # Todo: redirect to bookaddmanual
            render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
            return render_template("autopageupdate.html", render_dict=render_dict)
    return ""


@app.route("/addbookmanually", methods=['GET', 'POST'])
def addbookmanually():
    render_dict = {}
    render_dict["localip"] = LOCAL_IP_ADDRESS
    render_dict["port"] = LOCAL_PORT
    return render_template("addbookmanually.html", render_dict=render_dict)

@app.route("/bookaddmanually", methods=['GET', 'POST'])
def bookaddmanually():
    render_dict = {}

    submit_dict = OrderedDict()
    submit_dict["title"] = None
    submit_dict["subtitle"] = None
    submit_dict["authors"] = None
    submit_dict["publisher"] = None
    submit_dict["publisheddate"] = None
    submit_dict["description"] = None
    submit_dict["isbn10"] = None
    submit_dict["isbn13"] = None
    submit_dict["pagecount"] = None
    submit_dict["categories"] = None
    submit_dict["smallthumbnail"] = None
    submit_dict["thumbnail"] = None

    temp_url = "http://{}:{}/showall".format(LOCAL_IP_ADDRESS, LOCAL_PORT)

    if request.method == "POST":
        try:
            for k, v in submit_dict.iteritems():
                submit_dict[k] = request.form[k]

            # check that a book with either isbn10 or isbn13 does not already exist
            isbn_10 = submit_dict["isbn10"]
            isbn10_rows = None
            if isbn_10 is not None or isbn_10.strip() != "":
                isbn10_rows = ATHDB_OBJECT.SearchInDb("isbn10", isbn_10)

            isbn_13 = submit_dict["isbn13"]
            isbn13_rows = None
            if isbn_13 is not None or isbn_13.strip() != "":
                isbn13_rows = ATHDB_OBJECT.SearchInDb("isbn13", isbn_13)

            if ((isbn_10 is not None and len(isbn10_rows) > 0) or
                (isbn_13 is not None and len(isbn13_rows) > 0)
            ):
                # an entry already exists
                render_dict["info_str"] = "Cannot add a book as one with this ISBN already exists!"
                render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
                return render_template("autopageupdate.html", render_dict=render_dict)

            else:
                ATHDB_OBJECT.InsertIntoDb(submit_dict["title"], submit_dict["subtitle"],
                                          submit_dict["authors"], submit_dict["publisher"],
                                          submit_dict["publisheddate"], submit_dict["description"],
                                          submit_dict["isbn10"], submit_dict["isbn13"],
                                          submit_dict["pagecount"], submit_dict["categories"],
                                          submit_dict["smallthumbnail"], submit_dict["thumbnail"])
                ATH_OBJECT.all_rows = ATHDB_OBJECT.GetAllRows()
                render_dict["info_str"] = "Book with ISBN {} {} added!".format(isbn_10, isbn_13)
                render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
                return render_template("autopageupdate.html", render_dict=render_dict)

        except Exception as e:
            render_dict["info_str"] = e
            render_dict["link_str"] = "http://{}:{}/".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
            return render_template("autopageupdate.html", render_dict=render_dict)

@app.route("/regenjson")
def regenjson():
    path_actb_json_file = os.path.join(PATH_STATIC_DIR, "actb_arrays.json")
    render_dict = {}

    jsonobj = {}
    jsonobj["words"] = []

    # sets to hold unique values
    set_words = set([])

    # get all rows from
    rows = ATHDB_OBJECT.GetAllRows()
    
    try:
        for row in rows:
            for item in row:
                set_words.add(str(item))
    except: 
        pass 

    jsonobj["words"] = [x for x in set_words]

    with open(path_actb_json_file, "w+") as foutjson:
        json.dump(jsonobj, foutjson)

    info_str = "{} rewritten!".format(path_actb_json_file)
    link_str = "http://{}:{}".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
    render_dict["info_str"] = info_str
    render_dict["link_str"] = link_str
    return render_template("autopageupdate.html", render_dict=render_dict)

@app.route("/search")
def search():
    render_dict = {}
    render_dict["localip"] = LOCAL_IP_ADDRESS
    render_dict["port"] = LOCAL_PORT
    return render_template("search.html", render_dict=render_dict)

@app.route("/submitsearch", methods=['GET', 'POST'])
def submitsearch():
    render_dict = {}
    render_dict["localip"] = LOCAL_IP_ADDRESS
    render_dict["port"] = LOCAL_PORT

    searchtext = None
    column = None
    if request.method == "POST":
        searchtext = request.form["searchtext"]
        column = request.form["column"]
        if searchtext is not None and column is not None:
            searchtext = searchtext.upper()
            column = column.lower()
            rows = ATHDB_OBJECT.SearchInDb(column, searchtext)
            render_dict["rows"] = rows
            return render_template("allitems.html", render_dict=render_dict)

    info_str = "Not found!"
    link_str = "http://{}:{}".format(LOCAL_IP_ADDRESS, LOCAL_PORT)
    render_dict["info_str"] = info_str
    render_dict["link_str"] = link_str
    return render_template("autopageupdate.html", render_dict=render_dict)




if __name__ == "__main__":
    app.jinja_env.cache = {}
    app.run(host="0.0.0.0", port=LOCAL_PORT)
