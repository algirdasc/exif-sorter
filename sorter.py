#!/usr/bin/python2.7
# coding=utf-8

import exifread
import ConfigParser
import os
import datetime
import locale
import shutil
import hashlib
import sys


class ExifSorter(object):

    def __init__(self):

        config = ConfigParser.ConfigParser()
        config.readfp(open('sorter.ini'))

        self.config = config

        print "Setting locale {0}".format(self.config.get('options', 'locale'))
        try:
            locale.setlocale(locale.LC_ALL, self.config.get('options', 'locale'))
        except locale.Error, ex:
            print "Unknown locale. Try 'sudo dpkg-reconfigure locales'."
            exit(1)

        self.check_paths()

        for root, subdir, images in os.walk(self.config.get('path', 'source')):
            print "Entering {0}".format(root)

            for image in images:
                filename = os.path.join(root, image)
                print "\tParsing file {0}".format(filename)

                data = self.parse_exif(filename)
                if not data:
                    continue

                if self.config.getboolean('options', 'remove_duplicates'):
                    print "\t\tChecking for duplicates"
                    self.move_duplicates(filename, images, data)

                if self.config.getboolean('options', 'rotate'):
                    print "\t\tRotating image"
                    self.rotate_image(filename, data)

                if self.config.getboolean('options', 'move'):
                    print "\t\tMoving image"
                    self.move_image(filename, data)

    def check_paths(self):
        if not os.path.exists(self.config.get('path', 'source')):
            raise Exception('Source path "{0}" does not exists'.format(self.config.get('path', 'source')))

        if not os.path.exists(self.config.get('path', 'destination')):
            raise Exception('Destination path "{0}" does not exists'.format(self.config.get('path', 'destination')))

    def parse_exif(self, filename):
        exif = exifread.process_file(open(filename, 'rb'))

        if not exif:
            return None

        if not exif['Image DateTime']:
            return None

        dt = datetime.datetime.strptime(str(exif['Image DateTime']), '%Y:%m:%d %H:%M:%S')
        data = {
            'year': dt.strftime('%Y'),
            'month': dt.strftime('%m'),
            'literal_month': dt.strftime('%B').title(),
            'day': dt.strftime('%d'),
            'hour': dt.strftime('%H'),
            'minute': dt.strftime('%M'),
            'second': dt.strftime('%S'),
            'filename': os.path.basename(filename)
        }
        return data

    def parse_destination(self, data):
        fformat = self.config.get('options', 'filename')
        fformat = fformat.replace('%Y', data['year'])
        fformat = fformat.replace('%m', data['month'])
        fformat = fformat.replace('%d', data['day'])
        fformat = fformat.replace('%H', data['hour'])
        fformat = fformat.replace('%M', data['minute'])
        fformat = fformat.replace('%S', data['second'])
        fformat = fformat.replace('%f', data['filename'])
        fformat = fformat.replace('%B', data['literal_month'])
        return os.path.join(self.config.get('path', 'destination'), fformat)

    def move_duplicates(self, filename, images, data):
        my_hash = self.checksum(filename)
        for idx, image in enumerate(images):
            image_filename = os.path.join(os.path.dirname(filename), image)

            if filename == image_filename or not os.path.exists(image_filename):
                continue

            image_hash = self.checksum(image_filename)

            if image_hash == my_hash:
                destination_dir = os.path.join(os.path.dirname(self.create_destination(data)), '_duplicates')
                if not os.path.exists(destination_dir):
                    os.makedirs(destination_dir)
                shutil.move(image_filename, destination_dir)
            else:
                sys.stdout.write("\r\t\t{0} / {1}".format(idx, len(images)))
                sys.stdout.flush()

    def checksum(self, filename):
        hash_sha = hashlib.md5()
        with open(filename, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha.update(chunk)
        return hash_sha.hexdigest()

    def create_destination(self, data):
        destination = self.parse_destination(data)
        destination_dir = os.path.dirname(destination)
        if not os.path.exists(destination_dir):
            os.makedirs(destination_dir)
        return destination

    def move_image(self, filename, data):
        shutil.move(filename, self.create_destination(data))

    def rotate_image(self, filename, data):
        from PIL import Image, ExifTags
        try:
            image = Image.open(filename)
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break

            exif = dict(image._getexif().items())

            if exif[orientation] == 3:
                image = image.rotate(180, expand=True)
            elif exif[orientation] == 6:
                image = image.rotate(270, expand=True)
            elif exif[orientation] == 8:
                image = image.rotate(90, expand=True)

            image.save(filename)
            image.close()

        except (AttributeError, KeyError, IndexError):
            pass


if __name__ == '__main__':
    ExifSorter()
