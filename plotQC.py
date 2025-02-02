# /usr/bin/env python3

import numpy as np
import matplotlib.pyplot as plt
import csv
import sys
import findUncoveredCoordinates


pileupFilename = sys.argv[1]
bedfile = sys.argv[2]


GENOME_SIZE = 29903
quality = np.zeros(GENOME_SIZE)
readDepth = np.zeros(GENOME_SIZE)
# numTermini = np.zeros(GENOME_SIZE)

# Import the pile-up file and record the coverage and average quality per position
with open(pileupFilename) as infile:
    # Uncomment below in case the -d <maxDepth> was unset during mpileup step.
    csv.field_size_limit(int(1e7))
    reader = csv.reader(infile, delimiter="\t", quoting=csv.QUOTE_NONE)
    for row in reader:
        pos = int(row[1])-1
        if pos >= GENOME_SIZE:
            print(
                'WARNING: Pileup file contains more rows than the genome length. Omitted extra fields.')
            break

        currentDepth = int(row[3])
        if currentDepth > 0:
            readDepth[pos] = currentDepth

            # PHRED to INT conversion rule:
            # def phred2int(x): return ord(x)-33
            quality[pos] = np.mean([ord(letter) for letter in row[5]]) - 33
        
        # Count the number of read termini at this location
        # This happens by checking for ^ and $ signs in the pileup file.
        # numTermini[pos] = row[4].count('^') + row[4].count('$')


# Calculate moving averages to smooth out patterns
def moving_avg(series, window=1001):
    out = np.convolve(series, np.ones(window)/window, 'same')
    half_window = int(window/2)
    out[0:half_window] = np.nan
    out[-half_window:] = np.nan
    return out

qualityMA = moving_avg(quality)
readDepthMA = moving_avg(readDepth)


# A Heaviside step function convolution to check if there are any up/down jumps in quality,
# which acts as a proxy to potential big discontinuities in coverage.
stepKernel = np.ones(501)
stepKernel[0:250] = -1
qualityjumpSignal = np.absolute(np.convolve(quality, stepKernel, 'same'))


# Import the list of uncovered genome regions due to kit design
gaps = findUncoveredCoordinates.findUncoveredCoordinates(bedfile, True)
gapStart = [ gaps[i][0] for i in range(len(gaps)) ]
gapEnd = [ gaps[i][1] for i in range(len(gaps)) ]

posIdx = np.arange(1, GENOME_SIZE+1, 1)
FDAblue = (0, 124/255, 186/255)  # RGB color representation of the logo
plt.rcParams.update({'font.size': 14})


#################################################################
# Generate a plot for quality vs pos and save in a file
plt.plot(posIdx, quality, '.', color=FDAblue)
plt.plot(posIdx[quality < 30], quality[quality < 30], '.', color='k')
plt.plot(posIdx, qualityMA, '-', color='m')


plt.xlabel('Genome position (kb)')
plt.ylabel('Average read quality')
plt.xlim([0, GENOME_SIZE+1])
plt.xticks(np.arange(0, GENOME_SIZE, 5000), ["%d" % (
    x/1000) for x in np.arange(0, GENOME_SIZE, 5000)])


# Add shading for uncovered regions
ymax = plt.gca().get_ylim()[1]
for i in range(0, len(gaps)):
    plt.fill([gapStart[i], gapEnd[i], gapEnd[i], gapStart[i]], [
             0, 0, ymax, ymax], 'r', alpha=1, edgecolor='none')
    plt.text((gapStart[i]+gapEnd[i])/2-GENOME_SIZE/60,
             1.01*ymax, '*', color='r', weight='bold', size=20)

plt.ylim([0, ymax])

plt.savefig('quality.png', dpi=200)
plt.close()



#################################################################
# Generate a 1D histogram for the quality factors and save in a file
plt.hist(quality, bins=50, color=FDAblue, edgecolor=None, density=True)
plt.xlim([0, max(40, *quality)*1.1])

(ymin, ymax) = plt.gca().get_ylim()
plt.plot([30, 30], [0, ymax], '--', color='k')
plt.ylim(ymin, ymax)

pctBelowThreshold = 100*len([x for x in quality if x < 30]) / len(quality)
(xmin, xmax) = plt.gca().get_xlim()
if (30-xmin) < 0.15*(xmax-xmin):
    plt.text(xmin, 1.05*ymax, "%.1f%%" %
             pctBelowThreshold,  color='r', size=16)
else:
    plt.text(10, 1.05*ymax, "%.1f%%" % pctBelowThreshold,  color='r', size=16)
plt.text((30+xmax)/2-5, 1.05*ymax, "%.1f%%" %
         (100-pctBelowThreshold),  color='g', size=16)

plt.xlabel('Average read quality')
plt.ylabel('Frequency')
plt.yticks([])

plt.savefig('qualityHistogram.png', dpi=200)
plt.close()



#################################################################
# Generate a plot for sequencing depth vs pos and save in a file
plt.plot(posIdx, readDepth, '.', color=FDAblue)
plt.plot(posIdx[readDepth < 10], readDepth[readDepth < 10], '.', color='k')
plt.plot(posIdx, readDepthMA, '-', color='m')

# If coverage is too high, scale the axes for a better view
if np.max(readDepth) > 5000:
    plt.ylabel('Coverage depth (1000)')
    locs, labels = plt.yticks()
    plt.yticks(locs, (locs/1000).astype('int') )
else:
    plt.ylabel('Coverage depth')


plt.xlabel('Genome position (kb)')
plt.xlim([0, GENOME_SIZE+1])
plt.xticks(np.arange(0, GENOME_SIZE, 5000), ["%d" % (
    x/1000) for x in np.arange(0, GENOME_SIZE, 5000)])

# Add shading for uncovered regions
ymax = plt.gca().get_ylim()[1]
for i in range(0, len(gaps)):
    plt.fill([gapStart[i], gapEnd[i], gapEnd[i], gapStart[i]], [
             0, 0, ymax, ymax], 'r', alpha=1, edgecolor='none')
    plt.text((gapStart[i]+gapEnd[i])/2-GENOME_SIZE/60,
             1.01*ymax, '*', color='r', weight='bold', size=20)

plt.ylim([0, ymax])
plt.tight_layout()
plt.savefig('coverage.png', dpi=200)
plt.close()


#################################################################
# Generate a histogram for the sequencing depth and save in a file
pctBelowThreshold = 100*len([x for x in readDepth if x < 100]) / len(quality)
if np.max(readDepth) > 5000:
    plt.hist(readDepth/1000, bins=50, color=FDAblue,
             edgecolor=None, density=True)
    (ymin, ymax) = plt.gca().get_ylim()
    plt.plot([0.1, 0.1], [0, ymax], '--', color='k')
    plt.ylim(ymin, ymax)
    plt.xlabel('Average read depth (1000)')

    (xmin, xmax) = plt.gca().get_xlim()
    if (0.1-xmin) < 0.15*(xmax-xmin):
        plt.text(xmin, 1.05*ymax, "%.1f%%" %
                 pctBelowThreshold,  color='r', size=16)
    else:
        plt.text(0.8*(xmin+0.1)/2, 1.05*ymax, "%.1f%%" %
                 pctBelowThreshold,  color='r', size=16)
    plt.text(max(0.09, 0.8*(xmax+0.1)/2), 1.05*ymax, "%.1f%%" %
             (100-pctBelowThreshold),  color='g', size=16)
else:
    plt.hist(readDepth, bins=50, color=FDAblue, edgecolor=None, density=True)
    (ymin, ymax) = plt.gca().get_ylim()
    plt.plot([100, 100], [0, ymax], '--', color='k')
    plt.ylim(ymin, ymax)
    plt.xlabel('Average read depth')

    (xmin, xmax) = plt.gca().get_xlim()
    if (100-xmin) < 0.15*(xmax-xmin):
        plt.text(xmin, 1.05*ymax, "%.1f%%" %
                 pctBelowThreshold,  color='r', size=16)
    else:
        plt.text(0.8*(xmin+100)/2, 1.05*ymax, "%.1f%%" %
                 pctBelowThreshold,  color='r', size=16)
    plt.text(max(90, 0.8*(xmax+100)/2), 1.05*ymax, "%.1f%%" %
             (100-pctBelowThreshold),  color='g', size=16)

plt.ylabel('Frequency')
plt.yticks([])
plt.savefig('depthHistogram.png', dpi=200)
plt.close()



#################################################################
# Generate a plot for the quality jump signal vs pos and save in a file
plt.plot(posIdx, qualityjumpSignal, '-', color='m')

# If coverage is too high, scale the axes for a better view
locs, labels = plt.yticks()
if locs[-1] > 2000:
    plt.ylabel('Discontinuity signal (1000 AU)')
    plt.yticks(locs, (locs/1000).astype('int') )
else:
    plt.ylabel('Discontinuity signal (AU)')


plt.xlabel('Genome position (kb)')
plt.xlim([0, GENOME_SIZE+1])
plt.xticks(np.arange(0, GENOME_SIZE, 5000), ["%d" % (
    x/1000) for x in np.arange(0, GENOME_SIZE, 5000)])

plt.tight_layout()
plt.savefig('discontinuitySignal.png', dpi=200)
plt.close()




#################################################################
# Generate a bar plot to show breakdown of uncovered/undercovered loci into viral genes and save in a file

# GeneName:(start_inclusive,end_inclusive)
gene_start_end = {"5' UTR":(1,265), 'ORF1ab':(266,21555), 'S':(21563,25384), 'ORF3a':(25393,26220), 'E':(26245,26472), 'M':(26523,27191), 'ORF6':(27202,27387), 'ORF7ab':(27394,27887), 'ORF8':(27894,28259), 'N':(28274,29533), 'ORF10':(29558,29674), "3' UTR":(29675,29903)}

def coordinate2gene (coordinate):   
    for gene_name in gene_start_end:
        (start,end) = gene_start_end[gene_name]
        if coordinate>=start and coordinate<=end:
            return gene_name
    
    # If the coordinate is not contained in any of the pre-defined genes...
    return 'Other'

gene_names = gene_start_end.keys()
gene_lengths = np.array([(gene_start_end[name][1]-gene_start_end[name][0]) for name in gene_names ])/1000.0

uncovered_genes = [coordinate2gene(x+1) for x in range(len(readDepth)) if readDepth[x]==0]
uncovered_gene_counts = np.array([ uncovered_genes.count(name) for name in gene_names ])
undercovered_genes = [coordinate2gene(x+1) for x in range(len(readDepth)) if readDepth[x]<10]
undercovered_gene_counts = np.array([ undercovered_genes.count(name) for name in gene_names ])

# Absolute genomic coordinate counts per gene
plt.bar(gene_names, undercovered_gene_counts, color=FDAblue)
plt.bar(gene_names, uncovered_gene_counts, color='k', width=0.5)
plt.legend(['<10X', '0X'], labelcolor='markerfacecolor', frameon=False, ncol=2)
plt.xticks(rotation = 60)
plt.xlabel('Genes')
plt.ylabel('#Genomic coordinates')

plt.tight_layout()
plt.savefig('genesVSuncovered_abscounts.png', dpi=200)
plt.close()


# Missing genomic coordinate counts per gene scaled with gene length
plt.bar(gene_names, undercovered_gene_counts/gene_lengths, color=FDAblue)
plt.bar(gene_names, uncovered_gene_counts/gene_lengths, color='k', width=0.5)
plt.legend(['<10X', '0X'], labelcolor='markerfacecolor', frameon=False, ncol=2)
plt.xticks(rotation = 60)
plt.xlabel('Genes')
plt.ylabel('#Genomic coordinates per kbp')

plt.tight_layout()
plt.savefig('genesVSuncovered_scaled.png', dpi=200)
plt.close()



# Coverage depth vs. breadth plot
depth_bins = [2**x for x in range(0,15,1)]
breadth_pdf = np.histogram(readDepth, bins=depth_bins)[0]
breadth_cdf = np.cumsum(np.flip(breadth_pdf)) * 100.0 / GENOME_SIZE

plt.plot(np.flip(depth_bins[0:-1]), breadth_cdf, '-', color=FDAblue)
plt.plot(np.flip(depth_bins[0:-1]), breadth_cdf, 'o', color=FDAblue)

plt.xlabel('Coverage depth (X, cumulative)')
plt.xscale('log')
plt.ylabel('Coverage breadth (%)')
plt.ylim(0,100)

plt.tight_layout()
plt.savefig('breadthVSdepth.png', dpi=200)
plt.close()



#################################################################
# Export a csv file for pos; coverage; quality
outfilename = "pos-coverage-quality.tsv"
with open(outfilename, 'w') as outfile:
    writer = csv.writer(outfile, delimiter="\t")
    for i in range(0, GENOME_SIZE):
        writer.writerow(["%d" % posIdx[i], "%d" %
                        readDepth[i], '%.2f' % quality[i]])

