#!/usr/bin/env python

# Based on MIT-licensed code from:
# https://www.stavros.io/posts/python-fuse-filesystem/

import os, sys, errno, time
import click
from github3 import login
from random import randint
from fuse import FUSE, FuseOSError, Operations
import rethinkdb as r

db_name = 'hookdb'

r.connect('lab.lbcpu.com', 28015).repl()

debug = True


class SlackFS(Operations):
    def __init__(self, db_host, db_name):
        self.db_host = db_host
        self.db_name = db_name

    def _contents(self, path):
        # Return contents of a given path
        # For now, return the issue title and body concatenated
        if debug: print('_contents path: {}'.format(path))

        if path.startswith('/#'):
            # Extract channel from filepath; if fails, abort
            channel = path.strip('/#').strip('.txt')
            print channel

        contents = []

        cursor = r.db(self.db_name).table(channel).order_by('timestamp').run()

        for document in cursor:
            message_data = {}
            message_data['timestamp'] = document['timestamp'].encode('utf-8')
            message_data['channel'] = channel.encode('utf-8')
            if 'bot_name' in document:
                message_data['user_name'] = document['bot_name'].encode('utf-8')
            else:
                message_data['user_name'] = document['user_name'].encode('utf-8')
            message_data['text'] = document['text'].encode('utf-8')

            message_template = '{timestamp}) {channel}/{user_name}:\n{text}'
            this_message = message_template.format(**message_data)

            contents.append(this_message)

        combined_content = '\n----------\n'.encode('utf-8').join(contents)
        return combined_content

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        if debug: print('access mode: {}, path: {}'.format(mode, path))
        # Mock
        # if False:
        #     raise FuseOSError(errno.EACCES)
        # return True

    def chmod(self, path, mode):
        if debug: print('chmod mode: {}, path: {}'.format(mode, path))
        # Mock
        return True

    def chown(self, path, uid, gid):
        if debug: print('chown uid: {}, gid: {}, path: {}'.format(uid, gid, path))
        # Mock
        return True

    def getattr(self, path, fh=None):
        if debug: print('getattr path: {}'.format(path))

        ignore_paths = ['/._.', '.gitignore']

        unix_timestamp = int(time.time())

        s = {'st_nlink': 1, 'st_mode': 16877, 'st_size': 0, 'st_gid': 20, 'st_uid': 501, 'st_ctime': unix_timestamp, 'st_mtime': unix_timestamp, 'st_atime': unix_timestamp}

        # If path is a directory
        if path.endswith('/'):
            s['st_mode'] = 16877
            s['st_size'] = 0
        # Else if path is a hidden file
        elif ('/.' in path):
            s['st_mode'] = 33188
            s['st_size'] = 0
        # Else if path is anything else, assume it's an issue entry
        else:
            path_content = self._contents(path)
            s['st_mode'] = 33188
            s['st_size'] = len(path_content)
            s['st_ino'] = randint(1, 10000000)
        return s

    def readdir(self, path, fh):
        if debug: print('readdir path: {}'.format(path))

        # If root of device...
        if path == '/':
            # Add . and .. entries to children array
            children = ['.', '..']

            # Get list of RethinkDB tables
            tables = r.db(db_name).table_list().run()

            # Add issue "filename" to children array
            for table in tables:
                table_filename = '#{}.txt'.format(table)[:255]
                children.append(table_filename)
                print table_filename

            # Return a generator object for each entry in children
            for entry in children:
                if debug: print entry
                yield entry

    def readlink(self, path):
        if debug: print('readlink path: {}'.format(path))
        # Mock
        return path

    def mknod(self, path, mode, dev):
        if debug: print('mknod path: {}'.format(path))
        # Mock
        return

    def rmdir(self, path):
        if debug: print('rmdir path: {}'.format(path))
        # Mock
        return path

    def mkdir(self, path, mode):
        if debug: print('mkdir path: {}'.format(path))
        # Mock
        return

    def statfs(self, path):
        if debug: print('statfs path: {}'.format(path))
        # Mocked up statfs return values for now
        # Mostly nonsensical but functional

        return {'f_bsize': 1048576, 'f_bavail': 0, 'f_favail': 7745916, 'f_files': 3, 'f_frsize': 4096, 'f_blocks': 29321728, 'f_ffree': 7745916, 'f_bfree': 0, 'f_namemax': 255, 'f_flag': 0}

    def unlink(self, path):
        if debug: print('unlink path: {}'.format(path))
        # Mock
        return

    def symlink(self, name, target):
        if debug: print('symlink name: {}, target: {}'.format(name, target))
        # Mock
        return

    def rename(self, old, new):
        if debug: print('rename old: {}, new: {}'.format(old, new))
        # Mock
        return

    def link(self, target, name):
        if debug: print('link name: {}, target: {}'.format(name, target))
        # Mock
        return

    def utimens(self, path, times=None):
        if debug: print('utimens path: {}'.format(path))
        # Mock
        return

    # File methods
    # ============

    def open(self, path, flags):
        if debug: print('open path: {}'.format(path))
        # Mock
        return True

    def create(self, path, mode, fi=None):
        if debug: print('create path: {}, mode: {}'.format(path, mode))
        # Mock
        return

    def read(self, path, length, offset, fh):
        if debug: print('read path: {} - {}:{}'.format(path, length, offset))
        # Retrieve contents, apply read offsets, and return
        # Added str() explicitly to return a byte array which read() expects
        return str(self._contents(path)[offset:offset+length])

    def write(self, path, buf, offset, fh):
        if debug: print('write path: {}, offset: {}'.format(path, offset))
        # Mock
        return True

    def truncate(self, path, length, fh=None):
        if debug: print('truncate path: {}, length: {}'.format(path, length))
        # Mock
        return True

    def flush(self, path, fh):
        if debug: print('flush path: {}'.format(path))
        # Mock
        # return True

    def release(self, path, fh):
        if debug: print('release path: {}'.format(path))
        # Mock
        return True

    def fsync(self, path, fdatasync, fh):
        if debug: print('fsync path: {}'.format(path))
        # Mock
        return True


# Use Python click decorators to handle command line options
@click.command()
@click.option('--mount', prompt='Mount point',
              help='The path where the filesystem will be mounted.')
@click.option('--db_host', prompt='RethinkDB hostname',
              help='The database host.')
@click.option('--db_name', prompt='RethinkDB database name',
              help='The database name.')
def new_slackfs(mount, db_host, db_name):
    # Ensure mountpoint already exists before mounting a FS to it
    if not os.path.exists(mount):
        os.makedirs(mount)

    # Create new FUSE filesystem at designated mountpoint using IssueFS
    FUSE(SlackFS(db_host, db_name), mount, nothreads=True, foreground=True)


if __name__ == '__main__':
    # Print out welcome instructions prior to execution
    print('Welcome to slackfs. Use a complete command like...')
    print('   ./slackfs.py --mount=./test --db_host=lab.lbcpu.com --db_name=hookdb')
    print('...or follow the interactive prompts.')

    # Initiative slackfs, including any command line option handling
    new_slackfs()