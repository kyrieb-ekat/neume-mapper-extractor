# Notes
This is a running section to keep track of small changes and alterations to the MEI bbox extraction procedure. 
Small scale test with MS73 have proven to be pretty good, even though it did occur to me that these are
pre-Neon items, and so their bbox info is a little off. 

I will, as a result of this, escalate to a low-mid size tests using corrected Einsie output files, which are
1) significantly more dense, notes-per-in^2
2) Neon-reviewed, and so have more correct bbox information
3) have a greater variety of neume labels, and will have correct(ed) neume labels from Gen in Neon

All of these will be, for now, tested in the small directories inside this repo: inside 
neume-mapper-extractor/MEI/MEI_files/Einsie and MEI/MSS_Images/Einsie respectively. Eventually these paths will
point entirely to the external drive, which will have the several hundred images and MEI files from Einsie present. 

Eventual full scale out of the gate will then be with Salzinnes, and using the corrected/final MS73 items to get a
good spread. 

The updated MEi script has been altered to be much more robust for large scale testing and conduct. I have also added
a _lot_ of other tracking and print statements for tracking checks, issues, and other small tests. 

Current input/run system should be as follows:

```
# First, analyze a few files to make sure everything looks right
./enhanced_mei_extractor.py \
  --mei-dir ~/external/test_mei_files \
  --output ~/external/test_output \
  --images ~/external/test_images \
  --analyze-only

# Then run a small batch with verbose logging
./enhanced_mei_extractor.py \
  --mei-dir ~/external/test_mei_files \
  --output ~/external/extracted_neumes/MS73 \
  --images ~/external/test_images \
  --width-scale 2.5 \
  --height-scale 2.7 \
  --workers 4 \
  --verbose

# For production run on hundreds of files
./enhanced_mei_extractor.py \
  --mei-dir ~/external/all_mei_files \
  --output ~/external/extracted_neumes/MS73 \
  --images ~/external/all_images \
  --width-scale 2.5 \
  --height-scale 2.7 \
  --workers 8
  ```
