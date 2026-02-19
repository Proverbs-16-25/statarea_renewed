import io
import contextlib
from StatareaAccumulator import StatareaAccumulator


def show_dashboard(db, last_output=None):
    print("\n==============================")
    print("     STATAREA ACCUMULATOR")
    print("==============================")

    # Match count (adjust column/table names if needed)
    try:
        count = db.conn.execute(
            "SELECT COUNT(*) FROM raw_matches WHERE home_ft_goals IS NOT NULL;"
        ).fetchone()[0]
    except Exception:
        count = "N/A"

    print(f"Match Count: {count}")

    # Daily status
    try:
        status = "SCRAPED" if db.was_accumulated_today() else "NOT SCRAPED"
    except Exception:
        status = "UNKNOWN"

    print(f"Today's Status: {status}")

    # Missed days
    try:
        missed = db.get_missed_days(limit_days=3)
    except Exception:
        missed = []

    if not missed:
        print("Days Missed: None")
    else:
        print("Days Missed:")
        for date in missed:
            print(f"  - {date}")

    print("\nCommands:")
    print("1 - Normal Daily Accumulation")
    print("2 - Custom Accumulation")
    print("3 - Exit")

    # Bottom Console Panel
    if last_output:
        print("\n------------------------------")
        print(" LAST RUN OUTPUT (Last 15 lines)")
        print("------------------------------")

        lines = last_output.strip().splitlines()
        for line in lines[-15:]:
            print(line)


def main():
    accumulator = StatareaAccumulator()
    db = accumulator.db

    last_output = None

    while True:
        show_dashboard(db, last_output)

        choice = input("\nSelect option: ").strip()

        if choice == "1":
            buffer = io.StringIO()
            with contextlib.redirect_stdout(buffer):
                accumulator.accumulate_daily()

            last_output = buffer.getvalue()

        elif choice == "2":
            try:
                scrape_day = int(input("Enter scrape_day: "))
                update_day = int(input("Enter update_day: "))

                custom = StatareaAccumulator(
                    scrape_days=scrape_day,
                    update_days=update_day
                )

                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    custom.accumulate_daily()

                last_output = buffer.getvalue()
                custom.close()

            except Exception as e:
                print(f"\nError during custom accumulation: {e}")

        elif choice == "3":
            break

        else:
            print("\nInvalid option.")

    accumulator.close()


if __name__ == "__main__":
    main()
