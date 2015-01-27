#Configuration information for Flask-WTForms
WTF_CSRF_ENABLED = True
f = open("secretkey.txt")
SECRET_KEY = f.read()
f.close()
del f
