#!/usr/bin/env python3

import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
import sys
import csv
import pandas as pd
import numpy as np
import pickle


if len(sys.argv) != 9:
    raise Exception('Incorrect call to the script.')


# Data regarding the current sample passed by UNIX
outputDirectory = sys.argv[1]
variantDBfilename = sys.argv[2]

# Sample-sepecific input files generated by upstream processes
variantFreqFilename = sys.argv[3]
kallistoFilename = sys.argv[4]
k2_allCovidFilename = sys.argv[5]
k2_majorCovidFilename = sys.argv[6]
freyjaOutputFile = sys.argv[7]
lcsFile = sys.argv[8]


# Import the pre-processed variant definitions from file
with open(variantDBfilename, 'rb') as file:
    uniqueVarNames = pickle.load(file)
    # uniqueMutationLabels = pickle.load(file)
    # var2mut = pickle.load(file)
    # mut2var = pickle.load(file) # Skipped these for efficiency
    # importantVars = pickle.load(file)
    # pos2gene = pickle.load(file)
    # gene2pos = pickle.load(file)
    # sigMutationMatrix = pickle.load(file)


# Translation table for pangolin and WHO names of variants
pangolin2WHO = {'B.1.1.7': 'Alpha', 'B.1.351': 'Beta', 'P.1': 'Gamma', 'B.1.427': 'Epsilon', 'B.1.429': 'Epsilon',
                'B.1.525': 'Eta', 'B.1.526': 'Iota', 'B.1.617.1': 'Kappa', 'B.1.621': 'Mu', 'B.1.621.1': 'Mu',
                'P.2': 'Zeta', 'B.1.617.3': 'B.1.617.3', 'B.1.617.2': 'Delta', 'AY': 'Delta',
                'B.1.1.529': 'Omicron', 'BA.1': 'BA.1', 'BA.2': 'BA.2', 
                'BA.3': 'BA.3', 'wt': 'wt', 'wt-wuhan': 'wt',
                'A.21': 'Bat', 'other': 'Other', 'A': 'wt', 'Error':'Error'}


# Convert each variant to a WHO-compatible name, if one exists
def getDisplayName(pangolinName):
    if pangolinName in pangolin2WHO.keys():
        # Exact correspondance to a published name
        return pangolin2WHO[pangolinName]
    elif pangolinName in pangolin2WHO.values():
        # Already an exact match to a published name
        return pangolinName
    else:
        # Check if this is a sublineage of a defined lineage
        for i in range(pangolinName.count('.'), 0, -1):
            superVariant = '.'.join(pangolinName.split('.')[0:i])
            if superVariant in pangolin2WHO:
                return pangolin2WHO[superVariant]

        # No name seems to correspond to it, return itself
        return pangolinName


# Assign a pre-determined color to each display name
rgbColors = plt.get_cmap('tab20b').colors + plt.get_cmap('tab20c').colors[0:16]
colorCycle = [to_hex(color) for color in rgbColors]
def getColor (var_name):
    if var_name.lower() == 'other':
        return '#BBBBBB'
    else:
        color_idx = hash(var_name)%len(colorCycle)
        return colorCycle[color_idx]


########################################################################
# Generate a full-size pie chart for the current sample depicting the prevalence of variants
# Only display variants that are >= x% abundant
# Less frequent variants will be cumulated under 'other' category
def drawPieChart(names2percentages, outfilename, title=''):
    minPlotThreshold = 5  # in %

    percentages2plot = []
    names2plot = []
    for name in names2percentages.keys():
        dname = getDisplayName(name)
        freq = names2percentages[name]
        if dname != 'Other' and freq >= minPlotThreshold:
            if dname in names2plot:
                var_idx = names2plot.index(dname)
                percentages2plot[var_idx] += freq
            else:
                names2plot.append(dname)
                percentages2plot.append(freq)

    # Cumulate all other infrequent variants under "other" category
    other_pct = 100-np.sum(percentages2plot)
    if other_pct > 0.1:
        names2plot.append('Other')
        percentages2plot = np.append(percentages2plot, other_pct)
        
    colors2plot = [getColor(name) for name in names2plot]
    explosionArray = np.full(len(percentages2plot), 0.07)
    plt.rcParams.update({'font.size': 12})
    plt.pie(percentages2plot, labels=names2plot, autopct='%1.1f%%', shadow=False,
            explode=explosionArray, colors=colors2plot)
    plt.axis('equal')
    plt.title(title)
    plt.savefig(outfilename, dpi=300)
    plt.close()


########################################################
# Process the results of linear deconvolution approach
names2percentages = {}
with open(variantFreqFilename, 'r') as infile:
    reader = csv.reader(infile, delimiter=" ")
    counter = 0
    for row in reader:
        cFreq = float(row[1])
        dname = getDisplayName(uniqueVarNames[counter])
        if dname in names2percentages:
            names2percentages[dname] += cFreq
        else:
            names2percentages[dname] = cFreq
        counter += 1

drawPieChart(names2percentages, outputDirectory+'/pieChart_deconvolution.png',
             title='Abundance of variants\n by linear regression')


########################################################
# Process the results of linear deconvolution approach
# Read the tsv file generated by kallisto
kallistoHits = {}
with open(kallistoFilename, 'r') as infile:
    reader = csv.reader(infile, delimiter="\t")
    next(reader) # Skip the header
    for row in reader:
        pangoName = row[0].split('_')[0]
        dname = getDisplayName(pangoName)
        numberHits = float(row[3])
        if dname in kallistoHits:
            kallistoHits[dname].append(numberHits)
        else:
            kallistoHits[dname] = [numberHits]


# Loop through the imported kallisto data.
# For duplicates, get an average
for varWHOname in kallistoHits:
    kallistoHits[varWHOname] = np.sum(kallistoHits[varWHOname])

totalNumReads = sum(kallistoHits.values())
names2percentages = {}
for varWHOname in kallistoHits:
    names2percentages[varWHOname] = 100.0 * \
        kallistoHits[varWHOname]/totalNumReads

drawPieChart(names2percentages, outputDirectory+'/pieChart_kallisto.png',
             title='Abundance of variants by kallisto')


with open(outputDirectory + '/kallisto.out', 'w') as outfile:
    for name in names2percentages:
        outfile.write('%s\t%.1f\n' % (name, names2percentages[name]))


########################################################
# Process the results of kraken2+bracken approach
# Read the tsv file generated by bracken
def importBrackenOutput(brackenFilename):
    brackenHits = {}
    with open(brackenFilename, 'r') as infile:
        # If there were no reads that are variant specific, bracken generates
        # an empty file output, even no header to skip. 
        
        reader = csv.reader(infile, delimiter="\t")
        for row in reader:
            pctHits = float(row[0])
            varDispName = getDisplayName(row[5]).strip()
            
            # Skip the header if column2 is either root or covid.
            if varDispName not in ['root', 'covid']:
                brackenHits[varDispName] = pctHits
            
    return brackenHits


brackenHits = importBrackenOutput(k2_allCovidFilename)
drawPieChart(brackenHits, outputDirectory+'/pieChart_k2_allCovid.png',
             title='Abundance of variants by\n kraken2+bracken, using allCovid DB')

brackenHits = importBrackenOutput(k2_majorCovidFilename)
drawPieChart(brackenHits, outputDirectory+'/pieChart_k2_majorCovid.png',
             title='Abundance of variants by\n kraken2+bracken, using majorCovid DB')


########################################################
# Process the abundance estimates by Freyja
freyja_raw = pd.read_table(freyjaOutputFile, index_col=0)

# Option A: summary reported by Freyja with WHO names
# var_pct = eval( pd.Series(freyja_raw.loc['summarized'][0])[0] )

# Option B: detailed subvariant breakdown
lineages = eval( pd.Series(freyja_raw.loc['lineages'][0])[0].replace(' ', ',') )
abundances = eval( ','.join(pd.Series(freyja_raw.loc['abundances'][0])[0].split()) )
var_pct = tuple(zip(lineages, abundances))

freyjaHits = {}
for var in var_pct:
    name = var[0]
    pct = 100*var[1]
    freyjaHits[name] = pct

drawPieChart(freyjaHits, outputDirectory+'/pieChart_freyja.png',
             title='Abundance of variants by Freyja')



########################################################
# Process the abundance estimates by LCS
with open(lcsFile, 'r') as infile:
    reader = csv.reader(infile, delimiter="\t")
    next(reader)  # Skip the header line of lcs.out  
    lcsHits = {}
    for row in reader:
        pangoName = row[1].split('_')[-1]
        dname = getDisplayName(pangoName)
        proportion = float(row[2])*100
        if dname in lcsHits:
            lcsHits[dname].append(proportion)
        else:
            lcsHits[dname] = [proportion]

# Loop through the imported kallisto data.
# For duplicates, get an average
for varWHOname in lcsHits:
    lcsHits[varWHOname] = np.sum(lcsHits[varWHOname])

drawPieChart(lcsHits, outputDirectory+'/pieChart_lcs.png',
             title='Abundance of variants by LCS')


