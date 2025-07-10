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
        Dictionary containing the stats data for pixel-perfect rendering
    """
    # Determine P1 and P2 stats regardless of who won
    if winner.char_name == "P1":
        p1_player = winner
        p2_player = loser
    else:
        p1_player = loser
        p2_player = winner

    # Calculate accuracies for P1 and P2
    p1_accuracy = (p1_player.hits_landed / max(p1_player.attacks_made, 1)) * 100
    p2_accuracy = (p2_player.hits_landed / max(p2_player.attacks_made, 1)) * 100

    # Return structured data instead of formatted strings
    return {
        "header": {"stat_label": "Stat", "p1_label": "P1", "p2_label": "P2"},
        "rows": [
            {
                "stat_name": "Attacks Made",
                "p1_value": str(p1_player.attacks_made),
                "p2_value": str(p2_player.attacks_made),
            },
            {
                "stat_name": "Hits Landed",
                "p1_value": str(p1_player.hits_landed),
                "p2_value": str(p2_player.hits_landed),
            },
            {
                "stat_name": "Accuracy",
                "p1_value": f"{p1_accuracy:.1f}%",
                "p2_value": f"{p2_accuracy:.1f}%",
            },
            {
                "stat_name": "Suicides",
                "p1_value": str(p1_player.suicides),
                "p2_value": str(p2_player.suicides),
            },
        ],
    }


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
        "winner_announcement": format_winner_announcement(winner),
        "final_stocks": format_final_stocks(winner, loser),
        "stats_table": format_stats_table(winner, loser),  # Now returns structured data
        "restart_instruction": "Press any key to restart",
    }


def print_match_summary_to_console(winner, loser):
    """
    Print a formatted match summary to the console for debugging/logging.

    Args:
        winner: Player object of the winner
        loser: Player object of the loser
    """
    summary = get_match_summary(winner, loser)

    print("\n" + "=" * 50)
    print(summary["winner_announcement"])
    print("=" * 50)
    print(summary["final_stocks"])
    print()
    print("Game Statistics:")

    # Handle the new structured format
    stats_table = summary["stats_table"]
    header = stats_table["header"]
    print(f"{'Stat':>18} {'P1':^12} {'P2':^12}")
    print(f"{'─' * 18} {'─' * 12} {'─' * 12}")

    for row in stats_table["rows"]:
        print(f"{row['stat_name']:>18} {row['p1_value']:^12} {row['p2_value']:^12}")

    print()
    print(summary["restart_instruction"])
    print("=" * 50)
