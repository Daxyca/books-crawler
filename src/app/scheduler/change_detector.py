from typing import Any, Optional, List
from src.app.models.book import Book
from src.app.models.change_log import ChangeLog, ChangeType, ChangeReport
from datetime import datetime, timezone
import csv
from io import StringIO


class ChangeDetector:
    # Fields to monitor for changes
    # (exclude metadata fields like crawl_timestamp, raw_html)
    MONITORED_FIELDS = [
        "name",
        "description",
        "category",
        "price_excl_tax",
        "price_incl_tax",
        "availability",
        "num_reviews",
        "rating",
        "image_url",
    ]

    def detect_changes(
        self, old_book: Optional[Book], new_book: Book
    ) -> List[ChangeLog]:
        changes = []

        # New book
        if old_book is None:
            changes.append(
                ChangeLog(
                    book_name=new_book.name,
                    book_url=new_book.source_url,
                    change_type=ChangeType.NEW_BOOK,
                    field_name=None,
                    old_value=None,
                    new_value=None,
                    summary=f"New book added: {new_book.name}",
                )
            )
            return changes

        # Compare each monitored field
        for field in self.MONITORED_FIELDS:
            old_value = getattr(old_book, field)
            new_value = getattr(new_book, field)

            if old_value != new_value:
                change_type = self._classify_change(field)
                summary = self._generate_summary(
                    field, old_value, new_value, new_book.name
                )

                changes.append(
                    ChangeLog(
                        book_name=new_book.name,
                        book_url=new_book.source_url,
                        change_type=change_type,
                        field_name=field,
                        old_value=old_value,
                        new_value=new_value,
                        summary=summary,
                    )
                )

        return changes

    def _classify_change(self, field_name: str) -> ChangeType:
        if field_name in ["price_excl_tax", "price_incl_tax"]:
            return ChangeType.PRICE_CHANGE
        elif field_name == "availability":
            return ChangeType.AVAILABILITY_CHANGE
        elif field_name == "rating":
            return ChangeType.RATING_CHANGE
        else:
            return ChangeType.OTHER_CHANGE

    def _generate_summary(
        self, field_name: str, old_value: Any, new_value: Any, book_name: str
    ) -> str:
        if field_name in ["price_excl_tax", "price_incl_tax"]:
            direction = "increased" if new_value > old_value else "decreased"
            field_display = (
                "Price (incl tax)" if "incl" in field_name else "Price (excl tax)"
            )
            return (
                f"{field_display} {direction} from £{old_value:.2f} to £{new_value:.2f}"
            )

        elif field_name == "availability":
            return f"Availability changed from '{old_value}' to '{new_value}'"

        elif field_name == "rating":
            return f"Rating changed from {old_value} to {new_value}"

        elif field_name == "num_reviews":
            change = new_value - old_value
            return f"Reviews {'increased' if change > 0 else 'decreased'} by {abs(change)} (now {new_value})"

        else:
            return f"{field_name.replace('_', ' ').title()} changed from '{old_value}' to '{new_value}'"

    def generate_report(self, changes: List[ChangeLog]) -> ChangeReport:
        # Count changes by type
        new_books = sum(1 for c in changes if c.change_type == ChangeType.NEW_BOOK)
        price_changes = sum(
            1 for c in changes if c.change_type == ChangeType.PRICE_CHANGE
        )
        availability_changes = sum(
            1 for c in changes if c.change_type == ChangeType.AVAILABILITY_CHANGE
        )
        rating_changes = sum(
            1 for c in changes if c.change_type == ChangeType.RATING_CHANGE
        )
        other_changes = sum(
            1 for c in changes if c.change_type == ChangeType.OTHER_CHANGE
        )

        return ChangeReport(
            report_date=datetime.now(timezone.utc),
            total_changes=len(changes),
            new_books=new_books,
            price_changes=price_changes,
            availability_changes=availability_changes,
            rating_changes=rating_changes,
            other_changes=other_changes,
            changes=changes,
        )

    def export_report_to_json(self, report: ChangeReport) -> str:
        return report.model_dump_json(indent=2)

    def export_report_to_csv(self, report: ChangeReport) -> str:
        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(
            [
                "Detected At",
                "Book Name",
                "Change Type",
                "Field",
                "Old Value",
                "New Value",
                "Summary",
            ]
        )

        # Data rows
        for change in report.changes:
            writer.writerow(
                [
                    change.detected_at.isoformat(),
                    change.book_name,
                    change.change_type.value,
                    change.field_name or "",
                    str(change.old_value) if change.old_value is not None else "",
                    str(change.new_value) if change.new_value is not None else "",
                    change.summary or "",
                ]
            )

        return output.getvalue()
