from typing import Dict


class Negotiator:
    """Automate negotiations with sellers using predefined personas."""

    personas = [
        "Friendly Neighbor",
        "Market Expert",
        "Quick Closer",
        "Bargain Hunter",
    ]

    def negotiate(
        self,
        listing: Dict,
        budget: float,
        location: str,
        payment_method: str,
        persona: str,
    ) -> str:
        """
        Start a negotiation conversation with the seller.
        Placeholder implementation returning a formatted message.
        """
        message = (
            f"Hello! I am interested in your listing '{listing.get('title', 'item')}'. "
            f"My budget is {budget}. "
            f"I can meet at {location} and pay via {payment_method}."
        )
        return message
