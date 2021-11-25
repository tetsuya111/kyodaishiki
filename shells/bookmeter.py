from . import book
from _kyodaishiki import __shell__
from . import util
from . import select2
from . import mecab
import os
import docopt
from bs4 import BeautifulSoup as bs
from myutil.site import bookmeter as bm
from myutil import site
import requests
import json
import re
import sys


HOST="bookmeter.com"
URL="https://"+HOST

class Attr(util.Attr):
	BMID="BM_ID"

class Mode:
	READ="R"
	READING="S"
	TSUNDOKU="T"
	WANT="W"
	ALL="RSTW"

HOME_F=None
class Url:
	USER=lambda userid:URL+"/users/{0}".format(userid)
	SEARCH_USERS=URL+"/users/search"
	SEARCH_F=None
	HOME_F=HOME_F
	READ_F=HOME_F # + ...
	READING_F=HOME_F # + ...	
	TSUNDOKU_F=HOME_F # + ...	
	WANT_F=HOME_F # + ...	


def append(db,name,mode="wish",tags=["WANT"],log=sys.stdout):
	user=bm.User.make(name)
	if not user:
		print("Don't find {0}.".format(name),file=log)
	for book_data in user.getBooks(mode,n=10**32):
		try:
			title=book_data["title"]
			title.encode().decode()
			title=re.sub("[\(\)]","_",title)
			book.appendTitleOfAuthor(db,book_data["author"],title)
		except Exception as e:
			print(e,book_data,file=log)
		else:
			words=mecab.Mecab.getWords(title)
			db.append(title,"",tags=(*tags,*words,Attr(Attr.BMID)(name),book.Tag.IS_BOOK))
	db.save()

		
class Docs:
	class DB:
		HELP="""
		Usage:
			help [(-a|--all)]
		"""
		APPEND="""
		Usage:
			append want <name>
			append read <name>
			append (sh|shi|shiori) [(-t <tags>)] [(-T <title>)] [(-a <author>)] [(-O|--override)]
			append (sh|shi|shiori) (l|list) <list_title> [(-m <memo>)] [(-t <tags>)] [(-T <title>)] [(-a <author>)] [(--pf <p_from>)] [(--pu <p_until>)]
			append related [(-t <tags>)] [(-T <title>)] [(-a <author>)] [(--rt <relatedTags>)] [(-O|--override)]
			append tag [(-t <tags>)] [(-m <memo>)] <tagsToAppend>... 

		Options:
			*** mode ***
			R -> READ
			S -> READING
			T -> TSUNDOKU 
			W -> WANT
		"""
		HELP_TEXT="""
			append
		"""
	HELP="""
		select <dbid>
	"""

class Command(util.Command):
	pass


class DBShell(book.DBShell):
	DEF_APPEND_MAX="100"
	def execQuery(self,query,output):
		if query.command in Command.HELP:
			try:
				args=docopt.docopt(Docs.DB.HELP,query.args)
			except SystemExit as e:
				print(e)
				return
			output.write(Docs.DB.HELP_TEXT+"\n")
			if args["-a"] or args["--all"]:
				return super().execQuery(query,output)
		elif query.command in Command.APPEND:
			try:
				args=docopt.docopt(Docs.DB.APPEND,query.args)
			except SystemExit as e:
				print(e)
				return
			FROM_BM="FROM_BOOKMETER"
			if args["want"]:	
				name=args["<name>"]
				append(self.db,name,"wish",tags=["WANT",FROM_BM])
			elif args["read"]:
				name=args["<name>"]
				append(self.db,name,"read",tags=["READ",FROM_BM])
			else:
				return super().execQuery(query,output)
		else:
			return super().execQuery(query,output)

class SiteShell(__shell__.BaseShell):
	def __init__(self,homeDB):
		self.homeDB=homeDB
		super().__init__()
	def execQuery(self,query,output):
		if query.command in Command.HELP:
			output.write(Docs.HELP+"\n")
		elif query.command in Command.DB.SELECT:
			if not query.args:
				output,write("	select <dbid>\n")
				return
			dbids=list(self.homeDB.getDBIDs(query.args[0].upper()))
			if not dbids:
				output.write("Don't find.\n")
				return
			dbid=dbids[0]
			db=self.homeDB.select(dbid)
			if not db:
				output.write("Don't find "+dbid+" .\n")
			shell=DBShell(db)
#exec alias.txt of select2 in homeDB
			all_alias=os.path.join(self.homeDB.dname,select2.AuHSShell.ALL_ALIAS_TXT)
			shell.execAliasf(all_alias,shell.null)
			return shell.start()
		else:
			return super().execQuery(query,output)
	def start(self):
		self.stdout.write("*** welcome to bookmeter ***\n")
		return super().start()

