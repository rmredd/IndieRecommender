import MySQLdb as mdb

def login_mysql(loginfile):
    f = open(loginfile)
    login_text = f.read()
    f.close()
    login = login_text.split()
    con = mdb.connect(login[0],login[1],login[2],'indiedb')
    return con

def get_apikey(filename):
    f = open(filename)
    apikey = f.readline()
    f.close()
    return apikey
