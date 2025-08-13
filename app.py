from search_automation import SearchAutomation
from listing_analysis import ListingAnalysis
from negotiations import Negotiator
from resale_value import ResaleValueCalculator
from dashboard import Dashboard


def main() -> None:
    """Run an example flow using the core features."""
    searcher = SearchAutomation()
    analyzer = ListingAnalysis()
    negotiator = Negotiator()
    calculator = ResaleValueCalculator()
    dashboard = Dashboard()

    listings = searcher.search(
        price_min=0,
        price_max=100,
        radius_km=10,
        keywords=["bike"],
        categories=["fietsen"],
    )
    for listing in listings:
        score = analyzer.rate(listing)
        estimated_resale = calculator.estimate(listing)
        message = negotiator.negotiate(
            listing,
            budget=50,
            location="Amsterdam",
            payment_method="cash",
            persona="Friendly Neighbor",
        )
        dashboard.add_deal(
            {
                "listing": listing,
                "score": score,
                "resale": estimated_resale,
                "message": message,
            }
        )

    print(dashboard.summary())


if __name__ == "__main__":
    main()
