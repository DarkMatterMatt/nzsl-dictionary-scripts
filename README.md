# nzsl-scripts

This repository holds scripts that are useful for the creation of the NZSL Android and iOS applications.

## python3

These scripts are written in Python 3 and will not work with Python 2.

If you are using OSX you can install it via

```
brew install python3
```

if you have not already done so.

Debian/Ubuntu users have access to the python3 command.

## Usage summary

```
cd /path/to/this/repo

# you must provide both AND android and an iOS path
python3 ./build-assets.py -i "/path/to/nzsl-dictionary-ios" -a "/path/to/nzsl-dictionary-android"
```

## build-assets.py

This is a wholistic script that performs all the steps needed to get all the necessary assets from the NZSL Freelex server. It does a number of steps:

* Step 1: Fetching the latest signs from Freelex
* Step 2: Fetching images from Freelex
* Step 3: Rename all images to meet Android requirements
* Step 4: Write out nzsl.dat for Android
* Step 5: Write out sqlite nzsl.db for iOS
* Step 6: Merge images together into one folder
* Step 7a: Update iOS app images
* Step 7b: Update iOS app nzsl.db
* Step 8a: Update Android app images
* Step 8b: Update Android app nzsl.dat
* Step 9: Cleanup (optional, requires -c flag)

To call the script you must provide the iOS and Android app base paths. The end result is your apps are updated with the latest sign databases and images, ready for building.

## freelex.py

Helper functions to interact with freelex and modify the files on the local file system.