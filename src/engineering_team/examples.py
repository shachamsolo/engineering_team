"""Example product briefs shown in the Gradio UI."""

TRADING_ACCOUNT = (
    "A simple account management system for a trading simulation platform. "
    "Users can create an account, deposit funds, and withdraw funds. "
    "Users can record that they have bought or sold shares, providing a quantity. "
    "The system should calculate the total value of the user's portfolio and the profit or loss from the initial deposit. "
    "It should report holdings and profit/loss at any point in time, and list transactions over time. "
    "Prevent withdrawing into a negative balance, buying more shares than the user can afford, or selling shares they don't have. "
    "Include get_share_price(symbol) with a test implementation that returns fixed prices for AAPL, TSLA, and GOOGL."
)

COUNTDOWN_TIMER = (
    "A focused countdown timer. The user enters a duration in seconds and starts the timer. "
    "Show remaining time clearly. In the last 10 seconds, switch to a prominent warning state. "
    "When the timer hits zero, celebrate with a distinctive finished state. "
    "Keep it to one user, no accounts, and no extra features."
)

HABIT_TRACKER = (
    "A personal habit tracker. The user can add habits, mark a habit complete for today, "
    "see today's completion status, and view a simple streak count per habit. "
    "Prevent duplicate habit names and completing a habit twice in the same day. "
    "No accounts, no calendar heatmaps, no third-party APIs."
)

EXAMPLE_BRIEFS = [TRADING_ACCOUNT, COUNTDOWN_TIMER, HABIT_TRACKER]


def example_rows() -> list[list[str]]:
    """Gradio Examples rows: one brief per row, single textbox input."""
    return [[brief] for brief in EXAMPLE_BRIEFS]
