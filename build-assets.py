#!/usr/bin/env python3
from optparse import OptionParser
import sys
import os
import re
import xml.etree.ElementTree as ET
import shutil

import freelex

def print_run_msg(msg):
    if options.verbose:
        print(" - Running: " + msg)

parser = OptionParser()
parser.add_option("-i", "--ios",
                  help="location of iOS app root", metavar="IOS_PATH")
parser.add_option("-a", "--android",
                  help="location of Android app root", metavar="ANDROID_PATH")
parser.add_option("-c", action="store_true", dest="cleanup", help="clean up files after execution")
parser.add_option("-v", "--verbose", action="store_true", help="increase verbosity")
parser.add_option("--skip", help="Skip step numbers")

(options, args) = parser.parse_args()

skip = [] if options.skip is None else options.skip.split(",")

filename = 'dnzsl-xmldump.xml'

if "1" not in skip:
    print("Step 1: Fetching the latest signs from Freelex")
    updated = freelex.update_database(filename)
    if updated == False:
        print("You're all up to date, no changes were made")
        sys.exit(0)

with open(filename) as f:
    data = f.read()
data = data.replace("\x05", "")
data = data.replace("<->", "")

# Replace ampersands, which are XML control characters, with
# the appropriate XML escape sequence
data = re.sub(r"&(?=[^#])", "&#038;", data)
parser = ET.XMLParser(encoding="UTF-8")
root = ET.XML(data, parser=parser)

if "2" not in skip:
    print("Step 2: Fetching images from freelex")
    freelex.fetch_assets(root, options.verbose)

if "4" not in skip:
    print("Step 4: Write out nzsl.dat for Android")
    freelex.write_datfile(root)

if "5" not in skip:
    print("Step 5: Write out sqlite nzsl.db for iOS")
    freelex.write_sqlitefile(root)

if "6" not in skip:
    print("Step 6: Merge images together into one folder")
    freelex.copy_images_to_one_folder()

    if "6a" not in skip:
        print("Step 6a: Generate search thumbnails")
        # Create thumbnails used on search screens
        for path, dirs, files in os.walk("assets/"):
            for filename in files:
                # Some images have a 1px border that looks bad in search results
                # Not all do - but we can safely trim 1px off all images
                shave_cmd = "mogrify -shave 1x1 assets/" + filename
                print_run_msg(shave_cmd)
                os.system(shave_cmd)

                # Then we make thumbnails of the border-free images
                create_thumbnail_cmd = "convert -resize x92 assets/" + filename + " assets/50." + filename
                print_run_msg(create_thumbnail_cmd)
                os.system(create_thumbnail_cmd)

    if "6b" not in skip:
        print("Step 6b: Shrink images for distribution")
        # In order to keep the app size small, we need to run a series
        # of compressions over the images

        # Resize images larger than 600x600 down using mogrify from imagemagick
        for path, dirs, files in os.walk("assets/"):
            for filename in files:
                cmd = "mogrify -resize '600x600>' assets/" + filename
                print_run_msg(cmd)
                os.system(cmd)

        # Convert all images to 4 colour depth
        for path, dirs, files in os.walk("assets/"):
            for filename in files:
                recolor_cmd = "convert -colors 4 assets/" + filename + " assets/" + filename
                print_run_msg(recolor_cmd)
                os.system(recolor_cmd)

        # Finally, run optipng
        for path, dirs, files in os.walk("assets/"):
            for filename in files:
                optipng_cmd = "optipng -quiet assets/" + filename
                print_run_msg(optipng_cmd)
                os.system(optipng_cmd)

if "7" not in skip and options.ios is not None:
    if "7a" not in skip:
        print("Step 7a: Update iOS app images")

        ios_asset_path = options.ios + "/Data/picture/"

        if os.path.isdir(ios_asset_path):
            shutil.rmtree(ios_asset_path)

        os.makedirs(ios_asset_path)

        # re-create the .gitkeep file in the assets dir (it is not necessary for the
        # app but keeps that dir in the git repo)
        os.system("touch " + ios_asset_path + ".gitkeep")

        for path, dirs, files in os.walk("assets/"):
            for filename in files:
                cp_cmd = "cp assets/" + filename + " " + ios_asset_path
                print_run_msg(cp_cmd)
                os.system(cp_cmd)

    if "7b" not in skip:
        print("Step 7b: Update iOS app nzsl.db")
        os.system("cp nzsl.db " + options.ios + "/Data/")

if "8" not in skip and options.android is not None:
    if "8a" not in skip:
        print("Step 8a: Update Android app images")
        android_asset_path = options.android + "/app/src/main/assets/images/signs/"

        if os.path.isdir(android_asset_path):
            shutil.rmtree(android_asset_path)

        os.makedirs(android_asset_path)

        # re-create the .gitkeep file in the assets dir (it is not necessary for the
        # app but keeps that dir in the git repo)
        os.system("touch " + android_asset_path + ".gitkeep")

        for path, dirs, files in os.walk("assets/"):
            for filename in files:
                cp_cmd = "cp assets/" + filename + " " + android_asset_path
                print_run_msg(cp_cmd)
                os.system(cp_cmd)

    if "8b" not in skip:
        print("Step 8b: Update Android app nzsl.dat")
        android_db_path = options.android + "/app/src/main/assets/db/"
        if not os.path.exists(android_db_path):
            os.makedirs(android_db_path)
        os.system("cp nzsl.dat " + android_db_path)

if options.cleanup:
    print("Step 9: Cleanup")
    os.remove("dnzsl-xmldump.xml")
    os.remove("nzsl.dat")
    os.remove("nzsl.db")
    shutil.rmtree("picture")
    shutil.rmtree("assets")
else:
    print("Skipping cleanup (see --help for how to enable it)")

print("Done")
