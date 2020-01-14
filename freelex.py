import sys
import os
import hashlib
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import re
import shutil
import sqlite3

def update_database(fname):
    r = urllib.request.urlopen('http://freelex.nzsl.vuw.ac.nz/dnzsl/freelex/publicsearch?xmldump=1')
    rread = r.read()
    new_hash = hashlib.sha512(rread).hexdigest()
    
    if os.path.exists(fname):
        with open(fname, "rb") as f:
            old_hash = hashlib.sha512(f.read()).hexdigest()
        if new_hash == old_hash:
            return False

    with open(fname, "wb") as f:
        f.write(rread)
    return True

def fetch_assets(root, verbose):
    for entry in root.iter("entry"):
        if verbose:
            print(entry.find("headword").text)
        for asset in entry.find("ASSET"):
            if ("picture" == asset.tag):
                fname = "picture/" + normalise_filename(asset.text)
                if not os.path.exists(fname):
                    try:
                        os.makedirs(os.path.dirname(fname))
                    except IOError:
                        pass
                    r = urllib.request.urlopen("http://freelex.nzsl.vuw.ac.nz/dnzsl/freelex/assets/" + urllib.parse.quote(asset.text))
                    with open(fname, "wb") as f:
                        f.write(r.read())
                asset.text = fname

def normalise_filename(old_fname):
    new_fname = old_fname.replace("-", "_").lower()
    num_of_periods = new_fname.count(".")
    if (num_of_periods > 1):
        new_fname = new_fname.replace(".", "_", num_of_periods - 1)
    return new_fname

def process_entry(entry):
    id       = entry.attrib["id"]
    headword = entry.find("headword").text
    mapping  = {
        "glossmain":  "glossmain",
        "sec":        "glosssecondary",
        "maori":      "glossmaori",
        "picture":    "ASSET/picture",
        "video":      "ASSET/glossmain",
        "handshape":  "handshape",
        "location":   "location",
        "categories": "HEADWORDTAGS",
    }
    
    d = {}
    for key, value in mapping.items():
        elem = entry.find(value)
        if elem is None:
            if key not in ["sec", "maori"]:
                print("{} missing {}".format((id, headword), key))
            d[key] = ""
        else:
            d[key] = elem.text
            
    if d["picture"]:
        d["picture"] = os.path.basename(d["picture"])
    if d["video"]:
        d["video"] = "http://freelex.nzsl.vuw.ac.nz/dnzsl/freelex/assets/" + d["video"].replace(".webm", ".mp4")
    
    d["norm_glossmain"] = normalise(d["glossmain"])
    d["norm_sec"]       = normalise(d["sec"])
    d["norm_maori"]     = normalise(d["maori"])
    
    d["norm_words_glossmain"] = re.sub(r"[^\w']+", "|", d["norm_glossmain"]).strip("|")
    d["norm_words_sec"]       = d["norm_sec"].replace(", ", "|")
    d["norm_words_maori"]     = d["norm_maori"].replace(", ", "|")
    d["categories"]           = re.sub(r",(?=[^ ])", "|", normalise(d["categories"]))
    
    d["target"] = "|".join((d["norm_glossmain"], d["norm_sec"], d["norm_maori"]))
    assert all(32 <= ord(x) < 127 for x in d["target"]), d["target"]
        
    return d

def write_datfile(root):
    with open("nzsl.dat", "w") as f:
        for entry in root.iter("entry"):
            d = process_entry(entry)
                
            print("\t".join((
                d["glossmain"],
                d["sec"],
                d["maori"],
                d["picture"],
                d["video"],
                d["handshape"],
                d["location"],
                d["categories"],
                d["norm_glossmain"],
                d["norm_words_glossmain"],
                d["norm_sec"],
                d["norm_words_sec"],
                d["norm_maori"],
                d["norm_words_maori"],
            )), file=f)

def write_sqlitefile(root):
    if os.path.exists("nzsl.db"):
        os.unlink("nzsl.db")
    db = sqlite3.connect("nzsl.db")
    db.execute("create table words (gloss, minor, maori, picture, video, handshape, location, categories, target)")
    for entry in root.iter("entry"):
        d = process_entry(entry)
        db.execute("insert into words values (?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            d["glossmain"],
            d["sec"],
            d["maori"],
            d["picture"],
            d["video"],
            d["handshape"],
            d["location"],
            d["categories"],
            d["target"],
        ))
    db.commit()
    db.close()

def copy_images_to_one_folder():
    if (os.path.isdir("assets")):
        shutil.rmtree("assets")
    os.makedirs("assets")
    os.system("cp picture/*/*.png assets/ 2>/dev/null")

# Helper functions
def normalise(s):
    return (s.lower()
             .replace("ā", "a")
             .replace("ē", "e")
             .replace("é", "e")
             .replace("ī", "i")
             .replace("ō", "o")
             .replace("ū", "u"))

