# This script generates a file to be supplied to a SPReD upload, containing subject metadata (e.g. WT or KO, SPReD ID, age, etc.) for uploading mice to the Brain-CODE SPReD.

# GenerateSubjectMetadata.R ----------------------------------------------------------

# Specify base folder containing the gf files used to identify which mice are WT and KO.
gfFilePath = '/micehome/jbruce/Documents/Code/R/ClusterMouseAutism/data/'

# Specify distortion corrected folder name, associated processed folder name, strain label, and gf file required for upload for each strain.
foldersToUpload = data.frame(FolderName=c('/projects/moush/jacob/ITGB3/ITGB3_Images/Distortion_Corrected/'),
                             ProcessedFolderName=c('/projects/moush/jacob/ITGB3/ITGB3_22Jan12_ANTS_processed/'),
                             StrainLabel=c('ITGB3'),
                             GfFile=c(paste(gfFilePath, 'gf_ITGB3_relative.txt', sep="")),
                             stringsAsFactors=FALSE)

# Create data frame data structure to store the metadata, which will eventually be written to a csv.
allSubjects = data.frame(Filename=character(1),
                         ProcessedFolder=character(1),
                         Genotype=character(1), 
                         SubjLabel=character(1), 
                         SubjNum=character(1),
                         dob=character(1),
                         gender=character(1),
                         handedness=character(1),
                         race=character(1),
                         ethnicity=character(1),
                         weight=numeric(1),
                         height=numeric(1),
                         stringsAsFactors=FALSE)

# Enumeration specifying the number system to use for subject indices (in this case, base 36, because it might be possible to have over 99 subjects per strain).
subjNumEnum = c('0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
                'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 
                'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 
                'U', 'V', 'W', 'X', 'Y', 'Z')

CreateSubjNum <- function(numericIndex, numericEnum) {
  # Summary:
  #   Given a numeric index, return the 2 digit alphanumeric index according to some numeric -> alphanumeric mapping enumeration to be used to identify a subject.
  # Args:
  #   numericIndex: An integer; the number to be converted to a 2 digit alphanumeric value.
  #   numericEnum: A character array mapping indices to alphanumeric characters (e.g. 13 to D).
  # Returns:
  #   A valid 2 digit SPReD alphanumeric ID.
  
  ones = numericIndex %% length(numericEnum)
  onesDigit = numericEnum[ones + 1]
  tens = floor(numericIndex / 36)
  tensDigit = numericEnum[tens + 1]
  
  newNumericIndex = paste(tensDigit, onesDigit, sep="")
  
  return(newNumericIndex)
}

# loop through strains and create SPReD subject metadata file
for (strainIndex in 1:dim(foldersToUpload)[1]) {
  
  folderName = foldersToUpload$FolderName[strainIndex]
  processedFolderName = foldersToUpload$ProcessedFolderName[strainIndex]
  strainLabel = foldersToUpload$StrainLabel[strainIndex]
  gfFile = foldersToUpload$GfFile[strainIndex]
  gfData = read.table(gfFile)
  missingFileCount = 0
  
#   if (strainIndex < 10) {
#     strainNum = paste('0', as.character(strainIndex), sep="")
#   } else {
#     strainNum = as.character(strainIndex)
#   }
  
  # Get MINC files having strainLabel and .mnc file extension from folderName.
  fileList = list.files(path=folderName, pattern=strainLabel)
  fileList = fileList[grep(pattern='.mnc', x=fileList)]
  
  for (MINCFileIndex in 1:length(fileList)) {
    
    MINCFile = fileList[MINCFileIndex]
    individualProcessedFolderName = list.files(path=processedFolderName, pattern=substr(MINCFile, 1, nchar(MINCFile) - 4))
    individualProcessedFolderName = paste(processedFolderName, individualProcessedFolderName, sep='')
    gfIndex = grep(pattern=substr(MINCFile, 1, nchar(MINCFile) - 4), x=gfData$Filenames)
    
    if (length(gfIndex) == 1) {
      
      group = as.character(gfData$Genotype[gfIndex])
      subjLabel = unlist(strsplit(x=MINCFile, split='[.]'))[1]
      
      # need to account for additional files that may have been found by grep
#       subjNum = MINCFileIndex - missingFileCount
#       subjNum = CreateSubjNum(subjNum, subjNumEnum)

#       subjCode = paste(strainNum, subjNum, sep="")
      
#       allSubjects[dim(allSubjects)[1] + 1, ] = c(paste(folderName, MINCFile, sep=""), individualProcessedFolderName, group, subjLabel, subjCode, '', '', '', '', strainLabel, '', '')
      allSubjects[dim(allSubjects)[1] + 1, ] = c(paste(folderName, MINCFile, sep=""), individualProcessedFolderName, group, subjLabel, '', '', '', '', '', strainLabel, '', '')
      
    } else {
      
      missingFileCount = missingFileCount + 1
      
    }
  }
}

browser()

allSubjects = allSubjects[2:dim(allSubjects)[1],]

write.csv(x=allSubjects, file='SubjectMetadata.csv', row.names=FALSE)
