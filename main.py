import logging
from src.house_scrape import run as house_scrape_run
from src.house_analysis import run_analysis as house_analysis_run
from src.senate_scrape import run as senate_scrape_run 
from src.senate_analysis import run_analysis as senate_analysis_run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Starting House disclosure scraping...")
        house_scrape_run()
        logger.info("House scraping complete")

        logger.info("Starting House disclosure analysis...")
        house_analysis_run()
        logger.info("House analysis complete")

        logger.info("Starting Senate disclosure scraping...")
        senate_scrape_run()
        logger.info("Senate scraping complete")

        logger.info("Starting Senate disclosure analysis...")
        senate_analysis_run()
        logger.info("Senate analysis complete")

    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()
