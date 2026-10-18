import argparse

from estimator import compare_models, estimate_monthly_cost


def main() -> None:
    parser = argparse.ArgumentParser(description="Estimate monthly LLM API cost.")
    parser.add_argument("--model", help="Model name. Omit to compare all models.")
    parser.add_argument("--requests", type=int, required=True, help="Requests per day")
    parser.add_argument("--input", type=int, required=True, help="Input tokens per request")
    parser.add_argument("--output", type=int, required=True, help="Output tokens per request")
    parser.add_argument("--days", type=int, default=30, help="Days per month (default: 30)")
    args = parser.parse_args()

    try:
        if args.model:
            cost = estimate_monthly_cost(
                args.model, args.requests, args.input, args.output, args.days
            )
            print(f"{args.model}: ${cost:.2f} / month")
        else:
            for name, cost in compare_models(
                args.requests, args.input, args.output, args.days
            ):
                print(f"{name:<20} ${cost:>8.2f}")
    except ValueError as e:
        parser.error(str(e))


if __name__ == "__main__":
    main()
