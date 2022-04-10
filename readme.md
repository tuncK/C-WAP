# C-WAP
# CFSAN Wastewater Analysis Pipeline

C-WAP is a bash-based bioinformatics pipeline for the analysis of either long-read (ONT or PacBio) or short-read (Illumina) whole genome sequencing
data of DNA extracted from wastewater. It was developed for SARS-CoV2 and its variants.

C-WAP was developed by the United States Food and Drug Administration, Center for Food Safety and Applied Nutrition.


### Introduction

The CFSAN Wastewater Analysis Pipeline uses a reference-based alignment to create a matrix of
SNPs for a given set of samples and estimate the perentage of SC2 variants in the sample 

The process includes the following:
1. Designating a reference and NGS data in fastq format
2. Alignment of reads to the reference via Bowtie2
3. Taxonomy check via kraken2
4. Processing of alignment results via samtools
5. Detection of variant positions with ivar
6. Determine composition of variants via kallisto, linear regression, kraken2/bracken and freyja
7. Generate an html and pdf formatted summary of results



### Dependencies

User provided:
* [Conda3] (https://docs.conda.io/en/latest/miniconda.html)
* [NextFlow v21.0+](https://www.nextflow.io/docs/latest/index.html)
* [ghostscript](https://www.ghostscript.com)

Auto-fetched by C-WAP:
* [kraken2 v2.1.2 ](https://github.com/DerrickWood/kraken2)
* [bracken](https://github.com/jenniferlu717/Bracken)
* [samtools v1.13 ](https://github.com/samtools/)
* [bcftools](https://github.com/samtools/bcftools)
* [ivar](https://github.com/andersen-lab/ivar)
* [bowtie2](http://bowtie-bio.sourceforge.net/bowtie2/manual.shtml)
* [minimap2 v2.22](https://github.com/lh3/minimap2)
* [entrez-direct](https://www.ncbi.nlm.nih.gov/books/NBK179288/)
* [pangolin](https://github.com/cov-lineages/pangolin)
* [Freyja](https://github.com/andersen-lab/Freyja)
* [kallisto](https://github.com/pachterlab/kallisto)
* [wkhtmltopdf](https://github.com/wkhtmltopdf)

./startWorkflow.nf assumes that conda, nextflow and gs executables are available in the search path. All other dependencies are imported via conda during runtime. Acquisition of the dependencies and creating of the env's might cause the very first execution attempt to take a substantially long time (potentially hours). Subsequent runs will make use of the cached env's stored under the c-wap/conda subdirectory and are expected to finish substantially faster.


### Installation

Install nextflow and conda. Afterwards, download c-wap repository and save.


### Usage 

The driver script is `startWorkflow.nf` and a standard execution with paired end illumina reads would be:  
`startWorkflow.nf --platform i --primers path/to/bed --in path/to/fastq/ --out path/to/outputDir`


### Output

C-WAP produces a number of files from the various processing steps.  

`sorted.stats` - Samtools stats output from aligned but untrimmed reads  
`kallisto.out` - Python-parsed summary of the kallisto lineage abundance estimates  
`deconvolution.output` - Output of linear deconvolution method for estimating variant composition  
`linearDeconvolution_abundance.csv` - Linear deconvolution estimates of variant composition  
`freyja.demix` - Lineage abundance estimate generated by Freyja  
`kallisto_abundance.tsv` - Kallisto estimates of variant composition  
`k2-majorCovid.out` - Covid-specific kraken2 output with major lineages identified, against majorCovid DB  
`k2-majorCovid_bracken.out` - Bracken lineage abundance estimates, against majorCovid DB  
`k2-allCovid.out` - Covid-specific kraken2 output, against allcovid DB  
`k2-allCovid_bracken.out` - Bracken lineage abundance estimates, against allCovid DB  
`pangolin_lineage_report.csv` - Pangolin lineage prediction for the consensus sequence  
`consensus.fa` - consensus fasta file generated by ivar  
`calls.vcf.gz` - Variant call file generated by bcftools  
`pos-coverage-quality.tsv` - QC metrics on coverage and quality obtained from the pileup file  
`rawVarCalls.tsv` - Variant calls generated by iVar, vcg equivalent of samtools  
`k2-std.out` - kraken2 output with standard database  
`report` - standalone directory containing html and pdf summary report  


### Note about variant composition

Variant composition analyses should be interpreted with caution where they should be treated as suspect if there are substantial gaps in coverage across the reference genome and/or a lack of sequencing depth.  The linear deconvolution and kraken2/bracken covid method are internally developed methods and under testing and validation.  


### Citing C-WAP
This work is currently unpublished. If you are making use of this package, 
we would appreciate if you gave credit to our repository. 


### License

See the LICENSE.txt file included in the C-WAP Pipeline distribution.

