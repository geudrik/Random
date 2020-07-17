""" Some dumbshit to import (or try to anyway) Google Play Music playists (courtesty of TakeOut data)
to Spotify. Lord knows YouTube music is a raging trashfire :/

Copyright (c) <2020> <geudrik>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import os

class Track:
	""" Represents a single track 
	Args:
		filepath (str) Absolute filepath of the Track.csv file

	Return:
		Dict representation of the track
	"""

	def __init__(self, filepath):
		self._filepath = filepath

		with open(self._filepath, 'r') as csvfile:
			row = None
			reader = csv.DictReader(csvfile)
			for _row in reader:
				row = _row
				break

		self.title = row['Title']
		self.artist = row['Artist']
		self.album = row['Album']


class Playlist:
	""" Represents a collection of tracks
	"""

	

for root, dirs, files in os.walk(sys.argv[1]):
	for d in dirs:

		# Load playlist name up
		with open(os.path.join(os.path.abspath(root), d, 'Metadata.csv'), 'r') as csvfile:
			reader = csv.reader(csvfile)
			fields = reader.next()

