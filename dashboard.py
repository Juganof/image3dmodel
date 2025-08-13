from typing import List, Dict


class Dashboard:
    """Track deals and negotiations."""

    def __init__(self) -> None:
        self.deals: List[Dict] = []

    def add_deal(self, deal: Dict) -> None:
        """Record a new deal in the dashboard."""
        self.deals.append(deal)

    def summary(self) -> Dict[str, int]:
        """Return basic stats about recorded deals."""
        return {"total_deals": len(self.deals)}
