### Approach Overview
The approach relies on feeding images and prompts into the multi-modal OpenAI API (gpt-4o-mini) for automated parsing. This end-to-end approach *by-far* outperforms OCR libraries and other fragmented LLM-based workflows. It is also way easier to implement and continue to develop, and will continue getting better and cheaper as these LLM's improve.

It is set up so that most users will not have to run the automation pipeline. `all_source_data` and `final_data` folders are small enough to commit to GitHub, so ideally one person will run this code periodically, and everyone else can just easily access these artifacts for their own use (unless you are contributing to development of the automation)



### Run in 3 Steps
**0_gather_source_data.py**
    * Retrieves congress member data from Congress API: https://api.congress.gov/v3/member/congress
    * Scrapes data from the House and Senate financial disclosure sites:
        * House Financial Disclosures: https://disclosures-clerk.house.gov/
        * Senate Financial Disclosures: https://efdsearch.senate.gov/
    * Organizes data for processing and converts PDF/GIF files to JPEGs.

  *Note: This step can be skipped if you already have recent source data, which should be up to date committed to the repo.
  This is useful for development, since much of the work will be on processing the source files*
      
**1_parse_asset_names_llm.py**
    * Sends images to OpenAI's API with specific prompts, extracting asset names and saving them to `./all_processed_data`.
    
**2_summarize_results.py**
    * Summarizes files in `./all_processed_data` into `final_datasets/final_asset_data.csv` and `final_datasets/final_summary_data.csv`.
    * Implements bitcoin/crypto term classification based on a predefined list.



### Ideas for Improvement
It currently works sufficiently well to detect the bitcoin/crypto terms. The following ideas could improve the asset list beyond just bitcoin/crypto related assets.

* Better method for image rotation. Assumptions can be made for most files, but sometimes an image will be rotated incorrectly, which hurts the LLM performance.
* Use gpt-4o instead of gpt-4o-mini (current choice to save $).
    * I have experimented with this on select files and it does seem to be markedly better.
    * Using gpt-4o-mini for clean house files (92%), gpt-4o for messy house (~7%) and senate gif files (~1%) might be best bang for buck.
* Refine prompts.
* Crop images intelligently to focus on relevant sections.
* Currently asking the LLM when to skip a file. This may be counter-productive. Consider just one-shot prompt each image.
* Directly ask the LLM, does this image mention bitcoin or cryptocurrency? not sure if this will work, might encourage hallucination. worth testing.
* links to all sources are available in the data scraping process, need to write them to file for easy inclusion in the main readMe
