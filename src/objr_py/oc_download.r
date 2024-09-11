library(objr)

args <- commandArgs(trailingOnly = TRUE)
uuid <- args[1]
folder <- args[2]

info <- asset_info(uuid)
filename <- paste(info$name, info$extension, sep = ".")

download_file(uuid, folder)

print(filename)
