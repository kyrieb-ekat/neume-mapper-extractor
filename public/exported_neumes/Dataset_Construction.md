Dataset_Construction

# Neume Sets
## Automatic Extraction
### Sankt Gallen Neumes 
for st gall, relying on the annotations made as part of the **optical neume recognition project**. 
These annotations were stored in a single very large annotated json file, which needed to be formatted
in a means my ensuing extractor could utilize. format_annotations.py was able to take the input raw json
file and format it in the necessary style. From here, export_neumes.py is able to use the converted
json and the image and api links to download and crop the images were needed. 

The images were then automatically sorted into named directories by types; as "type":"neume" was
encountered, a directory was created of that neume name and the images/URLs following filtered
inwards until a new "type":"name" was detected, until the end of the file was met. 

The total number of items extracted from this project numbered in the 18,000s. However, for my purposes
of distinct neume extraction and comparison, I only needed some of the directories of neumes, reducing the
total number of used neume images to 8,172. 

Ensuing trainings may utilize all of the available neumes, but for this current iteration of POSSUMM
these are the neumes selected for use following the word and letter spotting procedure discussed in 
**Mårtensson et al. 2018** . 

### Square Neumes
These, like Sankt Gallen,w ere able to be extracted using data from a previous project. At the 
Distributed Digital Media Archives and Libraries Lab (DDMAL), a number of manuscripts had been
processed for end-to-end OMR, producing not only separated layers of all manuscript pages but MEI files
for their subsequent encoding and symbolic representation elsewhere. 

I utilized my access to these images and MEI files to write a script in a separate small project called
_Neume-Mapper-Extractor_ with `MEI_neume_extractor.py`. This utilized the bounding boxes provided by
the MEI files and mapped them onto the downloaded image, automatically cropping them. This proved 
to be remarkably difficult, given the fact that the MEI bounding boxes did not scale per neume size
and appeared fix; a large neume such as a _climacus_ or _porrectus flexus_ would have the same size image
cut/bounding box size as would a smaller neume, like a _punctum_ or a _virga_.

Experimentation with this found that defaulting to a larger (x1.8) scale crop from the bounding box provided
successfully grabbed the needed image data in most cases. Continued experimentation on default scaling or image
detection are on deck. However, for rapid mass processing this does for now. 

A further small problem arises with the fact that all neume (or rather neume component) IDs in the MEI file
are URIs, and so don't distinguish between neume type, and so multiple neumes of varying types may exist in the
same directory. For the purposes of square notation, it is somewhat visually distinct enough that several items
might remain and be useful for script and neume classification, but this might be problematic especially for
images which have little detail (such as a _punctum_ or _virga_). 

Otherwise, the MEI-Image mutual reference and extraction process works, and gets me around needing to utilize
a sepatate job inside of Rodan to extract black and white renderings of images, or proceed to some of the experimentation
detailed below for Beneventan neumes. 

## Hand Extracted and Experimental Extraction of Neume Styles
### Hispanic Neumes
These are, unlike all other neume classes analysed here, so visually distinct and separate in classification and 
naming in about any way they were exceptionally easy to label. The naming conventions for these items are very
broad and nuanced: encountering something like -neutral-high-low-low-neutral-low-high would not be uncommon. 
Due to this, and the high visual dissimilarity of this script from not only the other scripts included here but in
the larger western european chant tradition, I was able to label each of these items as "hispanic" with no further
nuance. This allowed some rapidity in the creation of this dataset, as I did not need to seek out 2,000 clivis', 
merely ~2,000 boxed samples. Where issues arose, it was most commonly in where to decide a neume ended and another
began, as this appears to be very context dependent; context was prioritized unless the symbol was highly distinct.

This annotation was conducted using the Oxford University Virtual Geometry Group's Image Annotator (VIA), and then 
exported as individuals into their own directory with no subdirectories. 

### Beneventan Neumes
Unlike the other scripts discussed here, Beneventan is not wholly visually distinct enough like the Hispanic set, 
nor common enough like square, for there to be an easy approach. The digitization of Beneventan sources at large, 
not only musical beneventan sources, remains an ongoing and slow tasked, burdened by a lack of funding and resources
in the institutions which do have the staff, time, and machines available to conduct digitization projects. As 
such the images which were collected have a larger representation of black and white images, and with other visual
disturbances due to watermarks automatically applied by archives (most notably the Vatican Apostolic Library, which
possesses a number of manuscripts with musical Beneventan script). As such, it was more difficult developing a rounded 
dataset of Beneventan neumes. 

I tried to be representative of Beneventan manuscripts with varied stafflines present; it's not unusual for Beneventan manuscriptso
to have dry point or other singular lines, nor for there to be two and four line staff implementations as well as
wholly adiastematic examples. 

I did my initial grab entirely within VIA, as with the Hispanic samples, though ensuing experiments are being done in 
Rodan and with Pixel.js. I am strongly hesitant to try and progress through to a full image and glyph identification training
and extraction phase. However, the clean labeling and extraction/layer separation capabilities of Rodan are fantastic. So 
it's for this reason I began experimenting and developing a model which could cleanly separate Beneventan musical script 
from its background, text, and staves (when present). I did this with the aim of then using the separated musical/symbol
layer to run through an edge or object detector and automatically crop out the sections, either as a fine line or as a box with
padding around the detected object of several pixels to gain some object context. This process of experimentation is still underway. 

If needs be I will proceed further downstream to the Interactive Classifier phase and attempt to train the IC to extract musical symbols. 
Given that E2E OMR is not the goal here, the ensuing glyph data and training file input to the NIC would need to be used in an extractor
similar to the one which currently exists for extracting c-clefs, though it would need to extract and label all detected classes. I 
strongly would prefer having _all_ available neumes sorted which I can then choose which neume types to feed into a model than to only
have items I at the outset thought I might use; I would rather have the data on hand then need to conduct this process again to get
additional data. 