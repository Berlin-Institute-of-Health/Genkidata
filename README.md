# Genkidata
OpenEHR sample data population tool.
Uses a provided set of compositions to populate a openEHR CDR by duplicating them. 
The amount of compositions and EHRs is defined by user input. 
Composition numbers will be randomized in a way so the sum is the amount that was specified by the user. 

## Requirements:
* Running openEHR server
* python3

## Use
1. Download dependencies 
`pip install -r requirements.txt`
2. Save your own opts and compositions into the folders or use the sample ones. XML compositions are not supported. 
3. Run Genkidata 
`python3 genkidata.py`

If running in an IDE the getpass won't work, use static variable then as contained in the code.


