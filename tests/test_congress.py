import unittest
import os 
from dotenv import load_dotenv
from src.congress import get_members

load_dotenv()

class TestCongressMembers(unittest.TestCase):

    def test_real_api_call(self):
        """Test actual API call to see if we get a reasonable number of members"""
        api_key = os.getenv('CONGRESS_API_KEY')
        members = get_members(api_key)
        
        # Congress should have between 400-600 members (allowing for vacancies/changes)
        min_expected = 400
        max_expected = 600
        
        actual = len(members)
        print(f"Retrieved {actual} members")
        
        self.assertTrue(min_expected <= actual <= max_expected, 
                        f"Expected between {min_expected}-{max_expected} members, got {actual}")

if __name__ == '__main__':
    unittest.main()
