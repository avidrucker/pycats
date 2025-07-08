"""
Purpose: Statistics formatting and display utilities.

Contents:
- Format player statistics for win screen display
- Handle column alignment and number formatting
- Generate formatted statistics tables

Use: Used by game.py to display win screen statistics in a clean, aligned format.
"""

def format_stats_table(winner, loser):
    """
    Format player statistics into a properly aligned table.
    
    Args:
        winner: Player object of the winner
        loser: Player object of the loser
    
    Returns:
        List of formatted strings ready for display
    """
    # Calculate accuracy for both players
    winner_accuracy = (winner.hits_landed / max(winner.attacks_made, 1)) * 100
    loser_accuracy = (loser.hits_landed / max(loser.attacks_made, 1)) * 100
    
    # Column configuration
    stat_col_width = 18
    player_col_width = 12
    
    # Helper function to format numbers with proper alignment
    def format_number(value, width, is_percentage=False):
        if is_percentage:
            # Format percentage with % flush to the number
            return f"{value:.1f}%".center(width)
        else:
            return f"{value}".center(width)
    
    # Statistics data
    stats_data = [
        ("Attacks Made", winner.attacks_made, loser.attacks_made, False),
        (" Hits Landed", winner.hits_landed, loser.hits_landed, False),
        ("    Accuracy", winner_accuracy, loser_accuracy, True),
        ("    Suicides", winner.suicides, loser.suicides, False),
    ]
    
    # Build the formatted table
    lines = []
    
    # Header - right-align "Stat" label, center-align player names
    lines.append(f"{'Stat':>{stat_col_width}} {winner.char_name:^{player_col_width}} {loser.char_name:^{player_col_width}}")
    
    # Separator line
    lines.append(f"{'─' * stat_col_width} {'─' * player_col_width} {'─' * player_col_width}")
    
    # Data rows - right-align stat names, center-align values
    for stat_name, winner_value, loser_value, is_percentage in stats_data:
        winner_formatted = format_number(winner_value, player_col_width, is_percentage)
        loser_formatted = format_number(loser_value, player_col_width, is_percentage)
        lines.append(f"{stat_name:>{stat_col_width}} {winner_formatted} {loser_formatted}")
    
    return lines


def format_final_stocks(winner, loser):
    """
    Format the final stock count display.
    
    Args:
        winner: Player object of the winner
        loser: Player object of the loser
    
    Returns:
        Formatted string for final stocks
    """
    return f"Final Stocks: {winner.lives} - {loser.lives}"


def format_winner_announcement(winner):
    """
    Format the winner announcement.
    
    Args:
        winner: Player object of the winner
    
    Returns:
        Formatted string for winner announcement
    """
    return f"{winner.char_name} Wins!"


def get_match_summary(winner, loser):
    """
    Get a comprehensive match summary with all formatted statistics.
    
    Args:
        winner: Player object of the winner
        loser: Player object of the loser
    
    Returns:
        Dictionary containing all formatted display strings
    """
    return {
        'winner_announcement': format_winner_announcement(winner),
        'final_stocks': format_final_stocks(winner, loser),
        'stats_table': format_stats_table(winner, loser),
        'restart_instruction': "Press any key to restart"
    }


def print_match_summary_to_console(winner, loser):
    """
    Print a formatted match summary to the console for debugging/logging.
    
    Args:
        winner: Player object of the winner
        loser: Player object of the loser
    """
    summary = get_match_summary(winner, loser)
    
    print("\n" + "="*50)
    print(summary['winner_announcement'])
    print("="*50)
    print(summary['final_stocks'])
    print()
    print("Game Statistics:")
    for line in summary['stats_table']:
        print(line)
    print()
    print(summary['restart_instruction'])
    print("="*50)
