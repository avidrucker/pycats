#!/usr/bin/env python3
"""
Test script to verify stats formatting without running the full game.
"""

import sys
import os

# Add the parent directory to sys.path to import the game modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock player class for testing
class MockPlayer:
    def __init__(self, name, attacks_made=5, hits_landed=3, suicides=1, lives=2):
        self.char_name = name
        self.attacks_made = attacks_made
        self.hits_landed = hits_landed
        self.suicides = suicides
        self.lives = lives

# Test the stats formatting
from pycats import stats_print

def test_stats_formatting():
    """Test the statistics formatting"""
    
    # Create mock players with different stats
    winner = MockPlayer("Player 2", attacks_made=8, hits_landed=6, suicides=0, lives=3)
    loser = MockPlayer("Player 1", attacks_made=5, hits_landed=2, suicides=2, lives=0)
    
    print("Testing statistics formatting:")
    print("=" * 60)
    
    # Test individual formatting functions
    print("Winner announcement:", stats_print.format_winner_announcement(winner))
    print("Final stocks:", stats_print.format_final_stocks(winner, loser))
    print()
    
    # Test the stats table
    print("Statistics table:")
    stats_table = stats_print.format_stats_table(winner, loser)
    for line in stats_table:
        print(f"'{line}'")
    
    print()
    print("Full match summary:")
    stats_print.print_match_summary_to_console(winner, loser)

if __name__ == "__main__":
    test_stats_formatting()
