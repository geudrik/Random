#! /usr/bin/env python2.7
#
# Author: Pat Litke (C) 2014
#
# This code is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This code is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Baku.  If not, see <http://www.gnu.org/licenses/>.
#
# Description:
# Quick and dirty module to read a binary file, look at the DOS header for the PE offset
#   Seek to the PE offset, read the third DWORD in, unpack it, and return either EPOCH or GMTIMEs
#
# Returns 1 if the file doesn't havea a DOS header
# Returns 2 if file couldn't be read
# Returns the data in epoch or formatted otherwise

from struct import unpack
from binascii import hexlify
from time import gmtime, strftime

def getEpoch(filePath, epoch = True):
	
	# Open the file in Binary mode
	try:
		handle = open(filePath, 'rb')
		if hexlify(handle.read(2)) != hexlify(u'MZ'):
			handle.close()
			return 1
	except:
		return 2

	# Get PE offset (@60, DWORD) from DOS header
	#	It's little-endian so we have to flip it
	#	We also need the HEX representation which is an INT value
	handle.seek(60, 0)
	offset = handle.read(4)
	offset = hexlify(offset[::-1])
	offset = int(offset, 16)

	# Seek to PE header and read second DWORD
	handle.seek(offset+8, 0)
	dword = handle.read(4)
	handle.close()
	t = unpack(">L", dword[::-1])[0]

	if epoch:
		return t
	else:
		return strftime('%Y-%m-%d %H:%M:%S', gmtime(float(t)))



def getUTC(filePath):
	return getEpoch(filepath, False)

def getBoth(filePath):
	return [getEpoch(filepath), getEpoch(filepath, False)]
