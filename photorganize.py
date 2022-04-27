import argparse
import datetime
import hashlib
from pathlib import Path
from PIL import Image, UnidentifiedImageError
from PIL.ExifTags import TAGS
from pprint import pprint
import sys
import os

class Photo:
    def __init__(self, path):
        self.path = Path(path).expanduser().resolve()

        # to determine whether a photo is a duplicate of another,
        # we compare their filesize and hash, so we'll cache that
        stat = self.path.stat()
        self.size = stat.st_size
        self.hashes = {} # lazy, we'll calculate the hash only if needed
        
        # lets discover this photo's datetime
        # best case scenario, this photo has EXIF metadata with this information
        # but if not, we can attempt to extract this information from the filename
        # (common if, for example, it was previously organized by this script)
        # last case scenario, we can use the file's last modified date
        self.datetime = datetime.datetime.fromtimestamp(stat.st_mtime)
        self.datetime_src = "mtime"
        
        if len(self.path.stem) == 23:
            # maybe self.path.stem in the format "YYYY-MM-DD hh:mm:ss ###"
            # (the format used by this script for organized photos)
            # we could use a more accurate test here, but for our purposes this works
            try:
                self.datetime = datetime.datetime.fromisoformat(self.path.stem[:-4])
                self.datetime_src = "filename"
            except (ValueError):
                # we thought the filename would be a valid datetime, but apperantly not, oh well
                pass
        
        self.exif = {}
        try:
            with Image.open(self.path) as image:
                img_exif = image.getexif()
                
                if img_exif is not None:
                    for tag, value in img_exif.items():
                        decoded = TAGS.get(tag, tag)
                        self.exif[decoded] = value
        except (UnidentifiedImageError):
            # uh-uh, Pillow can't identify this file as being an image
            # nothing else we can do now about it
            return 

        # there are three tags we care about: DateTimeOriginal, DateTimeDigitized, DateTime
        # we prioritize them in that order, we have no guarantees if any actually exist
        datetime_str = None
        if 'DateTimeOriginal' in self.exif:
            datetime_str = self.exif['DateTimeOriginal']
        elif 'DateTimeDigitized' in self.exif:
            datetime_str = self.exif['DateTimeDigitized']
        elif 'DateTime' in self.exif:
            datetime_str = self.exif['DateTime']
        else:
            # uh-uh, no datetime on this photo's metadata
            # nothing else we can do now about it
            return
        
        try:
            self.datetime = datetime.datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
            self.datetime_src = "exif"
        except (ValueError):
            # uh-uh, datetime with an unexpected format
            # nothing else we can do now about it
            return
    
    def __lt__(self, other):
        if self.datetime != other.datetime:
            return self.datetime < other.datetime
        # these two photos have the same datetime!
        # in this case, we must look at the directory they're in: deeper directories should come first
        # (may feel a bit counter-intuitive, but this means that, for the same datetime,
        # photos inside directories are organized before photos from outside it are moved there)
        if len(self.path.parents) != len(other.path.parents):
            return len(self.path.parents) > len(other.path.parents)
        # these two photos are in the same directory!
        # not much we can do now, just order them based on their filename
        return self.path.name < other.path.name
        
    def get_hash(self, hash_algorithm="sha256"):
        if hash_algorithm not in self.hashes:
            # we need the hash for this photo, let's calculate it
            with open(self.path, 'rb') as f:
                d = f.read()
                self.hashes[hash_algorithm] = hashlib.new(hash_algorithm, d).hexdigest()
        
        return self.hashes[hash_algorithm]

        
    def is_duplicate_of(self, other, hash_algorithm="sha256"):
        """Checks wether self and other have equal contents, using their size and hash"""
        return (self.size == other.size) and (self.get_hash(hash_algorithm) == other.get_hash(hash_algorithm))



class Command:
    def execute(self):
        pass

    def simulate(self, simulacrum):
        pass

class MakeDirectory(Command):
    def __init__(self, directory):
        self.directory = Path(directory)
    
    def __repr__(self):
        return f"mkdir \"{str(self.directory)}\""

    def execute(self):
        if self.directory.exists():
            raise FileExistsError()
        self.directory.mkdir()

    def simulate(self, simulacrum):
        if self.directory in simulacrum:
            raise FileExistsError()
        simulacrum.append(self.directory)
        
class Move(Command):
    def __init__(self, source, dest):
        self.source = Path(source)
        self.dest = Path(dest)

    def __repr__(self):
        return f"mv \"{str(self.source)}\" \"{str(self.dest)}\""
    
    def execute(self, verbose=False):
        if not self.source.exists():
            raise FileNotFoundError()
        if self.dest.exists():
            raise FileExistsError()
        self.source.rename(self.dest)

    def simulate(self, simulacrum):
        if self.source not in simulacrum:
            raise FileNotFoundError()
        if self.dest in simulacrum:
            raise FileExistsError()
        simulacrum.append(self.dest)
        simulacrum.remove(self.source)
        
class Remove(Command):
    def __init__(self, target):
        self.target = Path(target)

    def __repr__(self):
        return f"rm \"{str(self.target)}\""
    
    def execute(self, verbose=False):
        if not self.target.exists():
            raise FileNotFoundError()
        if self.target.is_dir():
            raise IsADirectoryError()
        self.target.unlink()

    def simulate(self, simulacrum):
        if self.target not in simulacrum:
            raise FileNotFoundError()
        if len(self.target.suffixes) == 0:
            # rough heuristic that the given target is not a file
            # for the purposes of this script, it should work just fine 
            raise IsADirectoryError()
        simulacrum.remove(self.target)



class UserPrompter:
    def __init__(self, assume=None):
        self.assume = assume
        if self.assume is not None:
            self.assume = self.assume.lower()
    
    def datetime_uncertain(self, photo):
        answer = self.assume
        while answer not in ['k', 'i', 'a']:
            if answer is not None:
                # this is not the first attempt
                print("Unrecognized command, try again\n")
            
            print("We cannot accurately determine the date and time this photo has been taken:\n")
            print(f"File name      : {photo.path.name}")
            print(f"Path           : {photo.path.parent}")
            print(f"Datetime found : {photo.datetime.isoformat(sep=' ', timespec='seconds')}")
            print(f"Datetime source: {photo.datetime_src}")
            if len(photo.exif) == 0:
                print("EXIF: (empty)")
            else:
                print("EXIF:")
                for tag, value in photo.exif.items():
                        print(f"{tag:14}: {value}")
            
            answer = input("\nHow to proceed? [(k)eep as is/(i)nput new datetime/(a)bort] ")
            answer = answer.lower()

            if answer == 'i':
                datetime_input = input("Which datetime? [YYYY-MM-DD hh:mm:ss] ")
                try:
                    photo.datetime = datetime.datetime.fromisoformat(datetime_input)
                    photo.datetime_src = "user"
                except (ValueError):
                    # uh-uh, user didn't input datetime correctly
                    # let's just repeat
                    print("Not a valid datetime, try again\n")
                    answer = None
        
        if answer == 'a':
            sys.exit("Photo's datetime uncertain. Aborted.")
        else:
            return

    def duplicate_found(self, original, duplicate):
        answer = self.assume
        while answer not in ['k', 'd', 'a']:
            if answer is not None:
                # this is not the first attempt
                print("Unrecognized command, try again\n")

            print("The following file:\n")
            print(f"File name: {duplicate.path.name}")
            print(f"Path     : {duplicate.path.parent}")
            print(f"Size     : {duplicate.size}")
            for algorithm, hash_hex in duplicate.hashes.items():
                    print(f"{algorithm.upper():9}: {hash_hex}")
            print("\nHas been found to be a duplicate of another:\n")
            print(f"File name: {original.path.name}")
            print(f"Path     : {original.path.parent}")
            print(f"Size     : {original.size}")
            for algorithm, hash_hex in original.hashes.items():
                    print(f"{algorithm.upper():9}: {hash_hex}")
            
            answer = input("\nHow to proceed? [(k)eep duplicate/(d)elete duplicate/(a)bort] ")
            answer = answer.lower()
        
        if answer == 'k':
            return None
        elif answer == 'd':
            return Remove(duplicate.path)
        elif answer == 'a':
            sys.exit("Duplicate found. Aborted.")
                



class Broadcaster:
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def prepare_init(self, path):
        if self.verbose:
            print(f"Organizing photos in \"{str(path)}\"...")
    
    def prepare_found_dir(self, path):
        if self.verbose:
            print(f"Found child directory \"{str(path)}\"")
    
    def prepare_found_disorganized_photo(self, photo):
        if self.verbose:
            print(f"Found disorganized photo \"{str(photo.path)}\"")

    def prepare_found_organized_photo(self, photo):
        if self.verbose:
            print(f"Found organized photo \"{str(photo.path)}\"")

    def prepare_checking_duplicates(self, photo):
        if self.verbose:
            print(f"Checking for duplicates of \"{str(photo.path)}\"...")

    def prepare_found_duplicate(self, original, duplicate):
        if self.verbose:
            print(f"\"{str(duplicate.path)}\" is duplicate of \"{str(original.path)}\"")
    
    def simulate_init(self):
        if self.verbose:
            print("Running simulation of changes...")

    def simulate_success(self):
        if self.verbose:
            print("Simulation finished successfuly!")

    def execute_init(self):
        if self.verbose:
            print("Applying changes...")

    def execute_success(self):
        if self.verbose:
            print("All changes applied successfully!")
    
    def command(self, cmd):
        if self.verbose:
            print(cmd)
    
    def nothing_to_do(self):
        if self.verbose:
            print("No actions needed.")



class Organizer:
    def __init__(self, path, extentions=None, assume=None, hash_algorithm="sha256", verbose=False):
        self.path = Path(path).expanduser().resolve()
        self.hash_algorithm = hash_algorithm
        self.commands = []
        if extentions == None:
            self.extentions = ['.jpg', '.jpeg', '.png', '.gif']
        else:
            self.extentions = extentions
        self.prompter = UserPrompter(assume=assume)
        self.broadcaster = Broadcaster(verbose=verbose)
    
    def prepare(self, verbose=False):
        self.broadcaster.prepare_init(self.path)

        # find photos and dirs in path
        dirs = []
        disorganized_photos = {}
        for child in self.path.iterdir():
            if child.is_dir():
                self.broadcaster.prepare_found_dir(child)
                dirs.append(child)

            elif child.is_file() and child.suffix.lower() in self.extentions:
                photo = Photo(child)
                self.broadcaster.prepare_found_disorganized_photo(photo)
                if photo.datetime_src != "exif":
                    # we were not able to find the photos datetime with certainty
                    self.prompter.datetime_uncertain(photo)
                photo_month = datetime.date(photo.datetime.year, photo.datetime.month, 1)
                disorganized_photos.setdefault(photo_month, list()).append(photo)
        
        # check if there's existing dirs for the disorganised photos
        organized_photos = {}
        for month in disorganized_photos.keys():
            month_str = month.strftime("%Y-%m")
            organized_photos[month] = list()
            if Path(self.path, month_str) not in dirs:
                # add command to create missing directory
                self.commands.append(MakeDirectory(Path(self.path, month_str)))
            else:
                # we must check whether the disorganized photos are duplicates of the photos inside this month's directory
                for child in Path(self.path, month_str).iterdir():
                    if child.is_file() and child.suffix.lower() in self.extentions:
                        photo = Photo(child)
                        self.broadcaster.prepare_found_organized_photo(photo)
                        if photo.datetime_src != "exif":
                            # we were not able to find the photos datetime with certainty
                            self.prompter.datetime_uncertain(photo)
                        organized_photos[month].append(photo)
        
        # check for duplicates, keep only those that are unique
        unique_photos = {}
        for month, photos_for_month in disorganized_photos.items():
            for i, photo in enumerate(photos_for_month):
                self.broadcaster.prepare_checking_duplicates(photo)

                photo_is_duplicate = False
                # check for duplicates in previously organized photos
                for other in organized_photos[month]:
                    if photo.is_duplicate_of(other, hash_algorithm=self.hash_algorithm):
                        self.broadcaster.prepare_found_duplicate(other, photo)
                        photo_is_duplicate = True
                        remove_cmd = self.prompter.duplicate_found(other, photo)
                        if remove_cmd is not None:
                            self.commands.append(remove_cmd)
                        break
                
                # check for duplicates in the remaining photos
                for other in photos_for_month[:i]:
                    if photo.is_duplicate_of(other, hash_algorithm=self.hash_algorithm):
                        self.broadcaster.prepare_found_duplicate(other, photo)
                        photo_is_duplicate = True
                        remove_cmd = self.prompter.duplicate_found(other, photo)
                        if remove_cmd is not None:
                            self.commands.append(remove_cmd)
                        break

                if not photo_is_duplicate:
                    unique_photos.setdefault(month, list()).append(photo)
        
        # merge and order lists
        for month in unique_photos:
            unique_photos[month].extend(organized_photos[month])
            unique_photos[month].sort()
        
        # prepare move commands
        for month, photos_for_month in unique_photos.items():
            # photos should be renamed to the format YYYY-MM-DD hh:mm:ss ###,
            # where ### is used for the rare occasion where various photos were taken during the same second
            n = 1
            last_datetime_formatted = datetime.datetime.min.isoformat(sep=' ', timespec='seconds')
            for photo in photos_for_month:
                photo_datetime_formatted = photo.datetime.isoformat(sep=' ', timespec='seconds')
                # lets determine ###
                if last_datetime_formatted == photo_datetime_formatted:
                    # this photo was taken during the same second as the previous photo
                    n += 1
                else:
                    last_datetime_formatted = photo_datetime_formatted
                    n = 1
                
                dest = Path(self.path, month.strftime("%Y-%m"), f'{photo_datetime_formatted} {n:03}{photo.path.suffix}')
                if dest == photo.path:
                    # this photo already has the path we want, no need to make any changes
                    continue
                self.commands.append(Move(photo.path, dest))
            
        # with this we now have all the commands necessary to organize all photos

    def simulate(self):
        self.broadcaster.simulate_init()
        simulacrum = Organizer._create_simulacrum(self.path)
        # simulate commands
        for cmd in self.commands:
            self.broadcaster.command(cmd)
            cmd.simulate(simulacrum)
        self.broadcaster.simulate_success()
    
    def _create_simulacrum(path):
        # create simulacrum of file system (recursively) starting at path
        # it consists simply of a list contaning the path of each found file/dir
        simulacrum = []
        for child in path.iterdir():
            simulacrum.append(child)
            if child.is_dir():
                simulacrum.extend(Organizer._create_simulacrum(child))
        return simulacrum
    
    def execute(self):
        self.broadcaster.execute_init()
        for cmd in self.commands:
            self.broadcaster.command(cmd)
            cmd.execute()
        self.broadcaster.execute_success()
        
    def run(self, simulate_only=False):
        self.prepare()

        if len(self.commands) == 0:
            self.broadcaster.nothing_to_do()
            return
        
        self.simulate()

        if not simulate_only:
            self.execute()


def parse_args():
    parser = argparse.ArgumentParser(description="organize photo files in given path according to the date and time they were taken")

    parser.add_argument("path", help="Path to directory containing photo files to organize")
    parser.add_argument("-e", "--ext", help="The extensions of the files to organize (case insensitive). All files with different extentions will be ignored. Default is '.jpg .jpeg .png .gif'", nargs="+", default=['.jpg', '.jpeg', '.png', '.gif'])
    parser.add_argument("-a", "--assume", "--answer", help='Assume the given value as answer to all prompts and run non-interactively', choices=['a', 'k'])
    parser.add_argument("--hash", metavar="HASH", help='Which hash algorithm to use to check for duplicates, uses sha256 by default', choices=hashlib.algorithms_available, default="sha256")
    parser.add_argument("-s", "--simulate", "--dry-run", help="Perform a simulation of the events that would occur but do not actually make any changes", action="store_true")
    parser.add_argument("-v", "--verbose", help="Increase verbosity", action="store_true")

    return parser.parse_args()


def main():
    args = parse_args()
    organizer = Organizer(args.path, extentions=args.ext, assume=args.assume, hash_algorithm=args.hash, verbose=args.verbose)
    organizer.run(simulate_only=args.simulate)

if __name__=="__main__":
    main()
