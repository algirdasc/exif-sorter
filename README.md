exif-sorter
-
This small python script reads JPEG image EXIF data, auto corrects orientation, removes duplicates and moves to folder by specified format (by default: year-month/day_hour_minute_filename.jpg, eg. 2017_05 July/02__13_30__IMG_0001.JPG).

----------


Install
-
> - sudo apt-get install libjpeg-dev python-exif python
> - sudo pip install exifread
> - sudo pip install cffi
> - sudo pip install jpegtran-cffi
