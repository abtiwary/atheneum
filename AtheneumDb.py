#!/usr/bin/env python

# AtheneumDb.py
# Defines a class around SQLite3 for Atheneum
#
# Principal Authors: Abhishek Tiwary
#                    ab.tiwary@gmail.com

import os
import sys
import json
import sqlite3


class AtheneumDb:
    def __init__(self, settings_file="./atheneum_settings.json"):
        self.settings_file = settings_file
        self.settings_dict = None
        self.dbpath = None
        self.dbconn = None
        self.dbcursor = None

        self._loadSettings()
        self._initDb()

    def _loadSettings(self):
        try:
            with open(self.settings_file, "rb") as fsettings:
                self.settings_dict = json.load(fsettings)
            self.dbpath = self.settings_dict["dbpath"]
        except Exception as e:
            print >> sys.stderr, "Exception while attempting to read {} : {}".format(self.settings_file, e)
            sys.exit(1)

    def _initDb(self):
        create_db = False if os.path.exists(self.dbpath) else True
        self.dbconn = sqlite3.connect(self.dbpath)
        self.dbcursor = self.dbconn.cursor()

        if create_db:
            self.dbcursor.execute('''CREATE TABLE IF NOT EXISTS
                books(id INTEGER PRIMARY KEY, title TEXT, subtitle TEXT, authors TEXT, publisher TEXT,
                        publisheddate TEXT, description TEXT, isbn10 TEXT, isbn13 TEXT, pagecount TEXT,
                        categories TEXT, smallthumbnail TEXT, thumbnail TEXT)
                ''')

            print "Created database with table 'books'"
        print

    def InsertIntoDb(self, *args, **kwargs):
        sisbn10 = None
        sisbn13 = None
        try:
            stitle = args[0].encode("utf-8").replace("'", "''") if args[0] is not None else ""
            ssubtitle = args[1].encode("utf-8").replace("'", "''") if args[1] is not None else ""
            sauthors = args[2].encode("utf-8").replace("'", "''") if args[2] is not None else ""
            spublisher = args[3].encode("utf-8").replace("'", "''") if args[3] is not None else ""
            spublisheddate = args[4].encode("utf-8").replace("'", "''") if args[4] is not None else ""
            sdescription = args[5].encode("utf-8").replace("'", "''") if args[5] is not None else ""
            sisbn10 = args[6].encode("utf-8").replace("'", "''") if args[6] is not None else ""
            sisbn13 = args[7].encode("utf-8").replace("'", "''") if args[7] is not None else ""
            spagecount = ("{}".format(args[8])).encode("utf-8").replace("'", "''") if args[8] is not None else ""
            scategories = args[9].encode("utf-8").replace("'", "''") if args[9] is not None else ""
            ssmallthumbnail = args[10].encode("utf-8").replace("'", "''") if args[10] is not None else ""
            sthumbnail = args[11].encode("utf-8").replace("'", "''") if args[11] is not None else ""

            self.dbcursor.execute("""INSERT INTO books VALUES(
                null, '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}',
                '{}', '{}', '{}', '{}')""".format(stitle, ssubtitle, sauthors, spublisher, spublisheddate,
                                                  sdescription, sisbn10, sisbn13, spagecount, scategories,
                                                  ssmallthumbnail, sthumbnail))

            self.dbconn.commit()
        except Exception as e:
            print >> sys.stderr, "Exception in {} - {}".format(sisbn13 if sisbn13 is not None else sisbn10, e)
        finally:
            return None

    def DeleteRowFromDb(self, id, tablename="books"):
        self.dbcursor.execute("""DELETE from '{}' where id='{}'""".format(tablename, id))
        self.dbconn.commit()

    def GetAllRows(self, tablename="books", sisbn10=None, sisbn13=None):
        if sisbn13 is not None:
            self.dbcursor.execute("SELECT * FROM books WHERE UPPER({}) like '{}'".format("isbn13", sisbn13))
        elif sisbn10 is not None:
            self.dbcursor.execute("SELECT * FROM books WHERE UPPER({}) like '{}'".format("isbn10", sisbn10))
        else:
            self.dbcursor.execute("SELECT * FROM '{}'".format(tablename))

        rows = self.dbcursor.fetchall()
        return rows

    def GetRowById(self, id, tablename="books"):
        self.dbcursor.execute("SELECT * FROM '{}' WHERE id='{}'".format(tablename, id))
        row = self.dbcursor.fetchall()
        if len(row) > 0:
            return row[0]
        return ""

    def PrintAllRows(self):
        rows = self.GetAllRows()
        for row in rows:
            print row
        print

    def SearchInDb(self, column, value, tablename="books"):
        value = "%" + value + "%"
        self.dbcursor.execute("""SELECT * FROM '{}' WHERE UPPER({}) like '{}'""".format(tablename, column, value))
        rows = self.dbcursor.fetchall()
        #for row in rows:
        #    print row
        return rows

    def UpdateColumnInDb(self, column, value, id, tablename="books"):
        self.dbcursor.execute("""UPDATE '{}' set {}='{}' where id='{}'""".format(tablename, column, value, id))
        self.dbconn.commit()




if __name__ == "__main__":
    athdb = AtheneumDb()
    print athdb.dbpath
