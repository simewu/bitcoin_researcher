# This script scans for Sample X numConnections Y.csv files wihin the current directory, and parses them, adding # Diff and BytesSum Diff columns to the end

from decimal import Decimal
import csv
import numpy as np
import os
import re
import scipy.stats
import sys
import time

numSecondsPerSample = 1


# List the files with a regular expression
def listFiles(regex, directory):
	path = os.path.join(os.curdir, directory)
	return [os.path.join(path, file) for file in os.listdir(path) if os.path.isfile(os.path.join(path, file)) and bool(re.match(regex, file))]

# Compute the confidence interval of a list of data
def compute_confidence(data, confidence=0.95):
	a = 1.0 * np.array(data)
	n = len(a)
	m, se = np.mean(a), scipy.stats.sem(a)
	h = se * scipy.stats.t.ppf((1 + confidence) / 2., n-1)
	return m, m-h, m+h

def compute_mean_open_high_low_close(data):
	m, o, c = compute_confidence(data)
	h = max(data)
	l = min(data)
	return f'{m} {o} {h} {l} {c}'

if __name__ == '__main__':
	outputFile = open(f'Raw Rate Info.csv', 'w', newline='')
	line = 'File Name,'
	line += 'Hash ID,'
	line += 'Connections,'
	line += 'Logging Time,'

	line += 'AvgBlockDelay,'

	line += 'NumAllMsgs,'

	line += 'NumUniqueTX,'
	line += 'NumAllTX,'
	line += 'TXRatioUnique/All,'
	
	line += 'NumUniqueBlocks,'
	line += 'NumAllBlocks,'
	line += 'BlockRatioUnique/All,'

	line += 'AllMsgs/Sec,'

	line += 'UniqueTX/Sec,'
	line += 'AllTX/Sec,'

	line += 'AvgBitcoinCPU,'
	line += 'AvgSystemCPU,'
	line += 'AvgMemory,'
	line += 'AvgMemoryMB,'
	line += 'AvgDownloadRate,'
	line += 'AvgUploadRate,'


	outputFile.write(line + '\n')
	directory = 'PostProcessed'
	files = listFiles(r'Connections_[0-9]+_mins_[0-9\.]+_hash_', directory)

	for file in files:
		print(f'Processing {file}')
		readerFile = open(file, 'r')
		# Remove NUL bytes to prevent errors
		reader = csv.reader(x.replace('\0', '') for x in readerFile)

		header = next(reader)
		headerDesc = next(reader)

		match = re.match(r'(?:\.[/\\])?' + directory + r'[/\\]Connections_([0-9]+)_mins_([0-9\.]+)_hash_(.*)\.csv', file)

		fileName = os.path.basename(file)
		connections = match.group(1)
		hashID = match.group(3)
		loggingTime = 0
		avgBlockDelay = 0
		numAllMsgs = 0
		numUniqueTx = 0
		numAllTx = 0
		txRatioUniqueAll = 0
		numUniqueBlocks = 0
		numAllBlocks = 0
		blockRatioUniqueAll = 0
		allMsgsPerSec = 0
		uniqueTxPerSec = 0
		allTxPerSec = 0
		avgBitcoinCpu = 0
		avgSystemCpu = 0
		avgMemory = 0
		avgMemoryMB = 0
		avgDownloadRate = 0
		avgUploadRate = 0


		numRows = 0
		cpuPercentRows = 0
		blockDelayRows = 0
		cpuSystemPercentRows = 0
		memoryPercentRows = 0
		avgDownloadUploadRateRows = 0
		firstRow = ''
		lastRow = ''
		row = ''
		prevRow = ''
		for row in reader:
			if numRows == 0: firstRow = row

			blockDelay = row[17]
			if blockDelay != '' and row[16] != row[17]:
				avgBlockDelay += float(blockDelay)
				blockDelayRows += 1

			# Skip the first row because the difference contains everything before the script execution
			if prevRow != '':
				allMsgsDiff = max(0, float(row[216]) + float(row[218]) + float(row[220]) + float(row[222]) + float(row[224]) + float(row[226]) + float(row[228]) + float(row[230]) + float(row[232]) + float(row[234]) + float(row[236]) + float(row[238]) + float(row[240]) + float(row[242]) + float(row[244]) + float(row[246]) + float(row[248]) + float(row[250]) + float(row[252]) + float(row[254]) + float(row[256]) + float(row[258]) + float(row[260]) + float(row[262]) + float(row[264]) + float(row[266]))
				numAllMsgs += allMsgsDiff
				uniqueTxDiff = max(0, float(row[20]) - float(prevRow[20]))
				numUniqueTx += uniqueTxDiff
				allTXDiff = max(0, float(row[232]))
				numAllTx += allTXDiff
				uniqueBlockDiff = max(0, float(row[16]) - float(prevRow[16]))
				numUniqueBlocks += uniqueBlockDiff
				allBlocksDiff = max(0, float(row[236]) + float(row[260]))
				numAllBlocks += allBlocksDiff
				allMsgsPerSec += allMsgsDiff
				uniqueTxPerSec += uniqueTxDiff
				allTxPerSec += allTXDiff

			cpuPercent = row[11]
			if cpuPercent.endswith('%'):
				cpuPercent = cpuPercent[:-1]
				avgBitcoinCpu += float(cpuPercent)
				cpuPercentRows += 1

			if header[15].strip() == 'Full System CPU %':
				cpuSystemPercent = row[15]
				if cpuSystemPercent.endswith('%'):
					cpuSystemPercent = cpuSystemPercent[:-1]
					avgSystemCpu += float(cpuSystemPercent)
					cpuSystemPercentRows += 1

			memoryPercent = row[12]
			if memoryPercent.endswith('%'):
				memoryPercent = memoryPercent[:-1]
				avgMemory += float(memoryPercent)
				memoryPercentRows += 1
			avgMemoryMB += float(row[13])

			bandwidth = row[14]
			if len(bandwidth.split('/')) == 2:
				down, up = bandwidth.split('/')
				avgDownloadRate += float(down)
				avgUploadRate += float(up)
				avgDownloadUploadRateRows += 1

			numRows += 1
			prevRow = row
		lastRow = row

		loggingTime = (float(lastRow[1]) - float(firstRow[1])) / 60

		avgBlockDelay /= blockDelayRows
		#numUniqueTx
		#numAllTx
		if numUniqueTx > numAllTx: numUniqueTx = numAllTx
		txRatioUniqueAll = (numUniqueTx / numAllTx) if numAllTx != 0 else 0
		#numUniqueBlocks
		#numAllBlocks
		if numUniqueBlocks > numAllBlocks: numUniqueBlocks = numAllBlocks
		blockRatioUniqueAll = (numUniqueBlocks / numAllBlocks) if numAllBlocks != 0 else 0
		allMsgsPerSec /= numRows
		uniqueTxPerSec /= numRows
		allTxPerSec /= numRows
		avgBitcoinCpu /= cpuPercentRows
		avgSystemCpu = (avgSystemCpu / cpuSystemPercentRows) if cpuSystemPercentRows != 0 else ''

		avgMemory /= memoryPercentRows
		avgMemoryMB /= numRows

		avgDownloadRate = (avgDownloadRate / avgDownloadUploadRateRows) if avgDownloadUploadRateRows != 0 else ''
		avgUploadRate = (avgUploadRate / avgDownloadUploadRateRows) if avgDownloadUploadRateRows != 0 else ''







		line = '"' + fileName + '",'
		line += str(hashID) + ','
		line += str(connections) + ','
		line += str(loggingTime) + ','

		line += str(avgBlockDelay) + ','

		line += str(numAllMsgs) + ','

		line += str(numUniqueTx) + ','
		line += str(numAllTx) + ','
		line += str(txRatioUniqueAll) + ','

		line += str(numUniqueBlocks) + ','
		line += str(numAllBlocks) + ','
		line += str(blockRatioUniqueAll) + ','

		line += str(allMsgsPerSec) + ','

		line += str(uniqueTxPerSec) + ','
		line += str(allTxPerSec) + ','

		line += str(avgBitcoinCpu) + ','
		line += str(avgSystemCpu) + ','
		line += str(avgMemory) + ','
		line += str(avgMemoryMB) + ','

		line += str(avgDownloadRate) + ','
		line += str(avgUploadRate) + ','

		outputFile.write(line + '\n')

		readerFile.close()
	
	outputFile.close()