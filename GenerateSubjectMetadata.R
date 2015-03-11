# This script generates a file to be supplied to a SPReD upload,
# containing subject metadata (e.g. WT or KO, SPReD ID, etc.) for
# uploading mice to the Brain-CODE SPReD.

# GenerateSubjectMetadata.R ----------------------------------------------------------

# folder containing gf files for all mouse strains
gf_file_path = '/micehome/jbruce/Documents/Code/R/ClusterMouseAutism/data/'

# specify folder locations here to upload to SPReD
folders_to_upload = data.frame(FolderName=c('/projects/mice/jacob/Neuroligin/NLGN_Images/Distortion_Corrected/',
                                            '/projects/moush/jacob/ITGB3/ITGB3_Images/Distortion_Corrected/'),
                               StrainLabel=c('NLGN', 'ITGB3'),
                               GfFile=c(paste(gf_file_path, 'gf_NL3_relative.txt', sep=""),
                                        paste(gf_file_path, 'gf_ITGB3_relative.txt', sep="")),
                               stringsAsFactors=FALSE)

all_subjects = data.frame(Filename=character(1), 
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

# loop through strains and create SPReD subject metadata file
for (strain_index in 1:dim(folders_to_upload)[1]) {
  
  folder_name = folders_to_upload$FolderName[strain_index]
  strain_label = folders_to_upload$StrainLabel[strain_index]
  gf_file = folders_to_upload$GfFile[strain_index]
  gf_data = read.table(gf_file)
  missing_file_count = 0
  
  if (strain_index < 10) {
    strain_num = paste('0', as.character(strain_index), sep="")
  } else {
    strain_num = as.character(strain_index)
  }
  
  # get MINC files with strain label and .mnc file extension
  file_list = list.files(path=folder_name, pattern=strain_label)
  file_list = file_list[grep(pattern='.mnc', x=file_list)]
  
  for (MINC_file_index in 1:length(file_list)) {
    
    MINC_file = file_list[MINC_file_index]
    gf_index = grep(pattern=substr(MINC_file, 1, nchar(MINC_file)-4), x=gf_data$Filenames)
    
    if (length(gf_index) == 1) {
      
      group = as.character(gf_data$Genotype[gf_index])
      subj_label = unlist(strsplit(x=MINC_file, split='[.]'))[1]
      
      subj_num = MINC_file_index - missing_file_count
      
      if (subj_num < 10) {
        subj_num = paste('0', as.character(subj_num), sep="")
      } else {
        subj_num = as.character(subj_num)
      }
      
      #browser()
      
      subj_code = paste(strain_num, subj_num, sep="")

      all_subjects[dim(all_subjects)[1]+1,] = c(paste(folder_name,MINC_file,sep=""), group, subj_label, subj_code, '', '', '', '', strain_label, '', '')
    } else {
      
      missing_file_count = missing_file_count + 1
      
    }
  }
}

all_subjects = all_subjects[2:dim(all_subjects)[1],]

write.csv(x=all_subjects, file='SubjectMetadata.csv', row.names=FALSE)
