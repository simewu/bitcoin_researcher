# This newer script scans files wihin the current directory, and parses them, adding # Diff and BytesSum Diff columns to the end

from decimal import Decimal
import csv
import hashlib
import codecs
import os
import re
import sys
import time

# List the files with a regular expression
def listFiles(regex):
	return [file for file in os.listdir(os.curdir) if os.path.isfile(file) and bool(re.match(regex, file))]

# Given a file name, compute the hash of its contents
def computeFileHash(fileName):
	BLOCK_SIZE = 65536
	fileHash = hashlib.sha256()
	with open(file, 'rb') as f:
		fb = f.read(BLOCK_SIZE)
		while len(fb) > 0:
			fileHash.update(fb)
			fb = f.read(BLOCK_SIZE)
	base64 = codecs.encode(fileHash.digest(), 'base64').decode().strip()
	base64 = re.sub(r'[<>:"/\\|?*]', '', base64)[:16]
	return base64

if __name__ == '__main__':
	try:
		os.mkdir('PostProcessed')
	except: pass
	files = listFiles(r'Sample [0-9]+, numConnections = [0-9]+, minutes = [0-9\.]+(?: copy(?: [0-9]+)?)?\.csv')
	for file in files:
		print(f'Processing {file}')
		match = re.match(r'Sample ([0-9]+), numConnections = ([0-9]+), minutes = ([0-9\.]+)', file)
		if match == None:
			print('\n' + '!' * 60 + f'\nERROR! File "{file}" does not match the pattern!\n')
			continue
		fileHash = computeFileHash(file)
		newFileName = f'Connections_{match.group(2)}_mins_{match.group(3)}_hash_{fileHash}.csv'
		if os.path.exists(os.path.join('PostProcessed', newFileName)):
			# Skip the files that have already been processed
			print(f'Skipping file "{newFileName}"')
			continue

		print(f'Writing to {newFileName}')

		readerFile = open(file, 'r')
		writerFile = open(os.path.join('PostProcessed', newFileName), 'w', newline='')

		# Remove NUL bytes to prevent errors
		reader = csv.reader(x.replace('\0', '') for x in readerFile)
		writer = csv.writer(writerFile)

		header = next(reader)
		headerDesc = next(reader)
		newHeader = header.copy()
		newHeaderDesc = headerDesc.copy()
		newColumns = []

		for i, cell in enumerate(header):
			match = re.match(r'# ([^ ]+) Msgs', cell)
			if match is not None:
				name = f'{cell} Diff'
				newColumns.append((name, i))
				newHeader.append(name)
				newHeaderDesc.append('The difference in number of messages')

			match = re.match(r'BytesAvg ([^ ]+)', cell)
			if match is not None:
				name = f'BytesSum {match.group(1)} Diff'
				newColumns.append((name, i))
				newHeader.append(name)
				newHeaderDesc.append('The number of bytes for this individual message')

		writer.writerow(newHeader)
		writer.writerow(newHeaderDesc)
		lastRow = [0] * len(newHeader)
		for row in reader:
			for column in newColumns:
				cell, i = column
				if cell.startswith('# '):
					row.append(int(row[i]) - int(lastRow[i]))
				elif cell.startswith('BytesSum '):
					bytesSum = Decimal(row[i]) * Decimal(row[i - 5])
					lastBytesSum = Decimal(lastRow[i]) * Decimal(lastRow[i - 5])
					row.append(round(bytesSum - lastBytesSum))
			writer.writerow(row)
			lastRow = row

		readerFile.close()
		writerFile.close()