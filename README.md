# Photorganize

A short and simple script to automatically organize all photos of a directory, grouping them by month and renaming them based on the time they were taken.  
Upon re-running the script on the same directory (say, after taking some more photos and placing them there), it will correctly organize the new photos into the previously organizes groups, if need arise.

The script will also identify duplicate photo files using SHA256 (by default), and will not organize those duplicates - you decide whether you want the script to delete them outright or just not touch them at all.

It uses [Pillow](https://python-pillow.org/) to read each photo's EXIF metadata to determine when they were taken. In case the photo does not have the required EXIF fields, then it will use the photo's last modified time, but will ask you whether you want to keep that as is or input the correct date and time it was taken.

## Usage

Install dependencies with
```sh
$ make init
```
Then run the script with
```sh
$ python3 photorganize.py path/to/photos
```
You can find more options with
```sh
$ python3 photorganize.py -h
```

## Example

```sh
$ tree Photos
Photos
├── P_20220216_235612.jpg
├── P_20220217_235452.jpg
├── P_20220218_143936.jpg
├── P_20220222_103238.jpg
├── P_20220222_161647.jpg
├── P_20220222_162632.jpg
├── P_20220222_204614.jpg
├── P_20220223_172900.jpg
├── P_20220225_161150.jpg
├── P_20220225_212624.jpg
├── P_20220225_213128.jpg
├── P_20220228_090145.jpg
├── P_20220228_155645.jpg
├── P_20220302_233636.jpg
├── P_20220303_210511.jpg
├── P_20220304_133019.jpg
├── P_20220304_133108.jpg
├── P_20220306_124820.jpg
├── P_20220306_140712.jpg
├── P_20220312_204134.jpg
├── P_20220403_114730.jpg
├── P_20220404_155606.jpg
├── P_20220404_155617.jpg
├── P_20220404_155631.jpg
├── P_20220404_155636.jpg
├── P_20220404_155652.jpg
├── P_20220404_155657.jpg
├── P_20220404_155702.jpg
├── P_20220404_155716.jpg
├── P_20220406_104626.jpg
└── P_20220408_185336.jpg

0 directories, 31 files
$ python3 photorganize.py Photos/ 
$ tree Photos
Photos
├── 2022-02
│   ├── 2022-02-16 23:56:12 001.jpg
│   ├── 2022-02-17 23:54:52 001.jpg
│   ├── 2022-02-18 14:39:37 001.jpg
│   ├── 2022-02-22 10:32:38 001.jpg
│   ├── 2022-02-22 16:16:47 001.jpg
│   ├── 2022-02-22 16:26:32 001.jpg
│   ├── 2022-02-22 20:46:14 001.jpg
│   ├── 2022-02-23 17:29:00 001.jpg
│   ├── 2022-02-25 16:11:50 001.jpg
│   ├── 2022-02-25 21:26:24 001.jpg
│   ├── 2022-02-25 21:31:28 001.jpg
│   ├── 2022-02-28 09:01:45 001.jpg
│   └── 2022-02-28 15:56:45 001.jpg
├── 2022-03
│   ├── 2022-03-02 23:36:36 001.jpg
│   ├── 2022-03-03 21:05:11 001.jpg
│   ├── 2022-03-04 13:30:19 001.jpg
│   ├── 2022-03-04 13:31:08 001.jpg
│   ├── 2022-03-06 12:48:20 001.jpg
│   ├── 2022-03-06 14:07:12 001.jpg
│   └── 2022-03-12 20:41:34 001.jpg
└── 2022-04
    ├── 2022-04-03 11:47:30 001.jpg
    ├── 2022-04-04 15:56:06 001.jpg
    ├── 2022-04-04 15:56:17 001.jpg
    ├── 2022-04-04 15:56:31 001.jpg
    ├── 2022-04-04 15:56:37 001.jpg
    ├── 2022-04-04 15:56:52 001.jpg
    ├── 2022-04-04 15:56:57 001.jpg
    ├── 2022-04-04 15:57:02 001.jpg
    ├── 2022-04-04 15:57:16 001.jpg
    ├── 2022-04-06 10:46:26 001.jpg
    └── 2022-04-08 18:53:36 001.jpg

3 directories, 31 files
```
## Issues

Yes.

This script was kept purposely small in scope and was really only made to fit my needs, so some issues are bound to appear, especially in situations that differ wildly from my own use case.  
That being said, I do want to open up its code - I figured if it helps even one person out there, then it was worth it.

If there are any outstanding problems you'd like to raise, I would sincerely love for you to contact me so I can learn more.
