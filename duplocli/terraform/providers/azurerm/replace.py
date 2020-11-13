
import psutil
import os
import datetime
import argparse


# replace
filenames=["main.tf.json","variables.tf.json","terraform.tfvars.json"]



def replaceInfiles(text_src, text_dest):
    for filename in filenames:
        replaceInfile(filename, text_src, text_dest)

def replaceInfile(filename, text_src, text_dest):
    text_src = text_src.strip()
    text_dest = text_dest.strip()
    if isBlank(text_src) or isBlank(text_dest):
        raise Exception("Error: text to replace should not be empty src='{0}' dest='{1}'".format(text_src,text_dest))
    jsonstr=read_file(filename)
    jsonstr = jsonstr.replace(text_src, text_dest)
    save_file(filename, jsonstr)

def isBlank (stringVal):
    if stringVal and stringVal.strip(): # is not empty or blank
        return False
    return True

def read_file(filename):
    with open (filename, "r") as myfile:
        data = myfile.read()
    return data

def save_file(filename, data):
    with open (filename, "w") as myfile:
        myfile.write(data)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-s", "--src", required=True,
                    help="src: text to replace. \n python replace.py --src duploservices --dest tfsvs"
                         + "\n python replace.py --src azdemo1 --dest tftenant20 ")
    ap.add_argument("-d", "--dest", required=True,
                    help="dest: text to replace with \n python replace.py --src duploservices --dest tfsvs"
                         + "\n python replace.py --src azdemo1 --dest tftenant20")
    args = vars(ap.parse_args())
    text_src = args["src"]
    text_dest = args["dest"]

    replaceInfiles(text_src, text_dest)

