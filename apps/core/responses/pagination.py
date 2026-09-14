import base64
import json

from django.core.exceptions import ValidationError
from django.db.models import Q


class CursorPagination:
    """
    Generic cursor pagination using a Relay/GraphQL-style
    connection structure.

    Supported query parameters:

        ?first=20
        ?first=20&after=<cursor>

        ?last=20&before=<cursor>

    Response:

        {
            "edges": [
                {
                    "cursor": "...",
                    "node": {...}
                }
            ],
            "page_info": {
                "has_next_page": true,
                "has_previous_page": false,
                "start_cursor": "...",
                "end_cursor": "..."
            },
            "total_count": 100
        }

    The paginator is completely independent of the model.
    """
    @classmethod
    def paginate(
        cls,
        *,
        queryset,
        request,
        serializer_class,
        ordering=("-created_at", "-id"),
    ):
        first = request.query_params.get("first")
        last = request.query_params.get("last")
        after = request.query_params.get("after")
        before = request.query_params.get("before")

        cls._validate_arguments(
            first=first,
            last=last,
            after=after,
            before=before,
        )

        direction = (
            "backward"
            if last is not None
            else "forward"
        )

        page_size = cls._get_page_size(
            first=first,
            last=last,
        )

        ordering = cls._normalize_ordering(
            ordering
        )

        queryset = queryset.order_by(
            *ordering
        )

        # -----------------------------------------------------
        # Total count
        #
        # This MUST happen before applying the cursor.
        # -----------------------------------------------------

        total_count = queryset.count()

        # -----------------------------------------------------
        # Apply cursor
        # -----------------------------------------------------

        if after:
            cursor_values = cls._decode_cursor(
                after
            )

            queryset = cls._apply_cursor(
                queryset=queryset,
                values=cursor_values,
                ordering=ordering,
                direction="after",
            )

        elif before:
            cursor_values = cls._decode_cursor(
                before
            )

            queryset = cls._apply_cursor(
                queryset=queryset,
                values=cursor_values,
                ordering=ordering,
                direction="before",
            )

        # -----------------------------------------------------
        # Fetch one extra record.
        #
        # This tells us whether there are records beyond
        # the requested page.
        # -----------------------------------------------------
        if page_size is None:
            items = list(queryset)
            has_extra=False
        else:
            items = list(
                queryset[: page_size + 1]
            )

            has_extra = len(items) > page_size

            if has_extra:
                items = items[:page_size]

        # For backwards pagination, the database query
        # returns records in the normal ordering. Reverse
        # them so the response is still presented in the
        # normal chronological/order sequence.
        if direction == "backward":
            items.reverse()

        # -----------------------------------------------------
        # Determine page boundaries
        # -----------------------------------------------------

        has_next_page = False
        has_previous_page = False

        if items:

            first_item = items[0]
            last_item = items[-1]

            first_cursor = cls._create_cursor(
                item=first_item,
                ordering=ordering,
            )

            last_cursor = cls._create_cursor(
                item=last_item,
                ordering=ordering,
            )

            if direction == "forward":

                has_next_page = has_extra

                has_previous_page = cls._exists_before(
                    queryset=queryset,
                    item=first_item,
                    ordering=ordering,
                )

            else:

                has_previous_page = has_extra

                has_next_page = cls._exists_after(
                    queryset=queryset,
                    item=last_item,
                    ordering=ordering,
                )

        else:
            first_cursor = None
            last_cursor = None

            # If a cursor was supplied but there are no
            # records, we still know which side of the
            # connection was requested.
            if direction == "forward":
                has_previous_page = bool(after)

            else:
                has_next_page = bool(before)

        # -----------------------------------------------------
        # Serialize
        # -----------------------------------------------------

        serializer = serializer_class(
            items,
            many=True,
        )

        edges = []

        for item, serialized_item in zip(
            items,
            serializer.data,
        ):
            edges.append(
                {
                    "cursor": cls._create_cursor(
                        item=item,
                        ordering=ordering,
                    ),
                    "node": serialized_item,
                }
            )

        return {
            "page_info": {
                "has_next_page": has_next_page,
                "has_previous_page": has_previous_page,
                "start_cursor": first_cursor,
                "end_cursor": last_cursor,
            },
            "total_count": total_count,
            "edges": edges,
        }

    # =========================================================
    # Validation
    # =========================================================

    @classmethod
    def _validate_arguments(
        cls,
        *,
        first,
        last,
        after,
        before,
    ):
        if first is not None and last is not None:
            raise ValidationError(
                "Only one of 'first' or 'last' may be provided."
            )

        if after is not None and before is not None:
            raise ValidationError(
                "Only one of 'after' or 'before' may be provided."
            )

        if before is not None and last is None:
            raise ValidationError(
                "'before' requires 'last'."
            )

        if last is not None and before is None:
            raise ValidationError(
                "'last' requires 'before'."
            )

    @classmethod
    def _get_page_size(
        cls,
        *,
        first,
        last,
    ):
        value = first or last

        if value is None:
            return None
            # return cls.default_page_size

        try:
            value = int(value)
        except (TypeError, ValueError):
            raise ValidationError(
                "Pagination size must be a valid integer."
            )

        if value <= 0:
            raise ValidationError(
                "Pagination size must be greater than zero."
            )
        return value
        # return min(
        #     value,
        #     cls.max_page_size,
        # )

    @staticmethod
    def _normalize_ordering(ordering):
        if isinstance(ordering, str):
            return (ordering,)

        return tuple(ordering)

    # =========================================================
    # Cursor encoding / decoding
    # =========================================================

    @staticmethod
    def _encode_cursor(values):
        payload = json.dumps(
            values,
            separators=(",", ":"),
            default=str,
        )

        return base64.urlsafe_b64encode(
            payload.encode()
        ).decode()

    @staticmethod
    def _decode_cursor(cursor):
        try:
            payload = base64.urlsafe_b64decode(
                cursor.encode()
            ).decode()

            return json.loads(payload)

        except (
            ValueError,
            TypeError,
            UnicodeDecodeError,
            json.JSONDecodeError,
        ):
            raise ValidationError(
                "Invalid cursor."
            )

    @classmethod
    def _create_cursor(
        cls,
        *,
        item,
        ordering,
    ):
        values = {}

        for field in ordering:
            field_name = field.lstrip("-")

            values[field_name] = getattr(
                item,
                field_name,
            )

        return cls._encode_cursor(
            values
        )

    # =========================================================
    # Cursor filtering
    # =========================================================

    @classmethod
    def _apply_cursor(
        cls,
        *,
        queryset,
        values,
        ordering,
        direction,
    ):
        condition = Q()

        for index, field in enumerate(ordering):

            field_name = field.lstrip("-")
            descending = field.startswith("-")

            if field_name not in values:
                raise ValidationError(
                    "Invalid cursor."
                )

            value = values[field_name]

            equal_condition = Q()

            for previous_field in ordering[:index]:

                previous_name = (
                    previous_field.lstrip("-")
                )

                if previous_name not in values:
                    raise ValidationError(
                        "Invalid cursor."
                    )

                equal_condition &= Q(
                    **{
                        previous_name: values[
                            previous_name
                        ]
                    }
                )

            if descending:
                if direction == "after":
                    lookup = "lt"
                else:
                    lookup = "gt"
            else:
                if direction == "after":
                    lookup = "gt"
                else:
                    lookup = "lt"

            comparison = Q(
                **{
                    f"{field_name}__{lookup}": value
                }
            )

            condition |= (
                equal_condition
                & comparison
            )

        return queryset.filter(condition)

    # =========================================================
    # Page boundary checks
    # =========================================================

    @classmethod
    def _exists_before(
        cls,
        *,
        queryset,
        item,
        ordering,
    ):
        values = {}

        for field in ordering:
            field_name = field.lstrip("-")

            values[field_name] = getattr(
                item,
                field_name,
            )

        condition = cls._build_boundary_condition(
            values=values,
            ordering=ordering,
            direction="before",
        )

        return queryset.filter(
            condition
        ).exists()

    @classmethod
    def _exists_after(
        cls,
        *,
        queryset,
        item,
        ordering,
    ):
        values = {}

        for field in ordering:
            field_name = field.lstrip("-")

            values[field_name] = getattr(
                item,
                field_name,
            )

        condition = cls._build_boundary_condition(
            values=values,
            ordering=ordering,
            direction="after",
        )

        return queryset.filter(
            condition
        ).exists()

    @classmethod
    def _build_boundary_condition(
        cls,
        *,
        values,
        ordering,
        direction,
    ):
        condition = Q()

        for index, field in enumerate(ordering):

            field_name = field.lstrip("-")
            descending = field.startswith("-")

            equal_condition = Q()

            for previous_field in ordering[:index]:

                previous_name = (
                    previous_field.lstrip("-")
                )

                equal_condition &= Q(
                    **{
                        previous_name: values[
                            previous_name
                        ]
                    }
                )

            if descending:
                lookup = (
                    "lt"
                    if direction == "after"
                    else "gt"
                )
            else:
                lookup = (
                    "gt"
                    if direction == "after"
                    else "lt"
                )

            comparison = Q(
                **{
                    f"{field_name}__{lookup}": values[
                        field_name
                    ]
                }
            )

            condition |= (
                equal_condition
                & comparison
            )

        return condition